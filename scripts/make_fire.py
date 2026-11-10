#!/usr/bin/env python3
"""Generate assets/fire.svg: a looping ASCII fire with a name burning in it.

Usage: python3 scripts/make_fire.py [NAME] [SEED]
"""
import random
import sys
from pathlib import Path

NAME = sys.argv[1].upper() if len(sys.argv) > 1 else "SURYANSH"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 7

ROWS = 16
FRAMES, FPS, WARMUP = 30, 10, 80
NAME_TOP = 4                      # row where the name starts
CW, RH, FS = 8.4, 16, 14          # cell width, row height, font size

RAMP = " ..::--==++**##"
MAXH = len(RAMP) - 1
# (minimum heat, colour) from coolest to hottest
BANDS = [(1, "#5c2012"), (6, "#a63a0e"), (10, "#e8740c"), (13, "#f5b041")]
NAME_COLOR = "#ffe9cc"
# same roles on a light page: faint smoke up to deep ember, name darkest
LIGHT = ["#f1cdb0", "#eda268", "#e06c0a", "#b8400c"]
LIGHT_NAME = "#6b2410"

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
COLS = max(72, name_w + 16)
x0 = (COLS - name_w) // 2
mask = set()
for i, ch in enumerate(NAME):
    for r, line in enumerate(FONT.get(ch, FONT[" "])):
        for c, v in enumerate(line):
            if v == "#":
                mask.add((NAME_TOP + r, x0 + i * 7 + c))

rng = random.Random(SEED)
heat = [[0] * COLS for _ in range(ROWS)]


def step():
    for x in range(COLS):
        heat[ROWS - 1][x] = MAXH - rng.randint(0, 6)
    for y in range(ROWS - 1):
        for x in range(COLS):
            src = heat[y + 1][min(COLS - 1, max(0, x + rng.randint(-1, 1)))]
            heat[y][x] = max(0, src - rng.choice((0, 1, 1, 2, 2, 3, 4)))
    for (y, x) in mask:
        heat[y][x] = max(heat[y][x], 6 + rng.randint(0, 3))  # letters smoulder


for _ in range(WARMUP):
    step()

W, H = COLS * CW, ROWS * RH + 6
DARK_CSS = "".join(f".{k}{{fill:{c}}}" for k, (_, c) in zip("abcdefgh", BANDS)) + f".n{{fill:{NAME_COLOR}}}"
LIGHT_CSS = "".join(f".{k}{{fill:{c}}}" for k, c in zip("abcdefgh", LIGHT)) + f".n{{fill:{LIGHT_NAME}}}"


def row(y, text, color):
    return (f'<text y="{(y + 1) * RH - 3}" class="{color}" '
            f'textLength="{W:.1f}">{text}</text>')


frames = []
for f in range(FRAMES):
    step()
    out = []
    for y in range(ROWS):
        layers = [[" "] * COLS for _ in range(len(BANDS) + 1)]
        for x in range(COLS):
            h = heat[y][x]
            if (y, x) in mask:
                layers[-1][x] = "#"
                continue
            for b in range(len(BANDS) - 1, -1, -1):
                if h >= BANDS[b][0]:
                    layers[b][x] = RAMP[h]
                    break
        colors = "abcdefgh"[:len(BANDS)] + "n"
        for chars, color in zip(layers, colors):
            s = "".join(chars)
            if s.strip():
                out.append(row(y, s, color))
    delay = -(FRAMES - f) / FPS if f else 0
    frames.append(f'<g class="f" style="animation-delay:{delay:.2f}s">'
                  + "".join(out) + "</g>")

dur = FRAMES / FPS
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H}" width="{W:.0f}" height="{H}" role="img" aria-label="{NAME.title()}, in ASCII fire">
<style>
{DARK_CSS}
@media (prefers-color-scheme:light){{{LIGHT_CSS}}}
text{{font:{FS}px ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace;white-space:pre}}
.f{{opacity:0;animation:k {dur}s steps(1) infinite}}
@keyframes k{{0%{{opacity:1}}{100 / FRAMES:.4f}%{{opacity:0}}100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.f{{animation:none}}.f:first-of-type{{opacity:1}}}}
</style>
<g xml:space="preserve" lengthAdjust="spacing">
{chr(10).join(frames)}
</g>
</svg>
'''
dest = Path(__file__).resolve().parent.parent / "assets" / "fire.svg"
dest.write_text(svg)
print(f"{dest}  {len(svg) / 1024:.0f} KB  {COLS}x{ROWS}  {FRAMES} frames")
