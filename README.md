# Tracking Turret

## Overview
The project is a camera-based tracking turret designed to detect and track a person's face using computer vision.

An ESP32-CAM streams video to a laptop running object detection and tracking software. The tracking data is then sent to an ESP32, which controls a pan-tilt mechanism using two servo motors.

When the system achieves a stable target lock, the ESP32 plays a randomly selected voice line through a speaker.

The purpose of the project is to explore computer vision, embedded systems, control, communication between devices, and mechanical design.

## Goals
The goal of the project is to create a real-time target tracking turret with minimal tracking latency and smooth, responsive movement.

## System Architecture
```text
ESP32-CAM (320x240 MJPEG)
    |
    | WiFi Video Stream
    v
Laptop
    |
    +-- OpenCV (stream reader thread, latest frame only)
    +-- YOLOv8n-pose (person + face keypoints)
    +-- Python Tracking Logic (system error -> angle -> PID)
    |
    | Serial / USB  ("pan,tilt\n"  ->  "POS pan,tilt")
    v
ESP32
    |
    +-- Pan Servo  (GPIO25)
    +-- Tilt Servo (GPIO33)
    +-- Speaker
    |
    v
Pan-Tilt Mechanism
```

## Hardware
- ESP32-CAM (AI Thinker, OV3660)
- Laptop
- ESP32
- 2x Servo Motors (pan on GPIO25, tilt on GPIO33)
- Speaker (driven by the turret ESP32)

## Software
- Python
    - OpenCV
    - Ultralytics YOLOv8n-pose
    - pyserial
- ESP32 Firmware (Arduino)
    - Camera web server (ESP32-CAM)
    - Serial Communication
    - Pan-Tilt Servo Control with speed limit
    - Voice Line Playback

## How It Works
1. **Video:** The ESP32-CAM streams 320x240 JPEG video over WiFi. A background thread in Python reads the stream and keeps only the newest frame, so no frames queue up and the latency stays low.
2. **Detection:** YOLOv8n-pose finds the person (confidence >= 50 %) and 17 body keypoints.
3. **Target:** `find_target` aims at the nose. If the nose is not visible it uses the visible eyes/ears, and otherwise a point 15 % below the top of the bounding box.
4. **System error:** `system_error` computes the offset between the image centre and the target:

   e_x = x_c - x_t,  e_y = y_c - y_t

5. **Angle:** `pixel_to_angle` converts the pixel error to an angle error using the camera's field of view:

   theta = arctan(e / f),  f = (width / 2) / tan(HFOV / 2)

6. **PID:** One PID controller per axis turns the angle error into a correction:
    - EMA smoothing: e_s = alpha * e + (1 - alpha) * e_s,prev
    - Deadzone: errors smaller than the deadzone are ignored, so the turret stands still
    - PID: u = Kp * e_s + Ki * sum(e_s * dt) + Kd * (e_s - e_s,prev) / dt
    - Anti-windup: the integral is limited, and everything resets when the target is lost
7. **Serial:** The new target angle (real servo position + correction) is sent to the ESP32 as `pan,tilt\n`. The ESP32 replies with the real servo position `POS pan,tilt`, which Python uses as the base for the next correction.
8. **Servos:** The ESP32 moves the servos towards the target angle in 20 ms steps with a maximum speed (150 deg/s), so the movement is smooth even though new angles only arrive a few times per second.

## Setup

### ESP32-CAM
1. Open `firmware/esp32_cam/CameraWebServer/CameraWebServer.ino` in Arduino IDE.
2. Copy `secrets.example.h` to `secrets.h` and fill in the WiFi name and password (`secrets.h` is ignored by git).
3. Board: **AI Thinker ESP32-CAM**. Upload.
4. The Serial Monitor (115200 baud) shows the camera's IP address. The laptop must be on the same WiFi network.

### Turret ESP32
1. Open `firmware/turret_controller/turret_controller.ino` in Arduino IDE.
2. Board: **ESP32 Dev Module**. Upload.
3. Test in Serial Monitor (115200 baud, "New Line"): type `90,160` and press Enter.

### Python
```text
cd vision
pip install -r requirements.txt
python main.py
```
- Set the camera URL at the top of `main.py` and the serial port in `serial_link.py` (default `COM3`).
- Close the Serial Monitor and the camera page in the browser before running.
- Press `q` in the video window to quit. The turret returns to its start position (90, 160).
- `python serial_link.py` moves the servos without camera and YOLO. `python pid.py` tests the PID math.

## Tuning
| Setting | File | Value | Effect |
|---|---|---|---|
| `HFOV_DEG` | `vision/main.py` | 60 | Camera field of view. Must be measured for the camera |
| `CONFIDENCE` | `vision/main.py` | 0.5 | Minimum YOLO confidence |
| `kp`, `ki`, `kd` | `vision/main.py` | 0.5, 0, 0 | PID gains |
| `alpha` | `vision/main.py` | 0.7 | EMA smoothing (1 = none, lower = calmer but slower) |
| `deadzone` | `vision/main.py` | 2 deg | Errors smaller than this are ignored |
| `PAN_DIR`, `TILT_DIR` | `vision/main.py` | -1, -1 | Flip if an axis moves the wrong way |
| `HOME_PAN`, `HOME_TILT` | `main.py` and `.ino` | 90, 160 | Start position |
| `MAX_SPEED` | `turret_controller.ino` | 150 deg/s | Maximum servo speed |

Because the correction is added to the current angle, the P term already acts partly like an integrator. Increase `ki` carefully to avoid overshoot.

## Repository Structure
```text
tracking-turret/
│
├── README.md
├── .gitignore
│
├── vision/
│   ├── main.py             (stream, YOLO, tracking loop, pixel_to_angle)
│   ├── tracking.py         (find_target, system_error)
│   ├── pid.py              (PID with EMA, deadzone, anti-windup)
│   ├── serial_link.py      (connect, send_angles)
│   └── requirements.txt
│
├── firmware/
│   ├── esp32_cam/
│   │   └── CameraWebServer/      (Arduino sketch, copy secrets.example.h to secrets.h)
│   │
│   └── turret_controller/
│       └── turret_controller.ino
│
├── audio/
│
└── hardware/
    ├── cad/
    └── wiring.md
```

## Development Plan

### Phase 1 - Video Stream ✅
- Set up the ESP32-CAM
- Stream live video over WiFi
- Read the video stream on the laptop using OpenCV

### Phase 2 - Object Detection ✅
- Set up YOLOv8
- Detect a person in the video stream
- Extract the target position (face via pose keypoints)

### Phase 3 - Servo Control ✅
- Connect the ESP32 to the two servo motors
- Implement pan and tilt movement
- Set servo movement limits

### Phase 4 - Communication ✅
- Establish serial communication between the laptop and ESP32
- Send movement commands from the laptop to the ESP32

### Phase 5 - Tracking ✅
- Connect target detection to the pan-tilt system
- Make the turret follow the detected target
- Improve tracking speed and stability (PID, EMA, deadzone, speed limit)

### Phase 6 - Target Lock
- Detect when the target is centered
- Add a target lock state
- Play a voice line from the ESP32

### Phase 7 - Optimization
- Reduce tracking latency
- Improve movement smoothness
- Tune the tracking and servo control

## Acknowledgements
- [mmm1712/ESP32-CAM-AI-Object-Tracking](https://github.com/mmm1712/ESP32-CAM-AI-Object-Tracking) was used as a reference for the latest-frame reader, EMA smoothing and deadzone ideas.
- The ESP32-CAM firmware is based on the Espressif `CameraWebServer` example.
