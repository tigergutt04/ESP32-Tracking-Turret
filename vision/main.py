import cv2
from ultralytics import YOLO
import threading
import time
import math
from tracking import find_target, system_error
from serial_link import connect, send_angles
from pid import PID

model = YOLO("yolov8n-pose.pt")     # Pose-modell: finner personer og 17 kroppspunkter (nese, øyne, skuldre ...)

HFOV_DEG = 50.0     # Kameraets horisontale synsvinkel i grader. MÅ måles for deres kamera, dette er bare et startpunkt

CONFIDENCE = 0.5    # YOLO må være minst 50 % sikker før en person regnes som funnet

PAN_DIR = -1       # Fortegn for pan-servoen (snu hvis den går feil vei)
TILT_DIR = -1       # Fortegn for tilt-servoen (snu hvis den går feil vei)

# Én PID per akse. Start med bare P, øk Ki og Kd forsiktig
# Kp 0.25: kamerastrømmen henger noen bilder etter, og høyere Kp skyter over når målet bygger på forrige mål
pan_pid = PID(kp=0.25, ki=0.0, kd=0.0, alpha=0.5, deadzone=2.0, stop_zone=0.75, i_limit=10.0)
tilt_pid = PID(kp=0.25, ki=0.0, kd=0.0, alpha=0.5, deadzone=2.0, stop_zone=0.75, i_limit=10.0)

HOME_PAN, HOME_TILT = 90, 130    # Startposisjon for tårnet


def pixel_to_angle(ex, ey, width):
    """Gjør om system error i piksler (ex, ey) til vinkelavvik i grader (pan, tilt) med tan(theta) = e / f."""
    # f = brennvidden i piksler: avstanden fra kameraet til bildeplanet, regnet ut fra synsvinkelen
    f = (width / 2) / math.tan(math.radians(HFOV_DEG / 2))
    pan_angle = math.degrees(math.atan(ex / f))     # theta = arctan(e / f)
    tilt_angle = math.degrees(math.atan(ey / f))    # Samme f i begge retninger, siden pikslene er kvadratiske
    return pan_angle, tilt_angle

url = "http://172.20.10.12:81/stream"    # URL til ESP32 - Webserver

cap = cv2.VideoCapture(url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Fikk ikke åpnet strømmen")
    exit()

print("Strømmen er åpnet")

ser = connect()     # Serial til turret-ESP32 (COM3). Serial Monitor i Arduino IDE må være lukket
pan, tilt = HOME_PAN, HOME_TILT  # Forrige mål sendt til servoene. Ny vinkel = dette + korreksjon
send_angles(ser, pan, tilt)
print("ESP32 tilkoblet")

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

prev = None         # Forrige bilde vi behandlet

while True:
    # Vent på et nytt bilde. cap.read() lager et nytt objekt hver gang, så "is" ser om bildet er byttet
    # Uten dette regnet PID-en korreksjon flere ganger på samme gamle feil -> rykk og overskyting
    if latest is None or latest is prev:
        time.sleep(0.001)   # Kort pause, så ventingen ikke tar CPU fra lese-tråden
        continue
    frame = prev = latest

    # classes=[0] = bare personer, imgsz=320 = mindre bilde for raskere YOLO, conf = minste sikkerhet
    results = model(frame, imgsz=320, classes=[0], conf=CONFIDENCE, verbose=False)
    h, w = frame.shape[:2]      # Gir høyde og bredde på bildet
    target = find_target(results[0])            # Finner ansiktet (xt, yt), eller None

    if target is not None:
        xt, yt = target
        ex, ey = system_error(xt, yt, w, h)     # Regner ut avstanden fra bildets sentrum til målet
        pan_err, tilt_err = pixel_to_angle(ex, ey, w)   # Avstanden i grader

        # PID gir korreksjonen (0 i dødsonen)
        pan_u = PAN_DIR * pan_pid.update(pan_err)
        tilt_u = TILT_DIR * tilt_pid.update(tilt_err)

        if pan_u != 0 or tilt_u != 0:     # I dødsonen: ingenting å sende, servoene blir stående
            # Målvinkel = forrige mål + korreksjon, holdt innenfor 0–180°
            pan_target = min(180, max(0, pan + pan_u))
            tilt_target = min(180, max(0, tilt + tilt_u))
            pos = send_angles(ser, pan_target, tilt_target)     # Der servoen står, (pan, tilt) eller None
            # Bygg på målet, ikke POS-svaret: svaret er én runde gammelt og ga sikksakk mellom to mål
            pan, tilt = pan_target, tilt_target
            print(f"feil: {pan_err:+.1f}°, {tilt_err:+.1f}°  ->  mål: {pan_target:.0f}, {tilt_target:.0f}  står: {pos}")
    else:
        pan_pid.reset()     # Ingen mål: glem gammel feil, så et nytt mål ikke arver den
        tilt_pid.reset()


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
send_angles(ser, HOME_PAN, HOME_TILT)    # Sett tårnet tilbake i startposisjon før vi avslutter
ser.close()
cv2.destroyAllWindows()
