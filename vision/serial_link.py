import serial
import time

ESP32_PORT = "COM3"     # Turret-ESP32 (kameraet på COM4 brukes bare til opplasting, video går over WiFi)
BAUD = 115200           # Må være lik Serial.begin(...) i turret_controller.ino


def connect(port=ESP32_PORT, baud=BAUD):
    """Åpner serial-forbindelsen til ESP32 og venter til den er klar. Gir tilbake forbindelsen."""
    ser = serial.Serial(port, baud, timeout=0.1)
    time.sleep(2)               # ESP32 restarter når porten åpnes, vent til setup() er ferdig
    ser.reset_input_buffer()    # Kast oppstartsmeldinger fra ESP32
    return ser


def send_angles(ser, pan, tilt):
    """Sender målvinklene som "pan,tilt\\n" til ESP32. Gir tilbake (pan, tilt) der servoene faktisk står, eller None."""
    ser.reset_input_buffer()    # Kast gamle svar, så vi leser svaret på akkurat denne meldingen
    ser.write(f"{round(pan)},{round(tilt)}\n".encode())    # ESP32 leser heltall, encode() gjør tekst om til bytes

    reply = ser.readline().decode(errors="ignore").strip()    # Venter maks 0.1 s (timeout i connect)
    if not reply.startswith("POS "):
        return None     # Ingen eller ukjent svar
    pan_now, tilt_now = reply[4:].split(",")     # "POS 92.4,158.0" -> "92.4" og "158.0"
    return float(pan_now), float(tilt_now)


# Test: kjør "python serial_link.py" for å flytte servoene uten kamera og YOLO
if __name__ == "__main__":
    ser = connect()
    for pan, tilt in [(90, 90), (60, 90), (120, 90), (90, 60), (90, 120), (90, 90)]:
        print(send_angles(ser, pan, tilt))    # Skriver ut der servoene står, f.eks. (90.0, 90.0)
        time.sleep(1)
    ser.close()
