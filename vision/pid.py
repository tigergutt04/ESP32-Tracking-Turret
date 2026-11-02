import time


class PID:
    """PID-regulator for én akse, med EMA-utjevning, dødsone og anti-windup."""

    def __init__(self, kp, ki, kd, alpha, deadzone, i_limit):
        """Lagrer innstillingene og starter med nullstilt tilstand."""
        self.kp = kp                # P: reagerer på feilen nå
        self.ki = ki                # I: reagerer på summen av feilen over tid
        self.kd = kd                # D: reagerer på hvor fort feilen endrer seg
        self.alpha = alpha          # EMA: 1 = ingen utjevning, lavere = roligere men tregere
        self.deadzone = deadzone    # Feil mindre enn dette (grader) ignoreres
        self.i_limit = i_limit      # Anti-windup: I-summen kan aldri bli større enn dette
        self.reset()

    def reset(self):
        """Glemmer alt fra før. Brukes når målet forsvinner."""
        self.smoothed = None        # Utjevnet feil (EMA), None til første måling
        self.integral = 0.0         # Summen av feil * dt
        self.prev_error = 0.0       # Forrige feil, for D-leddet
        self.prev_time = None       # Tidspunkt for forrige måling, for dt

    def update(self, error):
        """Tar inn ny vinkelfeil (grader) og gir tilbake hvor mye vinkelen skal endres (grader)."""
        now = time.time()
        dt = 0.0 if self.prev_time is None else now - self.prev_time    # Sekunder siden forrige bilde
        self.prev_time = now

        # 1. EMA: e_s = alpha * e + (1 - alpha) * e_s,forrige
        if self.smoothed is None:
            self.smoothed = error
        else:
            self.smoothed = self.alpha * error + (1 - self.alpha) * self.smoothed
        e = self.smoothed

        # 2. Dødsone: nær nok midten -> stå stille, og ikke bygg opp I-summen
        if abs(e) < self.deadzone:
            self.prev_error = e
            return 0.0

        # 3. PID: u = Kp*e + Ki*sum(e*dt) + Kd*(e - e_forrige)/dt
        if dt > 0:
            self.integral += e * dt
            self.integral = max(-self.i_limit, min(self.i_limit, self.integral))    # Anti-windup
            derivative = (e - self.prev_error) / dt
        else:
            derivative = 0.0    # Første måling: ingen dt å regne endring med
        self.prev_error = e

        return self.kp * e + self.ki * self.integral + self.kd * derivative


# Test: kjør "python pid.py" for å sjekke regnestykkene uten kamera
if __name__ == "__main__":
    pid = PID(kp=1.0, ki=0.0, kd=0.0, alpha=1.0, deadzone=2.0, i_limit=10.0)
    assert pid.update(1.0) == 0.0           # Innenfor dødsonen -> ingen bevegelse
    assert pid.update(5.0) == 5.0           # Bare P med Kp = 1 -> u = e

    pid = PID(kp=0.0, ki=0.0, kd=0.0, alpha=0.5, deadzone=0.0, i_limit=10.0)
    pid.update(10.0)
    pid.update(0.0)
    assert pid.smoothed == 5.0              # EMA med alpha = 0.5: halvveis mellom 10 og 0

    pid = PID(kp=0.0, ki=1.0, kd=0.0, alpha=1.0, deadzone=0.0, i_limit=10.0)
    pid.integral = 100.0
    pid.prev_time = time.time() - 1.0
    pid.update(5.0)
    assert pid.integral == 10.0             # Anti-windup holder summen på taket
    print("PID-test ok")
