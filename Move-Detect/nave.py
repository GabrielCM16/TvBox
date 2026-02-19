#!/usr/bin/env python3
import time, curses, select
from evdev import InputDevice, list_devices, ecodes

DEADZONE = 1
WINDOW_MS = 15
GAIN = 1.0
SHIP_CHAR = "A"
FPS = 60.0
DT = 1.0 / FPS

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def achar_mouse():
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)
        if ecodes.EV_REL in caps:
            return dev
    return None

class RelMouse:
    def __init__(self, dev):
        self.dev = dev
        self.dx = 0
        self.dy = 0
        self.last = time.monotonic()

    def poll(self):
        while True:
            r,_,_ = select.select([self.dev.fd], [], [], 0)
            if not r:
                break
            e = self.dev.read_one()
            if not e: break
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X: self.dx += e.value
                if e.code == ecodes.REL_Y: self.dy += e.value

        now = time.monotonic()
        if (now-self.last)*1000 < WINDOW_MS:
            return 0,0
        self.last = now

        dx = 0 if abs(self.dx)<DEADZONE else self.dx
        dy = 0 if abs(self.dy)<DEADZONE else self.dy
        self.dx = self.dy = 0
        return dx,dy

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    h,w = stdscr.getmaxyx()
    dev = achar_mouse()
    if not dev:
        stdscr.addstr(0,0,"Sem mouse REL. Rode com sudo.")
        stdscr.getch()
        return

    inp = RelMouse(dev)

    x = float(w//2)
    y = float(h//2)

    last=time.monotonic()
    acc=0.0

    while True:
        now=time.monotonic()
        acc += now-last
        last=now

        k=stdscr.getch()
        if k in (ord('q'),ord('Q')): break

        dx,dy = inp.poll()
        x += dx*GAIN
        y += dy*GAIN

        x = clamp(x,1,w-3)
        y = clamp(y,2,h-3)

        while acc>=DT:
            acc-=DT
            stdscr.erase()

            stdscr.addstr(0,2,"Mover nave | Q sai")

            # borda segura
            for col in range(w-1):
                stdscr.addch(1,col,"-")
                stdscr.addch(h-2,col,"-")
            for row in range(1,h-1):
                stdscr.addch(row,0,"|")
                stdscr.addch(row,w-2,"|")

            stdscr.addch(int(y),int(x),SHIP_CHAR)
            stdscr.refresh()

        time.sleep(0.001)

if __name__=="__main__":
    curses.wrapper(main)
