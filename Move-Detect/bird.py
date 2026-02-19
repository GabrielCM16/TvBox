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
    - valor bruto suavizado (sm_dy)
    - cooldown (MIN_GAP_S) + histerese (REARM_LEVEL)
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

        # métricas p/ HUD
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
            up = max(0.0, -self.sm_dy)  # só "subida"
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

    # RNG leve p/ pipes (xorshift32)
    rng_seed = int(time.time() * 1_000_000) & 0xFFFFFFFF
    def rng_next():
        nonlocal rng_seed
        x = rng_seed
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        rng_seed = x & 0xFFFFFFFF
        return rng_seed

    def reset_game():
        return {
            "bird_y": float(h // 2),
            "bird_v": 0.0,
            "score": 0,
            "pipes": [],
            "spawn_t": 0.0,
            "alive": True,
        }

    def spawn_pipe(state):
        min_y = top + 2
        max_y = bottom - PIPE_GAP - 2
        if max_y <= min_y:
            gy = min_y
        else:
            gy = min_y + (rng_next() % (max_y - min_y + 1))
        state["pipes"].append({"x": float(w - 2), "gap_y": int(gy), "passed": False})

    def collide_pipes(state, by):
        for p in state["pipes"]:
            px = int(round(p["x"]))
            if px == BIRD_X:
                gy = p["gap_y"]
                gap_bot = gy + PIPE_GAP
                if by < gy or by > gap_bot:
                    return True
        return False

    def draw_frame(title, state, show_pipes):
        stdscr.erase()
        stdscr.addstr(0, 2, title)

        # HUD de input (sem prints no terminal)
        stdscr.addstr(
            1, 2,
            f"IN up={flap_in.up:5.2f} d={flap_in.delta_up:5.2f} armed={'1' if flap_in.armed else '0'}"
        )

        for x in range(w):
            stdscr.addch(top, x, "-")
            stdscr.addch(bottom, x, "-")

        if show_pipes:
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

        stdscr.refresh()

    # =========================
    # MENU / TREINO (sandbox)
    # =========================
    menu_state = reset_game()
    last = time.monotonic()
    acc = 0.0
    last_flap_flash = 0.0  # pra mostrar "FLAP!" por pouco tempo

    while True:
        now = time.monotonic()
        acc += (now - last)
        last = now

        k = stdscr.getch()
        if k in (ord('q'), ord('Q')):
            return

        # qualquer tecla inicia o jogo (inclusive Enter, espaço etc.)
        if k != -1:
            break

        flap = flap_in.poll()
        if flap:
            menu_state["bird_v"] = FLAP_V
            last_flap_flash = now

        while acc >= DT:
            acc -= DT

            # física do treino
            menu_state["bird_v"] += GRAVITY * DT
            menu_state["bird_y"] += menu_state["bird_v"] * DT

            # chão: NÃO perde, trava (pedido do usuário)
            if menu_state["bird_y"] >= bottom - 1:
                menu_state["bird_y"] = float(bottom - 1)
                if menu_state["bird_v"] > 0:
                    menu_state["bird_v"] = 0.0

            # teto: opcionalmente não perde no menu também; só trava
            if menu_state["bird_y"] <= top + 1:
                menu_state["bird_y"] = float(top + 1)
                if menu_state["bird_v"] < 0:
                    menu_state["bird_v"] = 0.0

        title = "MENU/TREINO | Faça flaps à vontade | Pressione QUALQUER TECLA para iniciar | Q sai"
        draw_frame(title, menu_state, show_pipes=False)

        # banner discreto de FLAP
        if (now - last_flap_flash) <= 0.25:
            msg = "FLAP!"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
            stdscr.refresh()

        time.sleep(0.001)

    # =========================
    # JOGO
    # =========================
    game_state = reset_game()
    acc = 0.0
    last = time.monotonic()

    while True:
        now = time.monotonic()
        acc += (now - last)
        last = now

        k = stdscr.getch()
        if k in (ord('q'), ord('Q')):
            break
        if (not game_state["alive"]) and k in (ord('r'), ord('R')):
            game_state = reset_game()

        flap = False
        if game_state["alive"]:
            flap = flap_in.poll()

        flap_pending = flap  # consome no máximo 1 flap por frame

        while acc >= DT:
            acc -= DT

            if not game_state["alive"]:
                continue

            # física
            game_state["bird_v"] += GRAVITY * DT
            if flap_pending:
                game_state["bird_v"] = FLAP_V
                flap_pending = False
            game_state["bird_y"] += game_state["bird_v"] * DT

            # chão: NÃO perde (pedido), trava
            if game_state["bird_y"] >= bottom - 1:
                game_state["bird_y"] = float(bottom - 1)
                if game_state["bird_v"] > 0:
                    game_state["bird_v"] = 0.0

            # teto: perde (mantém desafio; se quiser travar também, eu troco em 2 linhas)
            if game_state["bird_y"] <= top + 1:
                game_state["alive"] = False
                break

            # pipes
            game_state["spawn_t"] += DT
            if game_state["spawn_t"] >= PIPE_SPAWN:
                game_state["spawn_t"] = 0.0
                spawn_pipe(game_state)

            for p in game_state["pipes"]:
                p["x"] -= PIPE_SPEED * DT

            while game_state["pipes"] and game_state["pipes"][0]["x"] < 0:
                game_state["pipes"].pop(0)

            for p in game_state["pipes"]:
                if not p["passed"] and p["x"] < BIRD_X:
                    p["passed"] = True
                    game_state["score"] += 1

            by = int(round(game_state["bird_y"]))
            if collide_pipes(game_state, by):
                game_state["alive"] = False
                break

        title = f"JOGO | Score: {game_state['score']} | R reinicia | Q sai"
        draw_frame(title, game_state, show_pipes=True)

        if not game_state["alive"]:
            msg = "GAME OVER (teto/canos) | R reinicia | Q sai"
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
            stdscr.refresh()

        time.sleep(0.001)

if __name__ == "__main__":
    curses.wrapper(main)
