#!/usr/bin/env python3
import time, math, curses, select
from evdev import InputDevice, list_devices, ecodes

# =========================
# MESMO TUNING (do seu código que funciona)
# =========================
DEADZONE = 3
WINDOW_MS = 60
SMOOTH = 0.35
MAX_MAG = 40.0

# Nave
SHIP_CHAR = "A"
FPS = 60.0
DT = 1.0 / FPS

BASE_STEP = 0.55   # passo base por “tick” de direção
GAIN = 1.50        # sensibilidade global

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def achar_mouse():
    best = None
    best_score = -1
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)

        tem_rel = ecodes.EV_REL in caps and any(
            c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)
        )
        if not tem_rel:
            continue

        tem_btn = ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]
        score = 2 if tem_btn else 1
        if score > best_score:
            best_score = score
            best = dev
    return best

class DirIntensityInput:
    """
    Replica o seu pipeline:
    - acumula REL_X/REL_Y
    - a cada WINDOW_MS: deadzone + smoothing
    - direção dominante (4 dirs)
    - intensidade 0..100
    """
    def __init__(self, dev: InputDevice):
        self.dev = dev
        self.acc_dx = 0
        self.acc_dy = 0
        self.last_emit = time.monotonic()
        self.sm_dx = 0.0
        self.sm_dy = 0.0
        self.dir = None
        self.intensity = 0

    def _norm_0_100(self, mag):
        mag_n = clamp(mag / MAX_MAG, 0.0, 1.0)
        return int(round(100.0 * math.sqrt(mag_n)))

    def poll(self):
        # non-blocking universal: só lê se houver dados
        while True:
            r, _, _ = select.select([self.dev.fd], [], [], 0)
            if not r:
                break
            e = self.dev.read_one()
            if e is None:
                break
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X:
                    self.acc_dx += e.value
                elif e.code == ecodes.REL_Y:
                    self.acc_dy += e.value

        now = time.monotonic()
        if (now - self.last_emit) * 1000.0 < WINDOW_MS:
            return None, 0

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0
        self.last_emit = now

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        if self.sm_dx == 0 and self.sm_dy == 0:
            self.dir, self.intensity = None, 0
            return None, 0

        if abs(self.sm_dx) >= abs(self.sm_dy):
            direcao = "RIGHT" if self.sm_dx > 0 else "LEFT"
            mag = abs(self.sm_dx)
        else:
            direcao = "DOWN" if self.sm_dy > 0 else "UP"
            mag = abs(self.sm_dy)

        intenso = self._norm_0_100(mag)
        if intenso <= 0:
            self.dir, self.intensity = None, 0
            return None, 0

        self.dir, self.intensity = direcao, intenso
        return direcao, intenso

def draw_border(stdscr, h, w):
    # borda segura (não escreve no último canto)
    for col in range(w - 1):
        stdscr.addch(1, col, "-")
        stdscr.addch(h - 2, col, "-")
    for row in range(1, h - 1):
        stdscr.addch(row, 0, "|")
        stdscr.addch(row, w - 2, "|")

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    if h < 10 or w < 30:
        stdscr.addstr(0, 0, "Terminal muito pequeno. Use >= 30x10.")
        stdscr.refresh()
        time.sleep(2)
        return

    dev = achar_mouse()
    if not dev:
        stdscr.addstr(0, 0, "Nenhum device REL_X/REL_Y encontrado. Rode com sudo.")
        stdscr.refresh()
        time.sleep(2)
        return

    inp = DirIntensityInput(dev)

    x = float(w // 2)
    y = float(h // 2)

    last = time.monotonic()
    acc = 0.0

    while True:
        now = time.monotonic()
        acc += (now - last)
        last = now

        k = stdscr.getch()
        if k in (ord('q'), ord('Q')):
            break

        # fallback teclado (setas)
        if k == curses.KEY_LEFT:  x -= 1
        if k == curses.KEY_RIGHT: x += 1
        if k == curses.KEY_UP:    y -= 1
        if k == curses.KEY_DOWN:  y += 1

        direcao, intensidade = inp.poll()

        # movimento proporcional à intensidade (0..100)
        step = BASE_STEP * GAIN * (intensidade / 25.0)

        if direcao == "LEFT":
            x -= step
        elif direcao == "RIGHT":
            x += step
        elif direcao == "UP":
            y -= step
        elif direcao == "DOWN":
            y += step

        x = clamp(x, 1, w - 3)
        y = clamp(y, 2, h - 3)

        while acc >= DT:
            acc -= DT
            stdscr.erase()
            title = f"Nave | Q sai | {dev.name[:max(0, w-15)]}"
            stdscr.addstr(0, 2, title)
            stdscr.addstr(2, 2, f"DIR={str(direcao):5} INT={intensidade:3d}  (WIN={WINDOW_MS}ms DZ={DEADZONE} SMOOTH={SMOOTH})")
            draw_border(stdscr, h, w)
            stdscr.addch(int(round(y)), int(round(x)), SHIP_CHAR)
            stdscr.refresh()

        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
