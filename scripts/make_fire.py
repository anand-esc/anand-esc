#!/usr/bin/env python3
"""Generate assets/fire.svg: a looping ASCII fire with a name smouldering in it.

The simulation follows the "wall of fire" look of the ASCII Art Archive fire
animation: a heat field that diffuses upward and cools, flame tongues that
flare from the base, drifting embers (*) and sparks (').

Usage: python3 scripts/make_fire.py [NAME] [SEED]
"""
import math
import random
import sys
from pathlib import Path

NAME = sys.argv[1].upper() if len(sys.argv) > 1 else "SURYANSH"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 11

ROWS = 26
FRAMES, FPS, WARMUP = 36, 12, 120
NAME_TOP = 8                      # row where the name starts
CW, RH, FS = 8.4, 16, 14          # cell width, row height, font size

INTENSITY, DECAY, TURBULENCE = 5.0, 1.0, 5.0
CHARS = " .:-=+*#%@"
# colour per heat level 0-9 -> palette slot
SLOT = [None, 0, 0, 1, 1, 2, 2, 3, 3, 4]
DARK = ["#4a170a", "#7a230a", "#c4521a", "#f49922", "#fff1c9"]
LIGHT = ["#f0d6c6", "#e9b08c", "#de7a2e", "#bf420d", "#7c2d12"]
NAME_DARK, NAME_LIGHT = "#fff1c9", "#5a1e0c"

FONT = {
    "A": [".###.", "#...#", "#####", "#...#", "#...#"],
    "B": ["####.", "#...#", "####.", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#...."],
    "G": [".####", "#....", "#..##", "#...#", ".####"],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "....#", "....#", "#...#", ".###."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "Z": ["#####", "...#.", "..#..", ".#...", "#####"],
    " ": ["....."] * 5,
}

name_w = len(NAME) * 5 + (len(NAME) - 1) * 2
COLS = max(88, name_w + 20)
x0 = (COLS - name_w) // 2
mask = set()
for i, ch in enumerate(NAME):
    for r, line in enumerate(FONT.get(ch, FONT[" "])):
        for c, v in enumerate(line):
            if v == "#":
                mask.add((NAME_TOP + r, x0 + i * 7 + c))

rng = random.Random(SEED)
R = rng.random
heat = [[0.0] * COLS for _ in range(ROWS)]

# smooth static noise that scrolls through the cooling term
noise = [[0.3 * R() for _ in range(COLS)] for _ in range(ROWS)]
for _ in range(2):
    noise = [[sum(noise[yy][xx]
                  for yy in range(max(0, y - 1), min(ROWS, y + 2))
                  for xx in range(max(0, x - 1), min(COLS, x + 2)))
              / ((min(ROWS, y + 2) - max(0, y - 1)) * (min(COLS, x + 2) - max(0, x - 1)))
              for x in range(COLS)] for y in range(ROWS)]

embers, sparks = [], []           # [x, y, vx, vy, life]
tick = 0.0
COOL = 0.2 * DECAY * 40 / ROWS    # the reference grid is 40 rows tall


def step():
    global tick
    base = heat[ROWS - 1]
    for x in range(COLS):
        if R() < 0.12:
            base[x] *= 0.7
        else:
            base[x] = max(base[x], INTENSITY * (0.6 + 0.4 * R()))

    # flame tongues
    if R() < 0.7:
        for _ in range(1 + rng.randrange(4)):
            cx, h, s = rng.randrange(COLS), 3 + rng.randrange(6), 7 + 3 * R()
            for e in range(h):
                y = ROWS - 3 - e
                half = 1.5 * math.sin(e / h * math.pi)
                i = -half
                while i <= half:
                    x = cx + round(i + R() - 0.5)
                    if 0 <= x < COLS:
                        heat[y][x] = max(heat[y][x], s * (1 - e / h * 0.5) * (0.6 + 0.4 * R()))
                    i += 1

    # letters smoulder: a gentle heat source so wisps rise off the name
    for (y, x) in mask:
        heat[y][x] = max(heat[y][x], 3.0 + 1.5 * R())

    tick += 0.02
    for y in range(ROWS - 1):
        lift = 1 - y / ROWS
        below = heat[y + 1]
        below2 = heat[y + 2] if y + 2 < ROWS else None
        nrow = noise[(y + int(10 * tick)) % ROWS]
        new = [0.0] * COLS
        for x in range(COLS):
            t, w = 3 * below[x], 3
            if x > 0:
                t += 2 * below[x - 1]; w += 2
            if x < COLS - 1:
                t += 2 * below[x + 1]; w += 2
            if x > 1:
                t += below[x - 2]; w += 1
            if x < COLS - 2:
                t += below[x + 2]; w += 1
            if below2:
                t += below2[x]; w += 1
            v = t / w - COOL * (0.6 + nrow[x] + 0.4 * R())
            v += (R() - 0.5) * lift * TURBULENCE * 0.12
            new[x] = max(0.0, min(10.0, v))
        heat[y] = new

    for y in range(ROWS - 6, ROWS - 1):
        row = heat[y]
        for x in range(1, COLS - 1):
            row[x] = 0.85 * row[x] + 0.075 * (row[x - 1] + row[x + 1])

    if R() < 0.21:
        embers.append([R() * COLS, ROWS - 2 - 3 * R(), 1.2 * (R() - 0.5), -0.3 - 0.4 * R(), 1.2 + 2.0 * R()])
    if R() < 0.46:
        for _ in range(1 + rng.randrange(3)):
            sparks.append([R() * COLS, ROWS - 3 - 2 * R(), 3 * (R() - 0.5), -1.2 - 1.6 * R(), 0.3 + 0.4 * R()])
    for p in embers:
        p[4] -= 1 / FPS; p[0] += p[2]; p[1] += p[3]
        p[2] += 0.5 * (R() - 0.5); p[3] -= 0.03
    for p in sparks:
        p[4] -= 1 / FPS; p[0] += p[2]; p[1] += p[3]
        p[2] += 2 * (R() - 0.5); p[3] += 0.2
    for ps in (embers, sparks):
        ps[:] = [p for p in ps if p[4] > 0 and p[1] >= 0 and 0 <= p[0] < COLS]


for _ in range(WARMUP):
    step()

W, H = COLS * CW, ROWS * RH + 6
NAME_SLOT = len(DARK)
frames = []
for f in range(FRAMES):
    step()
    cells = {}                    # (y, x) -> (char, slot)
    for y in range(ROWS):
        for x in range(COLS):
            h = heat[y][x]
            ci = min(9, int(h + 0.5))
            if ci:
                cells[(y, x)] = (CHARS[ci], SLOT[max(1, min(9, int(h)))])
    for p in embers:
        k = (int(p[1]), int(p[0]))
        if k[0] < ROWS:
            cells[k] = ("*" if p[4] > 0.3 else ".", 4 if p[4] > 0.5 else 3)
    for p in sparks:
        k = (int(p[1]), int(p[0]))
        if k[0] < ROWS:
            cells[k] = ("'", 4)
    for k in mask:
        cells[k] = ("#", NAME_SLOT)

    out = []
    for slot in range(NAME_SLOT + 1):
        spans = []
        for y in range(ROWS):
            s = "".join(cells[(y, x)][0] if (y, x) in cells and cells[(y, x)][1] == slot else " "
                        for x in range(COLS)).rstrip()
            if s:
                spans.append(f'<tspan x="0" y="{(y + 1) * RH - 3}">{s}</tspan>')
        if spans:
            out.append(f'<text class="c{slot}">' + "".join(spans) + "</text>")
    delay = -(FRAMES - f) / FPS if f else 0
    frames.append(f'<g class="f" style="animation-delay:{delay:.3f}s">' + "".join(out) + "</g>")


def css(colors, name):
    return "".join(f".c{i}{{fill:{c}}}" for i, c in enumerate(colors + [name]))


dur = FRAMES / FPS
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H}" width="{W:.0f}" height="{H}" role="img" aria-label="{NAME.title()}, in ASCII fire">
<style>
{css(DARK, NAME_DARK)}
@media (prefers-color-scheme:light){{{css(LIGHT, NAME_LIGHT)}}}
text{{font:{FS}px ui-monospace,SFMono-Regular,Menlo,"DejaVu Sans Mono","Liberation Mono",monospace;white-space:pre}}
.f{{opacity:0;animation:k {dur}s steps(1) infinite}}
@keyframes k{{0%{{opacity:1}}{100 / FRAMES:.4f}%{{opacity:0}}100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.f{{animation:none}}.f:first-of-type{{opacity:1}}}}
</style>
<g xml:space="preserve">
{chr(10).join(frames)}
</g>
</svg>
'''
dest = Path(__file__).resolve().parent.parent / "assets" / "fire.svg"
dest.write_text(svg)
print(f"{dest}  {len(svg) / 1024:.0f} KB  {COLS}x{ROWS}  {FRAMES} frames")
