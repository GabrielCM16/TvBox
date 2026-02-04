#!/usr/bin/env python3
import time, math, curses, select
from evdev import InputDevice, list_devices, ecodes

# INPUT tuning
DEADZONE = 3
WINDOW_MS = 55
SMOOTH = 0.20
MAX_MAG = 40.0

MIN_INT = 20
DELTA_TRIGGER = 18
COOLDOWN_MS = 180

# GAME tuning
FPS = 30.0
DT = 1.0 / FPS
GRAVITY = 26.0
FLAP_V = -10.5
PIPE_SPEED = 18.0
PIPE_GAP = 7
PIPE_SPAWN = 1.35
BIRD_X = 10

def clamp(v, a, b): return a if v < a else b if v > b else v

def achar_mouse():
    best = None
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)
        if ecodes.EV_REL in caps and any(c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)):
            best = dev
            break
    return best

def norm_0_100(mag):
    mag_n = max(0.0, min(1.0, mag / MAX_MAG))
    return int(round(100.0 * math.sqrt(mag_n)))

class EdgeFlap:
    def __init__(self, dev):
        self.dev = dev
        self.dev.set_nonblocking(True)
        self.acc_dx = 0
        self.acc_dy = 0
        self.sm_dx = 0.0
        self.sm_dy = 0.0
        self.last_emit = time.monotonic()
        self.prev_vert = 0
        self.last_fire = 0.0

        self.any_int = 0
        self.vert_int = 0
        self.delta = 0
        self.flap = False

    def poll(self):
        # drain
        while True:
            r, _, _ = select.select([self.dev.fd], [], [], 0)
            if not r:
                break
            e = self.dev.read_one()
            if e is None:
                break
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X: self.acc_dx += e.value
                elif e.code == ecodes.REL_Y: self.acc_dy += e.value

        now = time.monotonic()
        if (now - self.last_emit) * 1000.0 < WINDOW_MS:
            self.flap = False
            return self.flap

        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        self.vert_int = norm_0_100(abs(self.sm_dy))
        self.any_int  = norm_0_100(math.hypot(self.sm_dx, self.sm_dy))

        self.delta = self.vert_int - self.prev_vert
        self.prev_vert = self.vert_int

        self.flap = False
        if self.vert_int >= MIN_INT and self.delta >= DELTA_TRIGGER:
            if (now - self.last_fire) * 1000.0 >= COOLDOWN_MS:
                self.last_fire = now
                self.flap = True

        return self.flap

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    if h < 18 or w < 50:
        stdscr.addstr(0, 0, "Terminal muito pequeno. Use >= 50x18.")
        stdscr.refresh()
        time.sleep(2)
        return

    dev = achar_mouse()
    if not dev:
        stdscr.addstr(0, 0, "Nao achei mouse REL_X/REL_Y. Rode com sudo.")
        stdscr.refresh()
        time.sleep(2)
        return

    edge = EdgeFlap(dev)

    # start screen (manual enter) removida: começa ao detectar flap
    started = False

    top = 1
    bottom = h - 2

    bird_y = float(h // 2)
    bird_v = 0.0
    score = 0
    alive = True

    pipes = []
    spawn_t = 0.0

    def spawn_pipe():
        min_y = top + 2
        max_y = bottom - PIPE_GAP - 2
        if max_y <= min_y:
            gy = min_y
        else:
            gy = min_y + int((time.time() * 1000) % (max_y - min_y + 1))
        pipes.append({"x": float(w - 2), "gap_y": gy, "passed": False})

    def collide_pipes(by):
        for p in pipes:
            px = int(round(p["x"]))
            if px == BIRD_X:
                gy = p["gap_y"]
                if by < gy or by > gy + PIPE_GAP:
                    return True
        return False

    def draw():
        stdscr.erase()
        stdscr.addstr(0, 2, f"Flappy Mouse | Score: {score} | Q sai")
        stdscr.addstr(1, 2, f"DBG any={edge.any_int:3d} vert={edge.vert_int:3d} delta={edge.delta:4d} flap={'1' if edge.flap else '0'}")
        stdscr.addstr(2, 2, f"TUNE MIN_INT={MIN_INT} DELTA_TRIGGER={DELTA_TRIGGER} COOLDOWN={COOLDOWN_MS}ms")

        for x in range(w):
            stdscr.addch(top, x, "-")
            stdscr.addch(bottom, x, "-")

        for p in pipes:
            px = int(round(p["x"]))
            if 0 <= px < w:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                for y in range(top + 1, bottom):
                    if y < gy or y > gap_bot:
                        stdscr.addch(y, px, "|")

        by = int(round(bird_y))
        by = clamp(by, top + 1, bottom - 1)
        stdscr.addch(by, BIRD_X, "@")

        if not started:
            msg = "FAÇA UM GESTO VERTICAL FORTE PARA INICIAR"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        if not alive:
            msg = "GAME OVER - R reinicia | Q sai"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        stdscr.refresh()

    last = time.monotonic()
    acc = 0.0

    while True:
        now = time.monotonic()
        frame = now - last
        last = now
        acc += frame

        k = stdscr.getch()
        if k in (ord('q'), ord('Q')):
            break

        if not alive and k in (ord('r'), ord('R')):
            bird_y = float(h // 2)
            bird_v = 0.0
            score = 0
            pipes.clear()
            spawn_t = 0.0
            alive = True
            started = False

        flap = False
        if alive:
            flap = edge.poll()
            if flap and not started:
                started = True

        while acc >= DT:
            acc -= DT

            if not started or not alive:
                continue

            bird_v += GRAVITY * DT
            if flap:
                bird_v = FLAP_V
                flap = False
            bird_y += bird_v * DT

            # não perde no chão: trava
            if bird_y >= bottom - 1:
                bird_y = float(bottom - 1)
                if bird_v > 0:
                    bird_v = 0.0

            # perde no teto
            if bird_y <= top + 1:
                alive = False
                break

            spawn_t += DT
            if spawn_t >= PIPE_SPAWN:
                spawn_t = 0.0
                spawn_pipe()

            for p in pipes:
                p["x"] -= PIPE_SPEED * DT

            while pipes and pipes[0]["x"] < 0:
                pipes.pop(0)

            for p in pipes:
                if not p["passed"] and p["x"] < BIRD_X:
                    p["passed"] = True
                    score += 1

            by = int(round(bird_y))
            if collide_pipes(by):
                alive = False
                break

        draw()
        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
