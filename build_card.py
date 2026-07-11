"""
Builds the neofetch-style profile card SVG (ASCII art + system-info panel),
in the spirit of the Andrew6rant/Andrew6rant README, for Suryansh Anand.

Produces dark_mode.svg and light_mode.svg with matching structure and
element IDs (repo_data, star_data, commit_data, follower_data, loc_data,
loc_add, loc_del + "_dots" siblings) so the companion today.py script can
overwrite the live GitHub stats via GitHub Actions, exactly like the
original.
"""

import html

# ---------------------------------------------------------------------------
# 1. Load ASCII art
# ---------------------------------------------------------------------------
with open('ascii_final.txt') as f:
    ART_LINES = [l for l in f.read().split('\n') if l != '']
ART_ROWS = len(ART_LINES)
ART_COLS = max(len(l) for l in ART_LINES)
ART_LINES = [l.ljust(ART_COLS) for l in ART_LINES]

# Density ramp used by ascii_gen.py (index 0 = lightest/emptiest -> last = densest)
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def opacity_for_char(ch):
    if ch == ' ':
        return 0.0
    idx = RAMP.index(ch) if ch in RAMP else 0
    frac = idx / (len(RAMP) - 1)
    # map to a pleasant visible range so even light strokes read on screen
    return round(0.18 + frac * 0.82, 3)


def run_length_encode(row):
    """Collapse consecutive identical characters into (char, count) runs."""
    runs = []
    i = 0
    while i < len(row):
        ch = row[i]
        j = i
        while j < len(row) and row[j] == ch:
            j += 1
        runs.append((ch, j - i))
        i = j
    return runs


# ---------------------------------------------------------------------------
# 2. Stats-panel content
# ---------------------------------------------------------------------------
# kind: 'header' | 'section' | 'field' | 'blank'
FIELDS = [
    ('header', 'suryansh@anand'),

    ('field', 'OS', 'Arch Linux \u00b7 Fedora \u00b7 Ubuntu'),
    ('field', 'Host', 'Sri Sri University (Student)'),
    ('field', 'Kernel', 'AI/ML Engineer \u2014 Agentic Systems'),
    ('field', 'IDE', 'VS Code \u00b7 Jupyter'),
    ('blank',),

    ('field', 'Languages.Core', 'Python, JavaScript, C++, SQL'),
    ('field', 'Languages.AI/ML', 'LangChain, LangGraph, Gemini API, OpenAI API'),
    ('field', 'Languages.Web', 'React, Node.js, FastAPI, Tailwind CSS'),
    ('blank',),

    ('field', 'Recognition.Google', "Gemini Student Ambassador '26"),
    ('field', 'Recognition.OpenSrc', "GSSoC'26 \u00b7 AI Agents Track"),
    ('blank',),

    ('section', 'Contact'),
    ('field', 'Email', 'suryansh.anand.dev@gmail.com'),
    ('field', 'LinkedIn', 'suryansh-anand'),
    ('field', 'GitHub', 'anand-esc'),
    ('blank',),

    ('section', 'GitHub Stats'),
    ('field', 'Repos', None, 'repo_data', '6', 'contrib_data', '11'),
    ('field', 'Stars', None, 'star_data', '0'),
    ('field', 'Commits', None, 'commit_data', '0'),
    ('field', 'Followers', None, 'follower_data', '0'),
    ('field', 'Lines of Code', None, 'loc_data', '0', 'loc_add', 'loc_del'),
]

TOTAL_ROWS = len(FIELDS)

# alignment column (in characters) where dot-leaders end and values begin
LABEL_MAXLEN = max(len(f[1]) for f in FIELDS if f[0] == 'field')
ALIGN_COL = LABEL_MAXLEN + 4          # e.g. "Recognition.OpenSrc" (20) -> 24
HEADER_RULE_LEN = 44                  # length of the "------" rule on header/section rows

# ---------------------------------------------------------------------------
# 3. Geometry
# ---------------------------------------------------------------------------
STATS_FONT = 13.2
STATS_CHAR_W = STATS_FONT * 0.6
STATS_LINE_H = 18.4

ART_FONT = 7.0
ART_CHAR_W = ART_FONT * 0.62
ART_LINE_H = (TOTAL_ROWS * STATS_LINE_H) / ART_ROWS  # matches panel height exactly

PAD = 34
GAP = 40
ART_W = ART_COLS * ART_CHAR_W
ART_H = ART_ROWS * ART_LINE_H

def field_full_width_chars(f):
    if f[0] == 'field':
        label = f[1]
        value = f[2] if f[2] is not None else (f[4] if len(f) > 4 else '')
        width = ALIGN_COL + len(str(value)) + 2
        if len(f) > 5:  # loc_data row: value + " (++NNN, --NNN)"
            width += len('  (++000,000, --000,000)')
        return width
    if f[0] in ('header', 'section'):
        return HEADER_RULE_LEN + len(f[1]) + 4
    return 0

STATS_COLS = max(field_full_width_chars(f) for f in FIELDS) + 3  # safety margin
STATS_W = STATS_COLS * STATS_CHAR_W

CARD_W = PAD + ART_W + GAP + STATS_W + PAD
CARD_H = PAD + ART_H + PAD

FONT_STACK = "'Cascadia Code','Fira Code',Consolas,'Liberation Mono',Menlo,monospace"

# ---------------------------------------------------------------------------
# 4. Theme palettes
# ---------------------------------------------------------------------------
THEMES = {
    'dark': dict(
        bg='#0d0d0d', border='#2a2a2a', art='#c7c7c7',
        header='#ffffff', rule='#4a4a4a',
        label='#d3a373', dots='#4a4a4a', value='#e8e8e8',
        section='#ffffff',
    ),
    'light': dict(
        bg='#f5f5f5', border='#dcdcdc', art='#3a3a3a',
        header='#111111', rule='#b8b8b8',
        label='#a9660f', dots='#b8b8b8', value='#2a2a2a',
        section='#111111',
    ),
}


def esc(s):
    return html.escape(str(s), quote=True)


def build_art_svg(theme):
    x0 = PAD
    y0 = PAD + ART_FONT
    out = []
    for r, row in enumerate(ART_LINES):
        y = y0 + r * ART_LINE_H
        runs = run_length_encode(row)
        tspans = []
        cx = 0
        for ch, count in runs:
            w = count * ART_CHAR_W
            op = opacity_for_char(ch)
            if op > 0:
                safe_ch = esc(ch) * count
                tspans.append(
                    f'<tspan x="{x0 + cx:.1f}" y="{y:.1f}" textLength="{w:.1f}" '
                    f'lengthAdjust="spacingAndGlyphs" fill-opacity="{op}">{safe_ch}</tspan>'
                )
            cx += w
        out.append(''.join(tspans))
    return (
        f'<text font-family="{FONT_STACK}" font-size="{ART_FONT}px" fill="{theme["art"]}" '
        f'xml:space="preserve">{"".join(out)}</text>'
    )


def build_stats_svg(theme):
    x0 = PAD + ART_W + GAP
    y = PAD + STATS_FONT
    parts = []
    for f in FIELDS:
        kind = f[0]
        if kind == 'blank':
            y += STATS_LINE_H
            continue

        if kind == 'header':
            text = f[1]
            rule = ' ' + ('\u2500' * (HEADER_RULE_LEN - len(text)))
            parts.append(
                f'<text x="{x0:.2f}" y="{y:.2f}" font-family="{FONT_STACK}" '
                f'font-size="{STATS_FONT}px" font-weight="700" '
                f'fill="{theme["header"]}">{esc(text)}'
                f'<tspan fill="{theme["rule"]}" font-weight="400">{esc(rule)}</tspan></text>'
            )
            y += STATS_LINE_H * 1.4
            continue

        if kind == 'section':
            text = f[1]
            rule = '\u2500 ' + text + ' ' + ('\u2500' * max(2, HEADER_RULE_LEN - len(text)))
            parts.append(
                f'<text x="{x0:.2f}" y="{y:.2f}" font-family="{FONT_STACK}" '
                f'font-size="{STATS_FONT}px" font-weight="700" '
                f'fill="{theme["section"]}">{esc(rule)}</text>'
            )
            y += STATS_LINE_H * 1.3
            continue

        if kind == 'field':
            label = f[1]
            if len(f) >= 5 and f[3]:
                value_id = f[3]
                value_text = f[4]
            else:
                value_id = None
                value_text = f[2]

            label_str = label + ':'
            dots_needed = max(1, ALIGN_COL - len(label_str))
            dots_str = ' ' + ('.' * max(0, dots_needed - 2)) + ' ' if dots_needed > 2 else ' ' * dots_needed

            lx = x0
            dx = x0 + len(label_str) * STATS_CHAR_W
            vx = x0 + ALIGN_COL * STATS_CHAR_W

            seg = [
                f'<tspan x="{lx:.2f}" y="{y:.2f}" fill="{theme["label"]}">{esc(label_str)}</tspan>',
                f'<tspan x="{dx:.2f}" y="{y:.2f}" fill="{theme["dots"]}">{esc(dots_str)}</tspan>',
            ]
            val_id_attr = f' id="{value_id}"' if value_id else ''

            if value_id == 'loc_data':
                # "12,345  (++123, --45)"
                loc_add_id, loc_del_id = f[5], f[6]
                seg.append(
                    f'<tspan x="{vx:.2f}" y="{y:.2f}"{val_id_attr} fill="{theme["value"]}">{esc(value_text)}</tspan>'
                )
                sx = vx + (len(str(value_text)) + 2) * STATS_CHAR_W
                seg.append(f'<tspan x="{sx:.2f}" y="{y:.2f}" fill="{theme["dots"]}">(</tspan>')
                ax = sx + 1 * STATS_CHAR_W
                seg.append(f'<tspan x="{ax:.2f}" y="{y:.2f}" id="{loc_add_id}" fill="#7fbf7f">++0</tspan>')
                cx2 = ax + 6 * STATS_CHAR_W
                seg.append(f'<tspan x="{cx2:.2f}" y="{y:.2f}" fill="{theme["dots"]}">, </tspan>')
                dxx = cx2 + 2 * STATS_CHAR_W
                seg.append(f'<tspan x="{dxx:.2f}" y="{y:.2f}" id="{loc_del_id}" fill="#d98080">--0</tspan>')
                ex = dxx + 6 * STATS_CHAR_W
                seg.append(f'<tspan x="{ex:.2f}" y="{y:.2f}" fill="{theme["dots"]}">)</tspan>')

            elif value_id == 'repo_data':
                # "6  (Contributed: 11)"
                contrib_id, contrib_default = f[5], f[6]
                seg.append(
                    f'<tspan x="{vx:.2f}" y="{y:.2f}"{val_id_attr} fill="{theme["value"]}">{esc(value_text)}</tspan>'
                )
                sx = vx + (len(str(value_text)) + 2) * STATS_CHAR_W
                seg.append(f'<tspan x="{sx:.2f}" y="{y:.2f}" fill="{theme["dots"]}">(Contributed: </tspan>')
                cxp = sx + 14 * STATS_CHAR_W
                seg.append(f'<tspan x="{cxp:.2f}" y="{y:.2f}" id="{contrib_id}" fill="{theme["value"]}">{esc(contrib_default)}</tspan>')
                ep = cxp + (len(str(contrib_default))) * STATS_CHAR_W
                seg.append(f'<tspan x="{ep:.2f}" y="{y:.2f}" fill="{theme["dots"]}">)</tspan>')

            else:
                seg.append(
                    f'<tspan x="{vx:.2f}" y="{y:.2f}"{val_id_attr} fill="{theme["value"]}">{esc(value_text)}</tspan>'
                )

            parts.append(
                f'<text font-family="{FONT_STACK}" font-size="{STATS_FONT}px">{"".join(seg)}</text>'
            )
            y += STATS_LINE_H
            continue
    return ''.join(parts)


def build_svg(mode):
    theme = THEMES[mode]
    art = build_art_svg(theme)
    stats = build_stats_svg(theme)
    divider_x = PAD + ART_W + GAP / 2
    svg = f'''<svg width="{CARD_W:.0f}" height="{CARD_H:.0f}" viewBox="0 0 {CARD_W:.0f} {CARD_H:.0f}" xmlns="http://www.w3.org/2000/svg">
  <rect x="0.5" y="0.5" width="{CARD_W-1:.0f}" height="{CARD_H-1:.0f}" rx="10" fill="{theme['bg']}" stroke="{theme['border']}"/>
  <line x1="{divider_x:.2f}" y1="{PAD-10:.2f}" x2="{divider_x:.2f}" y2="{CARD_H-PAD+10:.2f}" stroke="{theme['border']}" stroke-width="1"/>
  {art}
  {stats}
</svg>'''
    return svg


if __name__ == '__main__':
    for mode in ('dark', 'light'):
        svg = build_svg(mode)
        fname = f'{mode}_mode.svg'
        with open(fname, 'w') as f:
            f.write(svg)
        print(fname, len(svg), 'bytes', f'{CARD_W:.0f}x{CARD_H:.0f}')
