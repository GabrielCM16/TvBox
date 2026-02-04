#!/usr/bin/env python3
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

TRIGGER_UP = 22       # flap (UP)
RELEASE_UP = 10
COOLDOWN_MS = 160

START_TRIGGER = 8     # qualquer movimento acima disso inicia o jogo (0..100)

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

class Gesture:
    def __init__(self, dev):
        self.dev = dev
        self.acc_dx = 0
        self.acc_dy = 0
        self.sm_dx = 0.0
        self.sm_dy = 0.0
        self.last_emit = time.monotonic()
        self.last_fire = 0.0
        self.armed = True

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
        Retorna (moved_intensity, flap_bool)
        - moved_intensity: 0..100 (movimento geral, qualquer direção) por janela
        - flap_bool: True quando detectar UP acima do limiar com cooldown
        """
        self._drain()

        now = time.monotonic()
        if (now - self.last_emit) * 1000.0 < WINDOW_MS:
            return 0, False
        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        # intensidade geral (qualquer direção)
        mag_any = math.sqrt(self.sm_dx * self.sm_dx + self.sm_dy * self.sm_dy)
        moved_int = self._norm_0_100(mag_any)

        # flap = UP (dy negativo geralmente é "subiu")
        flap = False
        if self.sm_dy < 0:
            up_mag = abs(self.sm_dy)
            up_int = self._norm_0_100(up_mag)

            if up_int <= RELEASE_UP:
                self.armed = True

            if self.armed and up_int >= TRIGGER_UP:
                if (now - self.last_fire) * 1000.0 >= COOLDOWN_MS:
                    self.last_fire = now
                    self.armed = False
                    flap = True
        else:
            # rearma quando estabilizar
            if abs(self.sm_dy) < 1:
                self.armed = True

        return moved_int, flap

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
    gest = Gesture(dev)

    # chão e teto
    top = 1
    bottom = h - 2

    def reset():
        return {
            "bird_y": float(h // 2),
            "bird_v": 0.0,
            "score": 0,
            "alive": True,
            "pipes": [],
            "spawn_t": 0.0,
            "started": False,   # << inicia só após movimento
        }

    state = reset()

    def spawn_pipe():
        min_y = top + 2
        max_y = bottom - PIPE_GAP - 2
        if max_y <= min_y:
            gy = min_y
        else:
            gy = min_y + int((time.time() * 1000) % (max_y - min_y + 1))
        state["pipes"].append({"x": float(w - 2), "gap_y": gy, "passed": False})

    def draw():
        stdscr.erase()

        ctrl = "mouse" if dev else "teclado"
        stdscr.addstr(0, 2, f"Flappy Terminal | Score: {state['score']} | Ctrl: {ctrl} | Q sai")

        # bordas
        for x in range(w):
            stdscr.addch(top, x, "-")
            stdscr.addch(bottom, x, "-")

        # pipes
        for p in state["pipes"]:
            px = int(round(p["x"]))
            if 0 <= px < w:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                for y in range(top + 1, bottom):
                    if y < gy or y > gap_bot:
                        stdscr.addch(y, px, "|")

        # bird
        by = int(round(state["bird_y"]))
        by = clamp(by, top + 1, bottom - 1)
        stdscr.addch(by, BIRD_X, "@")

        if not state["started"] and state["alive"]:
            msg = "MOVA o mouse (ou SPACE) para INICIAR"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        if not state["alive"]:
            msg = "GAME OVER - R reinicia | Q sai"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        stdscr.refresh()

    def collide_pipes():
        by = int(round(state["bird_y"]))
        for p in state["pipes"]:
            px = int(round(p["x"]))
            if px == BIRD_X:
                gy = p["gap_y"]
                if by < gy or by > gy + PIPE_GAP:
                    return True
        return False

    last = time.monotonic()
    acc = 0.0

    while True:
        now = time.monotonic()
        frame = now - last
        last = now
        acc += frame

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break

        if not state["alive"]:
            if key in (ord("r"), ord("R")):
                state = reset()
            draw()
            time.sleep(0.01)
            continue

        moved_int, flap_mouse = gest.poll()
        flap_key = (key == ord(" "))

        # START gate: qualquer movimento inicia (ou SPACE)
        if (not state["started"]) and (moved_int >= START_TRIGGER or flap_key or flap_mouse):
            state["started"] = True
            # se iniciou com flap, aplica já
            if flap_key or flap_mouse:
                state["bird_v"] = FLAP_V

        # se não começou ainda: pássaro fica parado
        if not state["started"]:
            draw()
            time.sleep(0.01)
            continue

        # flap normal (após começar)
        flap = flap_mouse or flap_key

        # simulação em passos fixos
        while acc >= DT:
            acc -= DT

            # física
            state["bird_v"] += GRAVITY * DT
            if flap:
                state["bird_v"] = FLAP_V
                flap = False
            state["bird_y"] += state["bird_v"] * DT

            # NÃO PERDE NO CHÃO: trava no chão e zera velocidade
            if state["bird_y"] >= bottom - 1:
                state["bird_y"] = float(bottom - 1)
                if state["bird_v"] > 0:
                    state["bird_v"] = 0.0

            # opcional: perde no teto (mantive)
            if state["bird_y"] <= top + 1:
                state["alive"] = False
                break

            # pipes
            state["spawn_t"] += DT
            if state["spawn_t"] >= PIPE_SPAWN:
                state["spawn_t"] = 0.0
                spawn_pipe()

            for p in state["pipes"]:
                p["x"] -= PIPE_SPEED * DT

            while state["pipes"] and state["pipes"][0]["x"] < 0:
                state["pipes"].pop(0)

            # score
            for p in state["pipes"]:
                if not p["passed"] and p["x"] < BIRD_X:
                    p["passed"] = True
                    state["score"] += 1

            # colisão com cano
            if collide_pipes():
                state["alive"] = False
                break

        draw()
        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
