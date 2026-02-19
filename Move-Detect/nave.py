#!/usr/bin/env python3
import time, curses, select
from evdev import InputDevice, list_devices, ecodes

# ===== Input tuning (mouse/controle emulando mouse) =====
DEADZONE = 1
WINDOW_MS = 15   # menor = mais responsivo
GAIN = 1.0       # sensibilidade (1.0 ~ ok)

SHIP_CHAR = "A"  # nave
FPS = 60.0
DT = 1.0 / FPS

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def achar_mouse():
    candidatos = []
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)

        tem_rel = ecodes.EV_REL in caps and any(
            c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)
        )
        tem_btn = ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]

        if tem_rel:
            candidatos.append((2 if tem_btn else 1, dev))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[0], reverse=True)
    return candidatos[0][1]

class RelMouse:
    def __init__(self, dev):
        self.dev = dev
        self.acc_dx = 0
        self.acc_dy = 0
        self.last_emit = time.monotonic()

    def poll(self):
        # drena eventos (non-blocking)
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
            return 0, 0
        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0
        return dx, dy

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    if h < 10 or w < 20:
        stdscr.addstr(0, 0, "Terminal muito pequeno. Use >= 20x10.")
        stdscr.refresh()
        time.sleep(2)
        return

    dev = achar_mouse()
    if not dev:
        stdscr.addstr(0, 0, "Nao achei mouse REL_X/REL_Y. Rode com sudo.")
        stdscr.refresh()
        time.sleep(2)
        return

    inp = RelMouse(dev)

    # posição começa no centro
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

        # também permite setas do teclado (fallback)
        if k == curses.KEY_LEFT:
            x -= 1
        elif k == curses.KEY_RIGHT:
            x += 1
        elif k == curses.KEY_UP:
            y -= 1
        elif k == curses.KEY_DOWN:
            y += 1

        dx, dy = inp.poll()
        x += dx * GAIN
        y += dy * GAIN

        x = clamp(x, 1, w - 2)
        y = clamp(y, 2, h - 2)

        # render em FPS fixo
        while acc >= DT:
            acc -= DT
            stdscr.erase()
            stdscr.addstr(0, 2, f"Nave (mouse REL) | Q sai | dx={dx:+4} dy={dy:+4}")
            # borda
            for col in range(w):
                stdscr.addch(1, col, "-")
                stdscr.addch(h - 1, col, "-")
            for row in range(1, h):
                stdscr.addch(row, 0, "|")
                stdscr.addch(row, w - 1, "|")

            stdscr.addch(int(round(y)), int(round(x)), SHIP_CHAR)
            stdscr.refresh()

        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
