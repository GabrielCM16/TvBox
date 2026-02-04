#!/usr/bin/env python3
# Flappy Bird (terminal) controlado por "gesto" UP do mouse (/dev/input/event*)
# - Extremamente simples
# - Suave (FPS fixo)
# - Deadzone + trigger + cooldown (não fica “contando a volta”)

import time
import math
import curses
from evdev import InputDevice, list_devices, ecodes
import select

# =========================
# INPUT (mouse gesture)
# =========================
DEADZONE = 3
WINDOW_MS = 55
SMOOTH = 0.35
MAX_MAG = 40.0

TRIGGER_UP = 22       # intensidade 0..100 para "flap"
RELEASE_UP = 10       # histerese (libera o trigger quando cair abaixo disso)
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

class GestureUp:
    def __init__(self, dev: InputDevice | None):
        self.dev = dev
        self.acc_dx = 0
        self.acc_dy = 0
        self.sm_dx = 0.0
        self.sm_dy = 0.0
        self.last_emit = time.monotonic()
        self.last_fire = 0.0
        self.armed = True  # histerese

        if self.dev:
            try:
                self.dev.set_nonblocking(True)
            except Exception:
                pass

    def _norm_0_100(self, mag: float) -> int:
        mag_n = max(0.0, min(1.0, mag / MAX_MAG))
        return int(round(100.0 * math.sqrt(mag_n)))  # curva “bonita” p/ movimentos pequenos

    def poll_flap(self) -> bool:
        # lê eventos disponíveis sem travar
        if self.dev:
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

        now = time.monotonic()
        if (now - self.last_emit) * 1000.0 < WINDOW_MS:
            return False
        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        # mouse: dy negativo normalmente significa "subiu"
        if self.sm_dy >= 0:
            # se está descendo ou neutro, rearma quando estiver fraco
            if abs(self.sm_dy) < 1:
                self.armed = True
            return False

        up_mag = abs(self.sm_dy)
        intensidade = self._norm_0_100(up_mag)

        # histerese: só rearma quando cair abaixo de RELEASE_UP
        if intensidade <= RELEASE_UP:
            self.armed = True

        if (not self.armed) or (intensidade < TRIGGER_UP):
            return False

        # cooldown
        if (now - self.last_fire) * 1000.0 < COOLDOWN_MS:
            return False

        self.last_fire = now
        self.armed = False
        return True

# =========================
# GAME
# =========================
FPS = 30.0
DT = 1.0 / FPS

GRAVITY = 26.0      # quanto cai por segundo^2
FLAP_V = -10.5      # impulso pra cima
PIPE_SPEED = 18.0   # colunas por segundo
PIPE_GAP = 7        # vão vertical
PIPE_SPAWN = 1.35   # segundos

BIRD_X = 10

def clamp(v, a, b): return a if v < a else b if v > b else v

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    # margens mínimas
    if h < 18 or w < 50:
        stdscr.addstr(0, 0, "Terminal muito pequeno. Use algo >= 50x18.")
        stdscr.refresh()
        time.sleep(2)
        return

    # tenta achar mouse
    dev = achar_mouse()
    gest = GestureUp(dev)

    # estado inicial
    bird_y = h // 2
    bird_v = 0.0
    score = 0
    alive = True

    pipes = []  # cada pipe: dict(x, gap_y, passed)
    spawn_t = 0.0

    # chão e teto
    top = 1
    bottom = h - 2

    def spawn_pipe():
        # gap_y = topo do vão
        # garante espaço
        min_y = top + 2
        max_y = bottom - PIPE_GAP - 2
        if max_y <= min_y:
            gy = min_y
        else:
            # pseudo-rand sem import random (rápido)
            gy = min_y + int((time.time() * 1000) % (max_y - min_y + 1))
        pipes.append({"x": float(w - 2), "gap_y": gy, "passed": False})

    def draw():
        stdscr.erase()

        # HUD
        ctrl = "mouse(UP)" if dev else "teclado(SPACE)"
        stdscr.addstr(0, 2, f"Flappy Terminal | Score: {score} | Ctrl: {ctrl} | Q sai")

        # bordas
        for x in range(w):
            stdscr.addch(top, x, "-")
            stdscr.addch(bottom, x, "-")

        # pipes
        for p in pipes:
            px = int(round(p["x"]))
            if 0 <= px < w:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                for y in range(top + 1, bottom):
                    if y < gy or y > gap_bot:
                        stdscr.addch(y, px, "|")

        # bird
        by = int(round(bird_y))
        by = clamp(by, top + 1, bottom - 1)
        stdscr.addch(by, BIRD_X, "@")

        if not alive:
            msg = "GAME OVER - R para reiniciar | Q para sair"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        stdscr.refresh()

    def collide() -> bool:
        by = int(round(bird_y))
        if by <= top or by >= bottom:
            return True
        for p in pipes:
            px = int(round(p["x"]))
            if px == BIRD_X:
                gy = p["gap_y"]
                if by < gy or by > gy + PIPE_GAP:
                    return True
        return False

    last = time.monotonic()
    acc = 0.0

    # loop
    while True:
        now = time.monotonic()
        frame = now - last
        last = now
        acc += frame

        # input (sempre)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break

        flap = False
        if alive:
            # mouse gesture tem prioridade; teclado é fallback
            if gest.poll_flap():
                flap = True
            elif key in (ord(" "),):  # SPACE
                flap = True

        if not alive:
            if key in (ord("r"), ord("R")):
                bird_y = h // 2
                bird_v = 0.0
                score = 0
                pipes.clear()
                spawn_t = 0.0
                alive = True

        # simulação em passos fixos (evita travar)
        while acc >= DT:
            acc -= DT

            if alive:
                # física
                bird_v += GRAVITY * DT
                if flap:
                    bird_v = FLAP_V
                    flap = False
                bird_y += bird_v * DT

                # spawn pipes
                spawn_t += DT
                if spawn_t >= PIPE_SPAWN:
                    spawn_t = 0.0
                    spawn_pipe()

                # move pipes
                for p in pipes:
                    p["x"] -= PIPE_SPEED * DT

                # remove pipes fora
                while pipes and pipes[0]["x"] < 0:
                    pipes.pop(0)

                # score (passou do bird)
                for p in pipes:
                    if not p["passed"] and p["x"] < BIRD_X:
                        p["passed"] = True
                        score += 1

                # colisão
                if collide():
                    alive = False

        draw()
        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
