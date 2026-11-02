import cv2
from ultralytics import YOLO
import threading

model = YOLO("yolov8n.pt")

url = "http://172.20.10.12:81/stream"    # URL til ESP32 - Webserver

cap = cv2.VideoCapture(url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Fikk ikke åpnet strømmen")
    exit()

print("Strømmen er åpnet")

latest = None
running = True


def read_frames():
    global latest
    while running:
        ok, f = cap.read()
        if ok:
            latest = f

threading.Thread(target=read_frames, daemon=True).start()

while True:
    if latest is None:
        continue
    frame = latest

    results = model(frame, imgsz=320, classes=[0], verbose=False)
    frame = results[0].plot()
    
    cv2.imshow("Turret", frame)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()