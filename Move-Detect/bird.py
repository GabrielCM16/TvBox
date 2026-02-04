#!/usr/bin/env python3
import time
import math
import curses
from evdev import InputDevice, list_devices, ecodes
import select

# =========================
# INPUT (mouse)
# =========================
DEADZONE = 3
WINDOW_MS = 55
SMOOTH = 0.35
MAX_MAG = 40.0

TRIGGER_UP = 22
RELEASE_UP = 10
COOLDOWN_MS = 160

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

class MouseGesture:
    def __init__(self, dev):
        self.dev = dev
        self.acc_dx = 0
        self.acc_dy = 0
        self.sm_dx = 0.0
        self.sm_dy = 0.0
        self.last_emit = time.monotonic()

        self.last_fire = 0.0
        self.armed = True

        # últimos valores publicados (para diagnóstico)
        self.last_any = 0
        self.last_up = 0

        if self.dev:
            try:
                self.dev.set_nonblocking(True)
            except Exception:
                pass

    def _norm_0_100(self, mag):
        mag_n = max(0.0, min(1.0, mag / MAX_MAG))
        return int(round(100.0 * math.sqrt(mag_n)))

    def _drain(self):
        if not self.dev:
            return
        while True:
            r, _, _ = select.select([self.dev.fd], [], [], 0)
            if not r:
                break
            try:
                e = self.dev.read_one()
            except BlockingIOError:
                break
            if e is None:
                break
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X:
                    self.acc_dx += e.value
                elif e.code == ecodes.REL_Y:
                    self.acc_dy += e.value

    def poll(self):
        """
        Retorna dict:
        {
          any_int: 0..100,
          up_int: 0..100,
          sm_dx, sm_dy: float,
          flap: bool
        }
        """
        self._drain()

        now = time.monotonic()
        if (now - self.last_emit) * 1000.0 < WINDOW_MS:
            return {
                "any_int": self.last_any,
                "up_int": self.last_up,
                "sm_dx": self.sm_dx,
                "sm_dy": self.sm_dy,
                "flap": False,
            }
        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        mag_any = math.sqrt(self.sm_dx * self.sm_dx + self.sm_dy * self.sm_dy)
        any_int = self._norm_0_100(mag_any)

        up_int = 0
        flap = False

        # dy negativo normalmente = "subiu"
        if self.sm_dy < 0:
            up_int = self._norm_0_100(abs(self.sm_dy))

            if up_int <= RELEASE_UP:
                self.armed = True

            if self.armed and up_int >= TRIGGER_UP:
                if (now - self.last_fire) * 1000.0 >= COOLDOWN_MS:
                    self.last_fire = now
                    self.armed = False
                    flap = True
        else:
            if abs(self.sm_dy) < 1:
                self.armed = True

        self.last_any = any_int
        self.last_up = up_int

        return {
            "any_int": any_int,
            "up_int": up_int,
            "sm_dx": self.sm_dx,
            "sm_dy": self.sm_dy,
            "flap": flap,
        }

# =========================
# GAME
# =========================
FPS = 30.0
DT = 1.0 / FPS

GRAVITY = 26.0
FLAP_V = -10.5
PIPE_SPEED = 18.0
PIPE_GAP = 7
PIPE_SPAWN = 1.35

BIRD_X = 10

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def diag_screen(stdscr, dev, gest):
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()

    while True:
        stdscr.erase()
        stdscr.addstr(0, 2, "DIAGNOSTICO DO MOUSE (antes do jogo)")
        stdscr.addstr(1, 2, "ENTER inicia | Q sai | SPACE tambem vai pular no jogo")
        stdscr.addstr(2, 2, "-" * (w - 4))

        if dev:
            stdscr.addstr(4, 2, f"Device: {dev.path}")
            stdscr.addstr(5, 2, f"Nome:   {dev.name}")
        else:
            stdscr.addstr(4, 2, "Device: [NAO ENCONTRADO]")
            stdscr.addstr(5, 2, "Dica: rode com sudo e/ou conecte o dispositivo que emula mouse")

        info = gest.poll() if gest else {"any_int": 0, "up_int": 0, "sm_dx": 0.0, "sm_dy": 0.0, "flap": False}

        stdscr.addstr(7, 2, f"any_int (0..100): {info['any_int']:3d}   (movimento geral)")
        stdscr.addstr(8, 2, f"up_int  (0..100): {info['up_int']:3d}   (movimento UP)")
        stdscr.addstr(10, 2, f"sm_dx: {info['sm_dx']:+8.2f}   sm_dy: {info['sm_dy']:+8.2f}")
        stdscr.addstr(12, 2, f"flap detectado: {'SIM' if info['flap'] else 'nao'}")

        stdscr.addstr(14, 2, "Ajustes relevantes:")
        stdscr.addstr(15, 4, f"DEADZONE={DEADZONE}  TRIGGER_UP={TRIGGER_UP}  COOLDOWN_MS={COOLDOWN_MS}  MAX_MAG={MAX_MAG}")

        stdscr.refresh()

        k = stdscr.getch()
        if k in (ord('q'), ord('Q')):
            return False
        if k in (10, 13):  # ENTER (LF/CR)
            return True

        time.sleep(0.01)

def main(stdscr):
    curses.curs_set(0)

    h, w = stdscr.getmaxyx()
    if h < 18 or w < 50:
        stdscr.addstr(0, 0, "Terminal muito pequeno. Use >= 50x18.")
        stdscr.refresh()
        time.sleep(2)
        return

    dev = achar_mouse()
    gest = MouseGesture(dev) if dev else None

    # 1) DIAGNÓSTICO
    ok = diag_screen(stdscr, dev, gest)
    if not ok:
        return

    # 2) JOGO
    stdscr.nodelay(True)
    stdscr.keypad(True)

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
        ctrl = "mouse(UP)+SPACE" if dev else "SPACE"
        stdscr.addstr(0, 2, f"Flappy Terminal | Score: {score} | Ctrl: {ctrl} | Q sai")

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

        flap = False
        if alive:
            if gest and gest.poll()["flap"]:
                flap = True
            if k == ord(' '):  # SPACE
                flap = True
        else:
            if k in (ord('r'), ord('R')):
                bird_y = float(h // 2)
                bird_v = 0.0
                score = 0
                pipes.clear()
                spawn_t = 0.0
                alive = True

        while acc >= DT:
            acc -= DT

            if alive:
                bird_v += GRAVITY * DT
                if flap:
                    bird_v = FLAP_V
                    flap = False
                bird_y += bird_v * DT

                # NÃO PERDE NO CHÃO: trava no chão
                if bird_y >= bottom - 1:
                    bird_y = float(bottom - 1)
                    if bird_v > 0:
                        bird_v = 0.0

                # perde no teto (mantido)
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
