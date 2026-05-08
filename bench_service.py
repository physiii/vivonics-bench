"""Vivonics X1 Bench Service — runs on Raspberry Pi.

Controls the projector (HDMI), captures from the camera (CSI/rpicam),
runs photocycle measurement protocols, and streams metrics via SSE.
"""
from __future__ import annotations

import asyncio
import threading
import time
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from capture import Capture, CaptureConfig
from photocycle import (
    LinearityResult,
    PhotocycleConfig,
    PhotocycleResult,
    run_green_write_sweep,
    run_linearity_check,
)
from projector import Projector, ProjectorConfig
from sensors import SensorSuite


class RunState(str, Enum):
    idle = "idle"
    running_linearity = "running_linearity"
    running_photocycle = "running_photocycle"
    completed = "completed"
    failed = "failed"
    aborted = "aborted"


class BenchState:
    def __init__(self) -> None:
        self.state: RunState = RunState.idle
        self.events: list[dict[str, Any]] = []
        self.linearity_result: LinearityResult | None = None
        self.photocycle_result: PhotocycleResult | None = None
        self._abort_flag = False
        self._lock = threading.Lock()
        self._event_queues: list[asyncio.Queue[dict[str, Any] | None]] = []

    def emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            self.events.append(event)
        for q in self._event_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue[dict[str, Any] | None]:
        q: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue(maxsize=200)
        self._event_queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any] | None]) -> None:
        if q in self._event_queues:
            self._event_queues.remove(q)

    def request_abort(self) -> None:
        self._abort_flag = True

    def should_abort(self) -> bool:
        return self._abort_flag

    def reset(self) -> None:
        self.state = RunState.idle
        self.events.clear()
        self.linearity_result = None
        self.photocycle_result = None
        self._abort_flag = False


bench_state = BenchState()
capture: Capture | None = None
projector: Projector | None = None
sensors: SensorSuite | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global capture, projector, sensors
    capture = Capture(CaptureConfig())
    projector = Projector(ProjectorConfig())
    sensors = SensorSuite()
    yield
    if projector is not None:
        projector.close()


app = FastAPI(title="Vivonics Bench Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    green_exposure_s: float = 1.0
    recovery_interval_s: float = 30.0
    settle_time_s: float = 0.5


@app.get("/status")
def get_status():
    return {
        "state": bench_state.state.value,
        "event_count": len(bench_state.events),
        "linearity_passed": (
            bench_state.linearity_result.passed
            if bench_state.linearity_result
            else None
        ),
        "photocycle_passed": (
            bench_state.photocycle_result.passed
            if bench_state.photocycle_result
            else None
        ),
        "projector_driver": projector.driver_name if projector else None,
        "sensors": sensors.availability() if sensors else None,
    }


@app.get("/sensors")
def read_sensors():
    if sensors is None:
        raise HTTPException(503, "Sensors not initialized")
    return sensors.read_all()


@app.post("/run/linearity")
def run_linearity(req: StartRequest | None = None):
    if bench_state.state in (RunState.running_linearity, RunState.running_photocycle):
        raise HTTPException(409, "Experiment already running")
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")

    bench_state.reset()
    bench_state.state = RunState.running_linearity

    config = PhotocycleConfig()
    if req and req.settle_time_s != 0.5:
        projector.config.settle_time_s = req.settle_time_s

    def worker():
        try:
            projector.open()

            def emit(event: dict[str, Any]) -> None:
                bench_state.emit(_with_sensor_snapshot(event))

            result = run_linearity_check(
                capture, projector, config,
                emit=emit,
                abort=bench_state.should_abort,
            )
            bench_state.linearity_result = result
            bench_state.state = RunState.completed
            emit({"type": "run_complete", "phase": 1, "passed": result.passed})
        except Exception as e:
            bench_state.state = RunState.failed
            bench_state.emit({"type": "error", "message": str(e)})
        finally:
            if projector is not None:
                projector.close()

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "linearity"}


@app.post("/run/photocycle")
def run_photocycle(req: StartRequest | None = None):
    if bench_state.state in (RunState.running_linearity, RunState.running_photocycle):
        raise HTTPException(409, "Experiment already running")
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")

    bench_state.reset()
    bench_state.state = RunState.running_photocycle

    config = PhotocycleConfig(
        green_exposure_s=req.green_exposure_s if req else 1.0,
        recovery_interval_s=req.recovery_interval_s if req else 30.0,
    )
    if req and req.settle_time_s != 0.5:
        projector.config.settle_time_s = req.settle_time_s

    def worker():
        try:
            projector.open()

            def emit(event: dict[str, Any]) -> None:
                bench_state.emit(_with_sensor_snapshot(event))

            lin_result = run_linearity_check(
                capture, projector, config,
                emit=emit,
                abort=bench_state.should_abort,
            )
            bench_state.linearity_result = lin_result

            if not lin_result.passed:
                bench_state.state = RunState.failed
                emit({"type": "error", "message": "Linearity check failed"})
                return

            if bench_state.should_abort():
                bench_state.state = RunState.aborted
                return

            read_level = lin_result.chosen_read_level
            idx = lin_result.red_codes.index(read_level)
            blank_ref = lin_result.blank_means[idx]

            pc_result = run_green_write_sweep(
                capture, projector, config,
                read_level=read_level,
                blank_reference=blank_ref,
                emit=emit,
                abort=bench_state.should_abort,
            )
            bench_state.photocycle_result = pc_result
            bench_state.state = RunState.completed
            emit({
                "type": "run_complete",
                "phase": 2,
                "passed": pc_result.passed,
            })
        except Exception as e:
            bench_state.state = RunState.failed
            bench_state.emit({"type": "error", "message": str(e)})
        finally:
            if projector is not None:
                projector.close()

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "photocycle"}


@app.post("/stop")
def stop_run():
    bench_state.request_abort()
    bench_state.state = RunState.aborted
    return {"status": "abort_requested"}


@app.get("/stream")
async def stream_events():
    queue = bench_state.subscribe()

    async def event_generator():
        import json

        for past_event in bench_state.events:
            yield f"data: {json.dumps(past_event)}\n\n"

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:
                        break
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            bench_state.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/frames/{name}")
def get_frame(name: str):
    frame_path = Path("/tmp/bench_frames") / name
    if not frame_path.exists():
        raise HTTPException(404, "Frame not found")
    return FileResponse(frame_path, media_type="image/png")


@app.get("/events")
def get_events():
    return {"events": bench_state.events}


def _with_sensor_snapshot(event: dict[str, Any]) -> dict[str, Any]:
    if sensors is None:
        return event
    if event.get("type") not in {
        "step",
        "pre_write",
        "green_write",
        "linearity_fit",
        "delta_t",
        "result",
    }:
        return event
    event = dict(event)
    event["aux_sensors"] = sensors.read_all()
    return event


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
