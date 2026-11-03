#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PCA9685 servo-kontroller over I2C (SDA = GPIO21, SCL = GPIO22, adresse 0x40)
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

const int PAN_CH = 0;       // Pan-servo (venstre/høyre) på kanal 0
const int TILT_CH = 1;      // Tilt-servo (opp/ned) på kanal 1

// Servo-signal: 50 Hz, pulsbredde 1000–2000 µs = 0–180°
const int SERVO_FREQ = 50;

// Fartsgrense: servoene glir mot målvinkelen i stedet for å hoppe
const float MAX_SPEED = 150.0;      // Maks fart i grader per sekund
const int STEP_MS = 20;             // Oppdaterer servoene hvert 20. ms (samme som servo-perioden)

// Startposisjon (samme som HOME i main.py)
const float HOME_PAN = 90.0;
const float HOME_TILT = 160.0;

float panNow = HOME_PAN, tiltNow = HOME_TILT;           // Der servoene står nå
float panTarget = HOME_PAN, tiltTarget = HOME_TILT;     // Der Python vil at de skal stå
unsigned long lastStep = 0;                             // Tidspunkt (ms) for forrige oppdatering

// Setter servoen på en PCA9685-kanal til en vinkel (0 - 180). float gir finere steg enn hele grader
void setServo(int channel, float angle) {
  float pulse_us = 1000.0 + angle / 180.0 * 1000.0;   // Vinkel -> pulsbredde
  pwm.writeMicroseconds(channel, pulse_us);           // PCA9685 lager selve PWM-signalet
}

// Flytter "now" mot "target", men aldri mer enn maxStep. Gir tilbake ny posisjon
float stepToward(float now, float target, float maxStep) {
  float diff = target - now;
  if (diff > maxStep) return now + maxStep;
  if (diff < -maxStep) return now - maxStep;
  return target;    // Nær nok: gå rett dit
}

// Kjører én gang når ESP32 starter
void setup() {
  Serial.begin(115200);       // Samme hastighet må brukes i Python og Serial Monitor
  Serial.setTimeout(50);      // Ikke vent mer enn 50 ms på resten av en linje

  pwm.begin();                          // Starter I2C og PCA9685
  pwm.setOscillatorFrequency(27000000); // Klokka på PCA9685-brettet, trengs for riktig pulsbredde
  pwm.setPWMFreq(SERVO_FREQ);           // 50 Hz servo-signal

  setServo(PAN_CH, panNow);
  setServo(TILT_CH, tiltNow);
}

// Kjører om og om igjen: leser nye målvinkler og flytter servoene jevnt mot dem
void loop() {
  // 1. Ny melding "pan,tilt\n" fra Python? Da oppdateres bare målet, ikke servoene direkte
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');      // Les til linjeskift

    int pan, tilt;
    // sscanf leser to heltall skilt med komma. Gir 2 hvis begge ble funnet.
    if (sscanf(line.c_str(), "%d,%d", &pan, &tilt) == 2) {
      panTarget = constrain(pan, 0, 180);             // Aldri send servoen utenfor 0–180°
      tiltTarget = constrain(tilt, 0, 180);
      Serial.printf("POS %.1f,%.1f\n", panNow, tiltNow);  // Svar med der servoene faktisk står nå
    } else {
      Serial.println("Feil format, bruk: pan,tilt");
    }
  }

  // 2. Hvert STEP_MS: flytt servoene et lite steg mot målet
  unsigned long now = millis();
  if (now - lastStep >= STEP_MS) {
    float dt = (now - lastStep) / 1000.0;   // Sekunder siden forrige steg
    lastStep = now;
    float maxStep = MAX_SPEED * dt;         // Lengste steg vi får ta nå, i grader

    panNow = stepToward(panNow, panTarget, maxStep);
    tiltNow = stepToward(tiltNow, tiltTarget, maxStep);
    setServo(PAN_CH, panNow);
    setServo(TILT_CH, tiltNow);
  }
}
