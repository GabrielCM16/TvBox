#!/usr/bin/env python3
from evdev import InputDevice, list_devices, ecodes
import time

def achar_mouse():
    candidatos = []
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)

        # mouse "clássico": eventos relativos + botão esquerdo
        tem_rel = ecodes.EV_REL in caps and any(
            c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)
        )
        tem_btn = ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]

        if tem_rel:
            score = 2 if tem_btn else 1
            candidatos.append((score, dev))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[0], reverse=True)
    return candidatos[0][1]

def main():
    dev = achar_mouse()
    if not dev:
        print("[ERRO] Nenhum dispositivo de mouse (REL_X/REL_Y) encontrado em /dev/input/event*.")
        print("Valide com: ls -l /dev/input/by-id/  e  cat /proc/bus/input/devices")
        return

    print(f"[OK] Lendo: {dev.path} | {dev.name}")
    print("Movimente o dispositivo (ou o que estiver emulando mouse). Ctrl+C para sair.\n")

    x = 0
    y = 0

    try:
        for e in dev.read_loop():
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X:
                    x += e.value
                elif e.code == ecodes.REL_Y:
                    y += e.value
                print(f"dx/dy: ({e.code==ecodes.REL_X and e.value or 0:+4}, {e.code==ecodes.REL_Y and e.value or 0:+4}) | pos: ({x:6}, {y:6})")
            elif e.type == ecodes.EV_KEY and e.code == ecodes.BTN_LEFT and e.value in (0, 1):
                print(f"[CLICK] BTN_LEFT={'DOWN' if e.value==1 else 'UP'}")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
