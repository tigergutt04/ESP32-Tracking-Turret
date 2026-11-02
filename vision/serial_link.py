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
    """Sender vinklene som "pan,tilt\\n" til ESP32."""
    ser.reset_input_buffer()    # Kast "OK"-svar vi ikke leser, så de ikke hoper seg opp
    ser.write(f"{int(pan)},{int(tilt)}\n".encode())    # ESP32 leser heltall, encode() gjør tekst om til bytes


# Test: kjør "python serial_link.py" for å flytte servoene uten kamera og YOLO
if __name__ == "__main__":
    ser = connect()
    for pan, tilt in [(90, 90), (60, 90), (120, 90), (90, 60), (90, 120), (90, 90)]:
        send_angles(ser, pan, tilt)
        time.sleep(1)
        print(ser.readline().decode().strip())    # Skriver ut svaret fra ESP32, f.eks. "OK 60,90"
    ser.close()
