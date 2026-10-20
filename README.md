# ESP32-Tracking-Turret

## How it works
ESP32-Cam 
  ↓ Wifi - Video - Stream
Laptop running Python + Yolo
  ↓ 
Target Position / Serial Movement command
  ↓ Serial USB
ESP32 
  ↓
Pan + Tilt Servos
  ↓
Continuous Camera tracking
