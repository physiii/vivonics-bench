"""Persistent USB-first client for the Vivonics laser/ADC controller."""
from __future__ import annotations

import copy
import json
import logging
import os
import threading
import time
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


LOG = logging.getLogger(__name__)
PROTOCOL_PREFIX = b"VLC1 "
CHANNELS = (
    ("IR", "Infrared", 780, True),
    ("RED", "Red", 650, True),
    ("GREEN", "Green", 520, True),
    ("BLUE", "Blue", 450, False),
)


class LaserControllerClient:
    """Own one serial connection and expose a transport-neutral live snapshot.

    USB is authoritative whenever a versioned telemetry line has arrived within
    ``usb_stale_s``. Wi-Fi polling/control is the automatic fallback.
    """

    def __init__(
        self,
        usb_path: str | None = None,
        wifi_url: str | None = None,
        *,
        stream_hz: int = 25,
        usb_stale_s: float = 0.8,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.usb_path = usb_path or os.environ.get("VIVONICS_LASER_CONTROLLER_USB", "/dev/ttyACM0")
        self.wifi_url = (wifi_url or os.environ.get(
            "VIVONICS_LASER_CONTROLLER_WIFI_URL", "http://192.168.1.179"
        )).rstrip("/")
        self.stream_hz = stream_hz
        self.usb_stale_s = usb_stale_s
        self._clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._serial: Any | None = None
        self._write_lock = threading.Lock()
        self._condition = threading.Condition()
        self._snapshot: dict[str, Any] | None = None
        self._snapshot_version = 0
        self._last_usb_at = 0.0
        self._last_wifi_at = 0.0
        self._usb_open = False
        self._wifi_reachable = False
        self._failover_count = 0
        self._last_command_transport: str | None = None
        self._last_error: str | None = None
        self._usb_parse_errors = 0
        self._usb_reconnects = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="laser-controller", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        try:
            self.off(wait_for_confirmation=False)
        except Exception:
            LOG.exception("Unable to force laser controller off during close")
        serial_port = self._serial
        if serial_port is not None:
            try:
                serial_port.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def status(self) -> dict[str, Any]:
        now = self._clock()
        usb_age_ms = (now - self._last_usb_at) * 1000 if self._last_usb_at else None
        wifi_age_ms = (now - self._last_wifi_at) * 1000 if self._last_wifi_at else None
        usb_fresh = usb_age_ms is not None and usb_age_ms <= self.usb_stale_s * 1000
        wifi_fresh = wifi_age_ms is not None and wifi_age_ms <= 1000
        snapshot_transport = self._snapshot.get("transport") if self._snapshot else None
        active = "usb" if usb_fresh else (
            "wifi" if wifi_fresh and snapshot_transport == "wifi" else "unavailable"
        )
        return {
            "activeTransport": active,
            "usbConnected": self._usb_open,
            "usbFresh": usb_fresh,
            "usbPath": self.usb_path,
            "usbSampleAgeMs": round(usb_age_ms, 1) if usb_age_ms is not None else None,
            "wifiReachable": self._wifi_reachable,
            "wifiUrl": self.wifi_url,
            "wifiSampleAgeMs": round(wifi_age_ms, 1) if wifi_age_ms is not None else None,
            "streamRateHz": self.stream_hz,
            "failoverCount": self._failover_count,
            "lastCommandTransport": self._last_command_transport,
            "usbReconnects": self._usb_reconnects,
            "usbParseErrors": self._usb_parse_errors,
            "lastError": self._last_error,
        }

    def snapshot(self) -> dict[str, Any] | None:
        with self._condition:
            payload = copy.deepcopy(self._snapshot)
        if payload is None:
            return None
        payload["connection"] = self.status()
        payload["receivedAtMs"] = int(time.time() * 1000)
        return payload

    def wait_until_available(self, timeout_s: float = 5.0) -> bool:
        """Wait for fresh USB or Wi-Fi telemetry after a controller reboot."""
        deadline = time.monotonic() + max(0.0, timeout_s)
        while True:
            if self.status()["activeTransport"] != "unavailable":
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            with self._condition:
                self._condition.wait(timeout=min(0.1, remaining))

    def set_levels(
        self,
        *,
        red: int = 0,
        green: int = 0,
        infrared: int = 0,
        blue: int = 0,
        wait_for_confirmation: bool = True,
    ) -> dict[str, Any]:
        levels = [infrared, red, green, blue]
        if any(not isinstance(level, int) or level < 0 or level > 255 for level in levels):
            raise ValueError("laser levels must be integers in the range 0..255")
        duties = [round(level * 1000 / 255) for level in levels]
        return self._set_permille(duties, wait_for_confirmation=wait_for_confirmation)

    def off(self, *, wait_for_confirmation: bool = True) -> dict[str, Any]:
        return self._set_permille([0, 0, 0, 0], wait_for_confirmation=wait_for_confirmation)

    def _set_permille(self, duties: list[int], *, wait_for_confirmation: bool) -> dict[str, Any]:
        usb_ready = self.status()["usbFresh"]
        if usb_ready:
            command = "OFF\n" if not any(duties) else "LEVELS " + " ".join(map(str, duties)) + "\n"
            if self._write_usb(command.encode("ascii")):
                self._last_command_transport = "usb"
                if not wait_for_confirmation or self._wait_for_duties(duties, timeout_s=0.45):
                    return {"ok": True, "transport": "usb", "dutiesPermille": duties}
                self._record_failover("USB command was not confirmed; using Wi-Fi")

        response = self._write_wifi(duties)
        self._last_command_transport = "wifi"
        return {"ok": True, "transport": "wifi", "dutiesPermille": duties, "controller": response}

    def _wait_for_duties(self, duties: list[int], timeout_s: float) -> bool:
        deadline = self._clock() + timeout_s
        with self._condition:
            version = self._snapshot_version
            while self._clock() < deadline:
                remaining = deadline - self._clock()
                self._condition.wait(timeout=max(0.0, remaining))
                if self._snapshot_version == version:
                    continue
                version = self._snapshot_version
                if self._snapshot and self._snapshot.get("transport") == "usb":
                    actual = self._snapshot.get("output", {}).get("dutiesPermille", [])
                    if actual == duties:
                        return True
        return False

    def _write_usb(self, payload: bytes) -> bool:
        serial_port = self._serial
        if serial_port is None or not self._usb_open:
            return False
        try:
            with self._write_lock:
                serial_port.write(payload)
                serial_port.flush()
            return True
        except Exception as exc:
            self._last_error = f"USB write failed: {exc}"
            self._usb_open = False
            return False

    def _write_wifi(self, duties: list[int]) -> dict[str, Any]:
        if not any(duties):
            return self._wifi_request("/api/lasers/off", method="POST", payload={})
        channels = [
            {"target": CHANNELS[index][0], "dutyPermille": duty}
            for index, duty in enumerate(duties)
            if duty > 0
        ]
        return self._wifi_request("/api/lasers", method="POST", payload={"channels": channels})

    def _wifi_request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.wifi_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            with urlopen(request, timeout=0.5) as response:
                result = json.loads(response.read().decode("utf-8"))
            self._wifi_reachable = True
            self._last_wifi_at = self._clock()
            return result
        except (OSError, URLError, ValueError) as exc:
            self._wifi_reachable = False
            self._last_error = f"Wi-Fi request failed: {exc}"
            raise RuntimeError(self._last_error) from exc

    def _run(self) -> None:
        retry_at = 0.0
        stream_command_at = 0.0
        wifi_poll_at = 0.0
        while not self._stop.is_set():
            now = self._clock()
            if self._serial is None and now >= retry_at:
                try:
                    self._serial = self._open_serial()
                    self._usb_open = True
                    self._usb_reconnects += 1
                    stream_command_at = now + 1.0
                    LOG.info("Laser controller USB opened at %s", self.usb_path)
                except Exception as exc:
                    self._usb_open = False
                    self._last_error = f"USB open failed: {exc}"
                    retry_at = now + 1.0

            serial_port = self._serial
            if serial_port is not None:
                try:
                    line = serial_port.readline()
                    if line:
                        self._handle_usb_line(line)
                    now = self._clock()
                    if now >= stream_command_at and now - self._last_usb_at > 0.5:
                        self._write_usb(f"STREAM {self.stream_hz}\n".encode("ascii"))
                        stream_command_at = now + 1.0
                except Exception as exc:
                    self._last_error = f"USB read failed: {exc}"
                    self._usb_open = False
                    try:
                        serial_port.close()
                    except Exception:
                        pass
                    self._serial = None
                    retry_at = self._clock() + 1.0

            now = self._clock()
            usb_fresh = self._last_usb_at and now - self._last_usb_at <= self.usb_stale_s
            if not usb_fresh and now >= wifi_poll_at:
                if self._last_usb_at and self._snapshot and self._snapshot.get("transport") == "usb":
                    self._record_failover("USB telemetry stale; using Wi-Fi")
                try:
                    payload = self._wifi_request("/api/telemetry")
                    self._publish(self._normalize_wifi(payload))
                except RuntimeError:
                    pass
                wifi_poll_at = now + 0.1

            self._stop.wait(0.005)

    def _open_serial(self) -> Any:
        import serial

        port = serial.Serial()
        port.port = self.usb_path
        port.baudrate = 115200
        port.timeout = 0.04
        port.write_timeout = 0.25
        port.dtr = False
        port.rts = False
        port.open()
        port.reset_input_buffer()
        return port

    def _handle_usb_line(self, line: bytes) -> None:
        if not line.startswith(PROTOCOL_PREFIX):
            return
        try:
            payload = json.loads(line[len(PROTOCOL_PREFIX):])
            normalized = self._normalize_usb(payload)
        except (ValueError, TypeError, KeyError) as exc:
            self._usb_parse_errors += 1
            self._last_error = f"USB telemetry parse failed: {exc}"
            return
        self._last_usb_at = self._clock()
        self._last_error = None
        self._publish(normalized)

    def _publish(self, payload: dict[str, Any]) -> None:
        with self._condition:
            self._snapshot = payload
            self._snapshot_version += 1
            self._condition.notify_all()

    def _record_failover(self, reason: str) -> None:
        self._failover_count += 1
        self._last_error = reason
        LOG.warning(reason)

    @staticmethod
    def _normalize_usb(payload: dict[str, Any]) -> dict[str, Any]:
        counts = payload["photodiodeCounts"]
        duties = payload["output"]["dutiesPermille"]
        current_raw = payload["currentSenseRaw"]
        current_mv = payload["currentSenseMillivolts"]
        monitor_raw = payload["sourceMonitorRaw"]
        monitor_mv = payload["sourceMonitorMillivolts"]
        output = dict(payload["output"])
        output["channels"] = [
            {"target": CHANNELS[index][0], "dutyPermille": duty}
            for index, duty in enumerate(duties)
            if duty > 0
        ]
        return {
            "ok": True,
            "protocolVersion": 1,
            "transport": "usb",
            "sampleIndex": payload["sampleIndex"],
            "sampledAtUs": payload["sampledAtUs"],
            "sampleRateHz": payload["sampleRateHz"],
            "timingOverruns": payload["timingOverruns"],
            "safetyState": payload["safetyState"],
            "faultMask": payload["faultMask"],
            "output": output,
            "photodiodes": [
                {
                    "channel": index + 1,
                    "name": "Signal photodiode",
                    "counts": count,
                    "volts": count * 5.0 / 32768.0,
                }
                for index, count in enumerate(counts)
            ],
            "lasers": [
                {
                    "channel": index + 1,
                    "target": target,
                    "name": name,
                    "wavelengthNm": wavelength,
                    "active": duties[index] > 0,
                    "dutyPermille": duties[index],
                    "currentSense": {"raw": current_raw[index], "millivolts": current_mv[index]},
                    "sourceMonitor": {
                        "raw": monitor_raw[index],
                        "millivolts": monitor_mv[index],
                        "equipped": equipped,
                    },
                }
                for index, (target, name, wavelength, equipped) in enumerate(CHANNELS)
            ],
        }

    @staticmethod
    def _normalize_wifi(payload: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(payload)
        result["protocolVersion"] = 1
        result["transport"] = "wifi"
        duties = [0, 0, 0, 0]
        by_target = {entry.get("target"): entry.get("dutyPermille", 0) for entry in payload.get("lasers", [])}
        for index, (target, _name, _wavelength, _equipped) in enumerate(CHANNELS):
            duties[index] = int(by_target.get(target, 0))
        result.setdefault("output", {})["dutiesPermille"] = duties
        return result
