const int PAN_PIN = 25;     // Pan-servo (venstre/høyre)
const int TILT_PIN = 33;    // Tilt-servo (opp/ned)

// Servo-signal: 50 Hz, pulsbredde 1000–2000 µs = 0–180°
const int SERVO_FREQ = 50;
const int SERVO_RESOLUTION = 14;    // 14 bit: 0–16383 tilsvarer én periode på 20 ms

// Setter servoen på en pinne til en vinkel (0 - 180)
void setServo(int pin, int angle) {
  int pulse_us = map(angle, 0, 180, 1000, 2000);    // Vinkel -> pulsbredde
  int duty = (long)pulse_us * 16383 / 20000;        // Pulsbredde -> PWM-verdi ((long) hindrer at tallet blir for stort)
  ledcWrite(pin, duty);
}

// Kjører én gang når ESP32 starter
void setup() {
  Serial.begin(115200);       // Samme hastighet må brukes i Python og Serial Monitor
  Serial.setTimeout(50);      // Ikke vent mer enn 50 ms på resten av en linje

  ledcAttach(PAN_PIN, SERVO_FREQ, SERVO_RESOLUTION);     // Kobler PWM-signal til pan-pinnen
  ledcAttach(TILT_PIN, SERVO_FREQ, SERVO_RESOLUTION);    // Kobler PWM-signal til tilt-pinnen

  setServo(PAN_PIN, 90);      // Start i midten
  setServo(TILT_PIN, 90);
}

// Kjører om og om igjen: leser "pan,tilt\n" fra serial og setter servoene
void loop() {
  if (Serial.available() > 0) {                       // Har det kommet noe data?
    String line = Serial.readStringUntil('\n');      // Les til linjeskift

    int pan, tilt;
    // sscanf leser to heltall skilt med komma. Gir 2 hvis begge ble funnet.
    if (sscanf(line.c_str(), "%d,%d", &pan, &tilt) == 2) {
      pan = constrain(pan, 0, 180);                   // Aldri send servoen utenfor 0–180°
      tilt = constrain(tilt, 0, 180);

      setServo(PAN_PIN, pan);
      setServo(TILT_PIN, tilt);
      Serial.printf("OK %d,%d\n", pan, tilt);         // Bekreftelse, nyttig i Serial Monitor
    } else {
      Serial.println("Feil format, bruk: pan,tilt");
    }
  }
}
