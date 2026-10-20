# Tracking Turret

## Overview
The project is a camera-based tracking turret designed to detect and track a person using computer vision.

An ESP32-CAM streams video to a laptop running object detection and tracking software. The tracking data is then sent to an ESP32, which controls a pan-tilt mechanism using two servo motors.

When the system achieves a stable target lock, it can trigger a light indicator and play a randomly selected voice line.

The purpose of the project is to explore computer vision, embedded systems, control, communication between devices, and mechanical design.

## Goals
The goal of the project is to create a real-time target tracking turret with minimal tracking latency and smooth, responsive movement.

## System Architecture
```text
ESP32-CAM
    |
    | WiFi Video Stream
    v
Laptop
    |
    +-- OpenCV
    +-- YOLOv8
    +-- Python Tracking Logic
    |
    | Serial / USB
    v
ESP32
    |
    +-- Pan Servo
    +-- Tilt Servo
    |
    v
Pan-Tilt Mechanism
```

## Hardware
- ESP32-Cam
- Laptop
- ESP32
- 2xServo Motors
- Speaker

## Software
- Python
- YOLOv8
- OpenCV
- ESP32 Firmware
    - Serial Communication
    - Pan-Tilt Servo Control

## How It Works
The ESP32-CAM streams live video to the laptop. OpenCV reads the video stream and passes the frames to YOLOv8, which detects the target.

A Python script then calculates the target position in the image and sends the required movement commands to the ESP32. The ESP32 controls the pan-tilt servos and moves the turret toward the detected target.

## Repository Structure
```text
tracking-turret/
│
├── README.md
├── .gitignore
│
├── vision/
│   └── main.py
│
├── firmware/
│   ├── esp32_cam/
│   │   └── main.cpp
│   │
│   └── turret_controller/
│       └── main.cpp
│
├── audio/
│
├── hardware/
│   ├── cad/
│   └── wiring.md

```

## Development Plan

### Phase 1 - Video Stream
- Set up the ESP32-CAM
- Stream live video over WiFi
- Read the video stream on the laptop using OpenCV

### Phase 2 - Object Detection
- Set up YOLOv8
- Detect a person in the video stream
- Extract the target position

### Phase 3 - Servo Control
- Connect the ESP32 to the two servo motors
- Implement pan and tilt movement
- Set servo movement limits

### Phase 4 - Communication
- Establish serial communication between the laptop and ESP32
- Send movement commands from the laptop to the ESP32

### Phase 5 - Tracking
- Connect target detection to the pan-tilt system
- Make the turret follow the detected target
- Improve tracking speed and stability

### Phase 6 - Target Lock
- Detect when the target is centered
- Add a target lock state
- Trigger the light indicator and voice line

### Phase 7 - Optimization
- Reduce tracking latency
- Improve movement smoothness
- Tune the tracking and servo control
