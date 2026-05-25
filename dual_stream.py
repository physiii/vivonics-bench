"""Start Picamera2 with simultaneous raw capture + RTSP monitor stream.

Usage:
    from dual_stream import start_dual_camera, stop_dual_camera

    cam = start_dual_camera(config_overrides={...})
    # cam.capture_array("raw") works as before
    # RTSP stream is live at rtsp://127.0.0.1:8554/cam
    ...
    stop_dual_camera(cam)
"""

import subprocess
import time
import os

CAMERA_RTSP_SERVICE = os.environ.get("VIVONICS_CAMERA_RTSP_SERVICE", "c1-camera-rtsp")
RTSP_URL = os.environ.get("VIVONICS_RTSP_URL", "rtsp://127.0.0.1:8554/cam")

_encoder = None
_output = None


def start_dual_camera(
    main_size=(640, 480),
    raw_size=(1332, 990),
    raw_format="SBGGR10_CSI2P",
    controls=None,
    rtsp_url=None,
    bitrate=4_000_000,
):
    """Start Picamera2 with raw capture AND an H264 RTSP monitor stream.

    Stops the system rpicam-vid RTSP service first (it holds the camera),
    then starts Picamera2 with a hardware H264 encoder on the main stream
    piped to MediaMTX via ffmpeg. Raw capture_array("raw") works normally.
    """
    global _encoder, _output
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FfmpegOutput

    url = rtsp_url or RTSP_URL

    # Stop the rpicam-vid based RTSP service to free the camera
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", CAMERA_RTSP_SERVICE],
            check=True, timeout=10,
        )
        time.sleep(0.5)
    except subprocess.SubprocessError:
        pass

    default_controls = {
        "FrameDurationLimits": (8298, 8298),
        "ExposureTime": 2000,
        "AnalogueGain": 1.0,
        "AeEnable": False, "AwbEnable": False,
        "ColourGains": (1.0, 1.0),
        "NoiseReductionMode": 0,
    }
    if controls:
        default_controls.update(controls)

    cam = Picamera2()
    config = cam.create_video_configuration(
        main={"size": main_size, "format": "RGB888"},
        raw={"size": raw_size, "format": raw_format},
        controls=default_controls,
    )
    cam.configure(config)

    _encoder = H264Encoder(bitrate=bitrate, repeat=True, iperiod=15)
    _output = FfmpegOutput(
        f"-f rtsp -rtsp_transport tcp {url}",
        audio=False,
    )

    cam.start()
    time.sleep(0.3)

    try:
        cam.start_encoder(_encoder, _output)
        print(f"  Monitor stream live at {url}")
    except Exception as e:
        print(f"  Warning: could not start monitor stream: {e}")
        _encoder = None
        _output = None

    time.sleep(1.2)
    return cam


def stop_dual_camera(cam):
    """Stop the encoder, camera, and restart the system RTSP service."""
    global _encoder, _output

    if _encoder is not None:
        try:
            cam.stop_encoder(_encoder)
        except Exception:
            pass
        _encoder = None
        _output = None

    cam.stop()
    cam.close()

    # Restart the rpicam-vid RTSP service
    try:
        subprocess.run(
            ["systemctl", "--user", "start", CAMERA_RTSP_SERVICE],
            check=True, timeout=15,
        )
    except subprocess.SubprocessError:
        pass
