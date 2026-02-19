#!/usr/bin/env python3
import time, select, curses
from evdev import InputDevice, list_devices, ecodes

# =========================
# INPUT (gesto tipo "flap")
# =========================
DEADZONE = 1
WINDOW_MS = 30
SMOOTH = 0.55

USE_UP_SIGN = True        # comum: subir => REL_Y negativo. Se for invertido, coloque False.
MIN_SM_UP = 6.0           # intensidade mínima (bruto)
DELTA_SM_TRIGGER = 6.0    # salto mínimo (bruto)

MIN_GAP_S = 0.30          # NÃO permite flaps em menos de 0.30s
REARM_LEVEL = 2.5         # precisa cair abaixo disso para rearmar (evita duplo-flap)

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


class GestureFlap:
    """
    Detector de flap por gesto vertical (robusto):
    - trabalha no valor bruto suavizado (sm_dy)
    - usa cooldown (MIN_GAP_S) + histerese (REARM_LEVEL)
    - opcional: só considera "subida" (USE_UP_SIGN)
    """
    def __init__(self, dev: InputDevice):
        self.dev = dev

        self.acc_dx = 0
        self.acc_dy = 0
        self.sm_dx = 0.0
        self.sm_dy = 0.0

        self.last_emit = time.monotonic()
        self.last_flap_t = -1e9
        self.armed = True
        self.prev_up = 0.0

        # métricas (pra depurar se quiser exibir)
        self.up = 0.0
        self.delta_up = 0.0
        self.flap = False

    def poll(self) -> bool:
        # drena eventos disponíveis
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
            self.flap = False
            return False
        self.last_emit = now

        dx = 0 if abs(self.acc_dx) < DEADZONE else self.acc_dx
        dy = 0 if abs(self.acc_dy) < DEADZONE else self.acc_dy
        self.acc_dx = 0
        self.acc_dy = 0

        self.sm_dx = (1.0 - SMOOTH) * self.sm_dx + SMOOTH * dx
        self.sm_dy = (1.0 - SMOOTH) * self.sm_dy + SMOOTH * dy

        if USE_UP_SIGN:
            up = max(0.0, -self.sm_dy)   # só "subida"
        else:
            up = max(0.0, self.sm_dy)

        delta_up = up - self.prev_up
        self.prev_up = up

        self.up = up
        self.delta_up = delta_up

        # rearme por histerese
        if not self.armed and up <= REARM_LEVEL:
            self.armed = True

        gap_ok = (now - self.last_flap_t) >= MIN_GAP_S
        intensity_ok = up >= MIN_SM_UP
        delta_ok = delta_up >= DELTA_SM_TRIGGER

        self.flap = False
        if self.armed and gap_ok and intensity_ok and delta_ok:
            self.last_flap_t = now
            self.armed = False
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

    flap_in = GestureFlap(dev)

    top = 1
    bottom = h - 2

    def reset_game():
        return {
            "started": False,
            "alive": True,
            "bird_y": float(h // 2),
            "bird_v": 0.0,
            "score": 0,
            "pipes": [],
            "spawn_t": 0.0,
        }

    state = reset_game()

    # spawn mais variado e estável (evita depender de time.time() % range)
    rng_seed = int(time.time() * 1_000_000) & 0xFFFFFFFF

    def rng_next():
        # xorshift32 simples (determinístico e leve)
        nonlocal rng_seed
        x = rng_seed
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        rng_seed = x & 0xFFFFFFFF
        return rng_seed

    def spawn_pipe():
        min_y = top + 2
        max_y = bottom - PIPE_GAP - 2
        if max_y <= min_y:
            gy = min_y
        else:
            gy = min_y + (rng_next() % (max_y - min_y + 1))
        state["pipes"].append({"x": float(w - 2), "gap_y": int(gy), "passed": False})

    def collide_pipes(by):
        for p in state["pipes"]:
            px = int(round(p["x"]))
            # hitbox simples: só na coluna do pássaro
            if px == BIRD_X:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                if by < gy or by > gap_bot:
                    return True
        return False

    def draw():
        stdscr.erase()
        stdscr.addstr(0, 2, f"Flappy Mouse | Score: {state['score']} | R reinicia | Q sai")

        # debug discreto (não polui)
        stdscr.addstr(
            1, 2,
            f"IN up={flap_in.up:5.2f} d={flap_in.delta_up:5.2f} armed={'1' if flap_in.armed else '0'}"
        )

        for x in range(w):
            stdscr.addch(top, x, "-")
            stdscr.addch(bottom, x, "-")

        for p in state["pipes"]:
            px = int(round(p["x"]))
            if 0 <= px < w:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                for y in range(top + 1, bottom):
                    if y < gy or y > gap_bot:
                        stdscr.addch(y, px, "|")

        by = int(round(state["bird_y"]))
        by = clamp(by, top + 1, bottom - 1)
        stdscr.addch(by, BIRD_X, "@")

        if not state["started"]:
            msg = "GESTO VERTICAL (FLAP) PARA INICIAR"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)

        if not state["alive"]:
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

        if k in (ord('r'), ord('R')):
            state = reset_game()

        # input: sempre pode iniciar; durante jogo só se alive
        flap = flap_in.poll()
        if flap and not state["started"]:
            state["started"] = True

        # FIX CRÍTICO: o flap não pode "sumir" dentro do while acc>=DT.
        # Consumimos no PRIMEIRO step daquele frame, no máximo 1 flap por frame.
        flap_pending = flap

        while acc >= DT:
            acc -= DT

            if not state["started"] or not state["alive"]:
                continue

            # física do pássaro
            state["bird_v"] += GRAVITY * DT

            if flap_pending:
                state["bird_v"] = FLAP_V
                flap_pending = False

            state["bird_y"] += state["bird_v"] * DT

            # colisão com limites: teto = perde, chão = perde (flappy padrão)
            if state["bird_y"] <= top + 1:
                state["alive"] = False
                break

            if state["bird_y"] >= bottom - 1:
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

            for p in state["pipes"]:
                if not p["passed"] and p["x"] < BIRD_X:
                    p["passed"] = True
                    state["score"] += 1

            by = int(round(state["bird_y"]))
            if collide_pipes(by):
                state["alive"] = False
                break

        draw()
        time.sleep(0.001)


if __name__ == "__main__":
    curses.wrapper(main)
