#!/usr/bin/env python3
import time, math, curses
from evdev import InputDevice, list_devices, ecodes

# =========================
# MESMO TUNING DO SEU CÓDIGO (funciona)
# =========================
DEADZONE = 3
WINDOW_MS = 60
SMOOTH = 0.35
MAX_MAG = 40.0

# Nave
FPS = 60.0
DT = 1.0 / FPS
SHIP_CHAR = "A"
BASE_STEP = 0.35   # escala de movimento por tick
GAIN = 1.35        # sensibilidade global (ajuste fino)

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
    Replica 1:1 o seu comportamento:
    - acumula REL_X/REL_Y
    - a cada WINDOW_MS: deadzone + smoothing
    - escolhe direção dominante (UP/DOWN/LEFT/RIGHT)
    - devolve intensidade 0..100
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

import select

def poll(self):
    # só tenta ler se houver dados (non-blocking universal)
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


def draw_border(stdscr, h, w):
    # borda segura (evita addch no último canto)
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

        direcao, intensidade = inp.poll()

        # move proporcional à intensidade (0..100)
        step = BASE_STEP * GAIN * (intensidade / 25.0)  # 25 => referência (ajuste fino)

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
            stdscr.addstr(0, 2, f"Nave | Q sai | Device: {dev.name[:(w-20)]}")
            stdscr.addstr(2, 2, f"DIR={str(direcao):5} INT={intensidade:3d}  (DEADZONE={DEADZONE} WIN={WINDOW_MS}ms SMOOTH={SMOOTH})")
            draw_border(stdscr, h, w)
            stdscr.addch(int(round(y)), int(round(x)), SHIP_CHAR)
            stdscr.refresh()

        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
