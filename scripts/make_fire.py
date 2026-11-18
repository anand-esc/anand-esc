#!/usr/bin/env python3
"""Generate assets/fire.svg: a looping ASCII fire with a name standing in it.

The flames use the classic "Doom fire" spread: every cell takes the heat of
a cell below it, shifted a random step sideways and cooled a random amount,
which grows tall, uneven tongues. Sparks drift up out of the flames.

The name is traced from a heavy font into pixels and drawn as solid blocks
(not text), so it stays crisp in any browser, with a soft ember glow behind.

Usage: python3 scripts/make_fire.py [NAME] [SEED]
Needs Pillow and the Noto Sans Black font for the name.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAME = sys.argv[1].upper() if len(sys.argv) > 1 else "SURYANSH"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 3
FONT = "/usr/share/fonts/noto/NotoSans-Black.ttf"

ROWS, COLS = 30, 112
FRAMES, FPS, WARMUP = 24, 10, 200
CW, RH, FS = 8.4, 16, 14            # cell width, row height, font size
MAXH = 36                           # heat levels, as in the original Doom fire
CHARS = " ..::--==++**##%%@@"       # heat -> character, cool to hot
NAME_ROW = 13                       # text row where the name's top sits
COOL = (0, 0, 1, 1, 1, 1, 2)        # random cooling per row: sets flame height

# heat bands -> colour slots (index into the palettes below)
BANDS = [(3, 0), (11, 1), (20, 2), (29, 3)]
DARK = ["#5a2210", "#b8430f", "#ee8a22", "#ffdc9a"]
LIGHT = ["#dcae90", "#c25f1d", "#93370a", "#4a1503"]
NAME_DARK, NAME_LIGHT = "#fff3d6", "#2a0d02"
GLOW_DARK, GLOW_LIGHT = "#ff8a2a", "#e0782f"

rng = random.Random(SEED)

# ---- name bitmap: one pixel = half a text cell (8.4 x 8 px, roughly square)
font = ImageFont.truetype(FONT, 20)
l, t, r, b = font.getbbox(NAME)
img = Image.new("1", (r - l + 2, b - t + 2), 0)
ImageDraw.Draw(img).text((1 - l, 1 - t), NAME, font=font, fill=1)
img = img.crop(img.getbbox())
img = img.resize((round(img.width * 8 / 8.4), img.height), Image.NEAREST)
NW, NH = img.size
px = img.load()
x0 = (COLS - NW) // 2
y0 = NAME_ROW * 2                   # in half-cell pixels
name_px = {(y0 + y, x0 + x) for y in range(NH) for x in range(NW) if px[x, y]}
name_cells = {(y // 2, x) for (y, x) in name_px}

# ---- fire simulation
heat = [[0] * COLS for _ in range(ROWS)]
sparks = []                         # [x, y, vx, vy, life]


# hot spots that wander along the fuel line; the gaps between them are what
# turn a wall of heat into separate tongues of flame
import math
SPOTS = [[rng.uniform(0, COLS), rng.uniform(-0.35, 0.35), rng.uniform(5.0, 9.0),
          rng.uniform(0, 6.28), rng.uniform(0.15, 0.35)] for _ in range(11)]


def step(t):
    base = heat[ROWS - 1]
    for sp in SPOTS:
        sp[0] = (sp[0] + sp[1]) % COLS
    for x in range(COLS):          # fuel: strong under hot spots, embers between
        f = 0.0
        for cx, _, w, ph, sp_ in SPOTS:
            d = min(abs(x - cx), COLS - abs(x - cx))
            pulse = 0.75 + 0.25 * math.sin(t * sp_ + ph)
            f = max(f, pulse * math.exp(-(d / w) ** 2))
        h = 9 + f * (MAXH - 9)
        base[x] = max(0, min(MAXH, int(h) - rng.randint(0, 4)))
    for y in range(ROWS - 1):      # each cell pulls heat from just below
        below = heat[y + 1]
        row = heat[y]
        for x in range(COLS):
            src = below[min(COLS - 1, max(0, x + rng.choice((-1, 0, 0, 1))))]
            row[x] = max(0, src - rng.choice(COOL))
    if rng.random() < 0.5:         # sparks leave the flame tips
        x = rng.randrange(COLS)
        for y in range(ROWS):
            if heat[y][x] > 14:
                sparks.append([x + rng.random(), y - 0.5, rng.uniform(-0.4, 0.4),
                               -rng.uniform(0.5, 1.0), rng.uniform(0.6, 1.4)])
                break
    for s in sparks:
        s[0] += s[2] + rng.uniform(-0.3, 0.3)
        s[1] += s[3]
        s[4] -= 1 / FPS
    sparks[:] = [s for s in sparks if s[4] > 0 and s[1] >= 0 and 0 <= s[0] < COLS]


for t in range(WARMUP):
    step(t)

W, H = COLS * CW, ROWS * RH + 4
frames = []
for f in range(FRAMES):
    step(WARMUP + f)
    rows = {}                      # slot -> list of row strings
    for y in range(ROWS):
        lines = [[" "] * COLS for _ in DARK]
        for x in range(COLS):
            if (y, x) in name_cells:
                continue
            h = heat[y][x]
            if h <= 0:
                continue
            slot = 0
            for lim, s in BANDS:
                if h >= lim:
                    slot = s
            lines[slot][x] = CHARS[min(len(CHARS) - 1, h * len(CHARS) // (MAXH + 1))]
        for s in sparks:
            sx, sy = int(s[0]), int(s[1])
            if sy == y and (sy, sx) not in name_cells:
                lines[3 if s[4] > 0.7 else 2][sx] = "*" if s[4] > 0.9 else "'"
        for slot, chars in enumerate(lines):
            text = "".join(chars).rstrip()
            lead = len(text) - len(text.lstrip())
            if text.strip():
                rows.setdefault(slot, []).append(
                    f'<tspan x="{lead * CW:g}" y="{(y + 1) * RH - 4}">{text[lead:]}</tspan>')
    out = "".join(f'<text class="c{s}">{"".join(v)}</text>' for s, v in sorted(rows.items()))
    delay = -(FRAMES - f) / FPS if f else 0
    frames.append(f'<g class="f" style="animation-delay:{delay:.3f}s">{out}</g>')


def name_path():
    """Horizontal runs of name pixels as one SVG path (pixel = CW x RH/2)."""
    d = []
    ph = RH / 2
    for y in range(min(p[0] for p in name_px), max(p[0] for p in name_px) + 1):
        xs = sorted(x for (yy, x) in name_px if yy == y)
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
                j += 1
            d.append(f"M{xs[i] * CW:.1f} {y * ph:.0f}h{(j - i + 1) * CW:.1f}v{ph:.0f}h-{(j - i + 1) * CW:.1f}z")
            i = j + 1
    return "".join(d)


def css(colors, name, glow):
    c = "".join(f".c{i}{{fill:{v}}}" for i, v in enumerate(colors))
    return c + f".nm{{fill:{name}}}.gl{{fill:{glow}}}"


dur = FRAMES / FPS
NP = name_path()
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H}" width="{W:.0f}" height="{H}" role="img" aria-label="{NAME.title()}, standing in ASCII fire">
<style>
{css(DARK, NAME_DARK, GLOW_DARK)}
@media (prefers-color-scheme:light){{{css(LIGHT, NAME_LIGHT, GLOW_LIGHT)}}}
text{{font:{FS}px ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace;white-space:pre}}
.f{{opacity:0;animation:k {dur}s steps(1) infinite}}
@keyframes k{{0%{{opacity:1}}{100 / FRAMES:.4f}%{{opacity:0}}100%{{opacity:0}}}}
.gl{{opacity:.55;animation:g 1.7s ease-in-out infinite alternate}}
@keyframes g{{from{{opacity:.35}}to{{opacity:.7}}}}
@media (prefers-reduced-motion:reduce){{.f,.gl{{animation:none}}.f:first-of-type{{opacity:1}}}}
</style>
<defs><filter id="blur" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="7"/></filter></defs>
<g xml:space="preserve">
{chr(10).join(frames)}
</g>
<path class="gl" filter="url(#blur)" d="{NP}"/>
<path class="nm" d="{NP}"/>
</svg>
'''
dest = Path(__file__).resolve().parent.parent / "assets" / "fire.svg"
dest.write_text(svg)
print(f"{dest}  {len(svg) / 1024:.0f} KB  {COLS}x{ROWS}  name {NW}x{NH}px  {FRAMES} frames")
