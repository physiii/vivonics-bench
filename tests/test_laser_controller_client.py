from __future__ import annotations

import json
import threading

from laser_controller_client import LaserControllerClient, PROTOCOL_PREFIX


def usb_payload(*, duties: list[int] | None = None) -> dict:
    return {
        "type": "telemetry",
        "sampleIndex": 42,
        "sampledAtUs": 123456,
        "sampleRateHz": 50,
        "timingOverruns": 0,
        "safetyState": 2,
        "faultMask": 0,
        "output": {
            "active": bool(duties and any(duties)),
            "latched": bool(duties and any(duties)),
            "channelMask": 0,
            "dutyPermille": max(duties or [0]),
            "dutiesPermille": duties or [0, 0, 0, 0],
        },
        "photodiodeCounts": [32768, 16384, 0, -16384],
        "currentSenseRaw": [1, 2, 3, 4],
        "currentSenseMillivolts": [10, 20, 30, 40],
        "sourceMonitorRaw": [5, 6, 7, 8],
        "sourceMonitorMillivolts": [50, 60, 70, 80],
    }


def test_usb_protocol_is_normalized_to_named_channels() -> None:
    now = [10.0]
    client = LaserControllerClient(clock=lambda: now[0])
    client._usb_open = True
    line = PROTOCOL_PREFIX + json.dumps(usb_payload(duties=[125, 250, 0, 1000])).encode() + b"\n"

    client._handle_usb_line(line)
    snapshot = client.snapshot()

    assert snapshot is not None
    assert snapshot["transport"] == "usb"
    assert snapshot["photodiodes"][0]["volts"] == 5.0
    assert [laser["target"] for laser in snapshot["lasers"]] == ["IR", "RED", "GREEN", "BLUE"]
    assert snapshot["lasers"][1]["dutyPermille"] == 250
    assert snapshot["lasers"][3]["sourceMonitor"]["equipped"] is False
    assert snapshot["connection"]["activeTransport"] == "usb"


def test_malformed_versioned_line_is_counted_without_replacing_snapshot() -> None:
    client = LaserControllerClient()
    client._handle_usb_line(PROTOCOL_PREFIX + b"not-json\n")

    assert client.snapshot() is None
    assert client.status()["usbParseErrors"] == 1


def test_wait_until_available_crosses_controller_reboot_window() -> None:
    client = LaserControllerClient()
    client._usb_open = True
    line = PROTOCOL_PREFIX + json.dumps(usb_payload()).encode() + b"\n"
    publisher = threading.Timer(0.01, client._handle_usb_line, args=(line,))

    publisher.start()
    try:
        assert client.wait_until_available(timeout_s=0.25)
    finally:
        publisher.join()


def test_wifi_normalization_preserves_controller_schema_and_adds_duties() -> None:
    payload = {
        "ok": True,
        "sampleIndex": 8,
        "output": {"active": True},
        "photodiodes": [],
        "lasers": [
            {"target": "GREEN", "dutyPermille": 400},
            {"target": "IR", "dutyPermille": 100},
        ],
    }

    normalized = LaserControllerClient._normalize_wifi(payload)

    assert normalized["transport"] == "wifi"
    assert normalized["output"]["dutiesPermille"] == [100, 0, 400, 0]


def test_level_mapping_uses_wifi_when_usb_is_not_fresh() -> None:
    client = LaserControllerClient()
    requests: list[tuple[str, str, dict]] = []

    def fake_request(path: str, *, method: str = "GET", payload=None):
        requests.append((path, method, payload))
        return {"ok": True}

    client._wifi_request = fake_request  # type: ignore[method-assign]

    result = client.set_levels(red=255, green=128, infrared=0, blue=1)

    assert result["transport"] == "wifi"
    assert requests == [
        (
            "/api/lasers",
            "POST",
            {
                "channels": [
                    {"target": "RED", "dutyPermille": 1000},
                    {"target": "GREEN", "dutyPermille": 502},
                    {"target": "BLUE", "dutyPermille": 4},
                ]
            },
        )
    ]


def test_all_zero_levels_use_wifi_off_endpoint() -> None:
    client = LaserControllerClient()
    requests: list[tuple[str, str, dict]] = []
    client._wifi_request = lambda path, *, method="GET", payload=None: (  # type: ignore[method-assign]
        requests.append((path, method, payload)) or {"ok": True}
    )

    result = client.off()

    assert result["transport"] == "wifi"
    assert requests == [("/api/lasers/off", "POST", {})]


def test_levels_reject_out_of_range_values() -> None:
    client = LaserControllerClient()
    try:
        client.set_levels(red=256)
    except ValueError as exc:
        assert "0..255" in str(exc)
    else:
        raise AssertionError("expected a ValueError")
