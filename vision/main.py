import cv2
from ultralytics import YOLO
import threading
from tracking import find_target, system_error

model = YOLO("yolo26n.pt")

url = "http://172.20.10.12:81/stream"    # URL til ESP32 - Webserver

cap = cv2.VideoCapture(url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Fikk ikke åpnet strømmen")
    exit()

print("Strømmen er åpnet")

latest = None       # Nyeste bilde fra kameraet ("postkassen"), None til første bilde kommer
running = True      # Settes til False for å stoppe lese-tråden


def read_frames():
    """Kjører i egen tråd: leser bilder fra kameraet hele tiden og tar bare vare på det nyeste."""
    global latest   # Endre variabelen utenfor funksjonen, ikke lag en ny lokal
    while running:
        ok, f = cap.read()
        if ok:
            latest = f  # Overskriver forrige bilde, så det aldri blir kø

# daemon=True: tråden stopper automatisk når programmet avsluttes
reader = threading.Thread(target=read_frames, daemon=True)
reader.start()

while True:
    if latest is None:
        continue
    frame = latest

    # classes=[0] = bare personer, imgsz=320 = mindre bilde for raskere YOLO
    results = model(frame, imgsz=320, classes=[0], verbose=False)
    h, w = frame.shape[:2]      # Gir høyde og bredde på bildet
    target = find_target(results[0].boxes)      # Finner målets sentrum (xt, yt), eller None

    if target is not None:
        xt, yt = target
        ex, ey = system_error(xt, yt, w, h)     # Regner ut avstanden fra bildets sentrum til målet
        print(int(ex), int(ey))


    frame = results[0].plot()   # Tegner YOLO-boksene. Vår egen tegning må komme etter, ellers males den over

    # Kryss i midten
    center = (w // 2, h //2)    # // = heltallsdivisjon, OpenCV vil ha hele piksler
    cv2.drawMarker(frame, center, (255, 0, 0), cv2.MARKER_CROSS, 20, 2)    # Farger i OpenCV er (B, G, R)

    # Prikk på målet
    if target is not None:
        person = (int(xt), int(yt))
        cv2.circle(frame, person, 5, (0,0,255), -1)     #cv2.circle(bildre, punkt, radius, farge, -1): -1 betyr at sirkeln fylles


    cv2.imshow("Turret", frame)

    if cv2.waitKey(1) == ord("q"):
        break

# Stopp lese-tråden før kameraet lukkes, ellers krasjer cap.read() i tråden
running = False
reader.join(timeout=2)      # Vent til tråden er ferdig (maks 2 s hvis strømmen henger)
cap.release()
cv2.destroyAllWindows()
