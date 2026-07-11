#!/usr/bin/env python3
"""Generates every SVG asset in ../assets from scratch.

No profile-README generators involved: each file is plain hand-parameterized
SVG with SMIL animation, built as light + dark variants so the profile adapts
to the viewer's GitHub theme via <picture> tags.
"""

import html
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

GRAD = ["#a78bfa", "#f0abfc", "#fda4af"]  # violet -> fuchsia -> rose

THEMES = {
    "dark":  {"muted": "#8b949e", "faint": "#8b949e", "glow_op": "0.16", "dot_op": 0.55},
    "light": {"muted": "#57606a", "faint": "#6e7781", "glow_op": "0.10", "dot_op": 0.45},
}

PHRASES = [
    "I build AI agents that browse, click and reason.",
    "RAG pipelines, typeahead search, HTTP servers from raw sockets.",
    "Java backends, TypeScript frontends, Python everywhere else.",
]

# ---- streaming-text timing (seconds) ----
P = 6.0            # window per phrase
C = P * len(PHRASES)  # full cycle
LEAD = 0.30        # pause before typing starts
DT = 0.038         # delay between characters
FADE = 0.45        # phrase fade-out duration
CHAR_IN = 0.10     # single character fade-in


def kt(t):
    """clamp a time to [0, C] and format as a keyTimes fraction"""
    return f"{max(0.0, min(t, C)) / C:.5f}"


def gradient(gid, animate=True, dur="6s"):
    stops = "".join(
        f'<stop offset="{int(i * 100 / (len(GRAD) - 1))}%" stop-color="{c}"/>'
        for i, c in enumerate(GRAD)
    )
    anim = (
        f'<animateTransform attributeName="gradientTransform" type="translate" '
        f'values="0 0;2 0" dur="{dur}" repeatCount="indefinite"/>'
        if animate else ""
    )
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect">'
        f"{stops}{anim}</linearGradient>"
    )


def phrase_group(i, text, muted):
    """One phrase: prompt marker + per-char streamed tspans + blinking caret."""
    t_win = i * P
    fs, fe = t_win + P - FADE, t_win + P

    # group gates the phrase's visibility window (fade out at the end)
    g_vals = "0;0;1;1;0;0"
    g_times = f"0;{kt(t_win)};{kt(t_win + 0.02)};{kt(fs)};{kt(fe)};1"
    g_anim = (
        f'<animate attributeName="opacity" values="{g_vals}" keyTimes="{g_times}" '
        f'dur="{C}s" repeatCount="indefinite"/>'
    )

    # prompt marker appears with the window
    t0 = t_win + 0.12
    marker = (
        f'<tspan fill="{GRAD[0]}" opacity="0">&#8250; '
        f'<animate attributeName="opacity" values="0;0;1;1" '
        f'keyTimes="0;{kt(t0)};{kt(t0 + CHAR_IN)};1" dur="{C}s" repeatCount="indefinite"/>'
        f"</tspan>"
    )

    chars = []
    for j, ch in enumerate(text):
        c0 = t_win + LEAD + j * DT
        chars.append(
            f'<tspan opacity="0">{html.escape(ch)}'
            f'<animate attributeName="opacity" values="0;0;1;1" '
            f'keyTimes="0;{kt(c0)};{kt(c0 + CHAR_IN)};1" dur="{C}s" repeatCount="indefinite"/>'
            f"</tspan>"
        )

    # caret becomes visible once typing ends, blinks through the hold
    te = t_win + LEAD + len(text) * DT + 0.05
    vals, times, t, on = ["0"], ["0"], te, True
    while t < fs - 0.15:
        vals.append("1" if on else "0")
        times.append(kt(t))
        on = not on
        t += 0.5
    vals.append("0")
    times.append(kt(fs))
    caret = (
        f'<tspan fill="{GRAD[1]}" opacity="0">&#9612;'
        f'<animate attributeName="opacity" calcMode="discrete" '
        f'values="{";".join(vals)}" keyTimes="{";".join(times)}" '
        f'dur="{C}s" repeatCount="indefinite"/>'
        f"</tspan>"
    )

    return (
        f'<g opacity="0">{g_anim}'
        f'<text x="450" y="176" text-anchor="middle" xml:space="preserve" '
        f'font-family="{MONO}" font-size="16.5" fill="{muted}">'
        f"{marker}{''.join(chars)}{caret}</text></g>"
    )


def dots(theme):
    pts = [
        (60, 40, 1.6, 3.9, 0.0), (140, 150, 1.2, 5.1, 1.2), (210, 66, 1.9, 4.4, 2.1),
        (320, 190, 1.3, 5.6, 0.7), (560, 195, 1.5, 4.8, 1.7), (690, 58, 1.9, 5.3, 0.4),
        (770, 160, 1.3, 4.1, 2.6), (840, 90, 1.7, 5.0, 1.1), (450, 24, 1.2, 6.0, 3.0),
        (40, 205, 1.4, 4.6, 0.9), (860, 205, 1.4, 5.4, 2.2), (110, 96, 1.1, 6.2, 1.5),
    ]
    op = theme["dot_op"]
    out = []
    for k, (x, y, r, dur, beg) in enumerate(pts):
        color = GRAD[k % len(GRAD)]
        out.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.15">'
            f'<animate attributeName="opacity" values="0.12;{op};0.12" '
            f'dur="{dur}s" begin="-{beg}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def hero(theme_name):
    t = THEMES[theme_name]
    label_tracking = 'letter-spacing="4"'
    phrases = "".join(phrase_group(i, p, t["muted"]) for i, p in enumerate(PHRASES))
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="230" viewBox="0 0 900 230" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
{gradient('g1')}
{gradient('g2', dur='8s')}
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
<stop offset="0%" stop-color="{GRAD[0]}" stop-opacity="{t['glow_op']}"/>
<stop offset="100%" stop-color="{GRAD[0]}" stop-opacity="0"/>
</radialGradient>
</defs>
<ellipse cx="450" cy="95" rx="330" ry="80" fill="url(#glow)">
<animate attributeName="opacity" values="0.7;1;0.7" dur="7s" repeatCount="indefinite"/>
</ellipse>
{dots(t)}
<text x="450" y="42" text-anchor="middle" font-family="{MONO}" font-size="12" {label_tracking} fill="{t['faint']}" opacity="0">SOFTWARE&#160;&#160;&#183;&#160;&#160;AGENTS&#160;&#160;&#183;&#160;&#160;SYSTEMS<animate attributeName="opacity" values="0;0.9" dur="0.9s" begin="0.1s" fill="freeze"/></text>
<text x="450" y="100" text-anchor="middle" font-family="{SANS}" font-size="44" font-weight="700" letter-spacing="9" fill="url(#g1)" opacity="0">MANASVI SABBARWAL<animate attributeName="opacity" values="0;1" dur="0.8s" begin="0.15s" fill="freeze"/></text>
<line x1="315" y1="124" x2="585" y2="124" stroke="url(#g2)" stroke-width="2" stroke-linecap="round" stroke-dasharray="270" stroke-dashoffset="270">
<animate attributeName="stroke-dashoffset" values="270;0" dur="1.1s" begin="0.5s" fill="freeze"/>
</line>
{phrases}
</svg>"""
    return svg


def divider(theme_name):
    base = "rgba(139,148,158,0.28)" if theme_name == "dark" else "rgba(110,119,129,0.28)"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="830" height="16" viewBox="0 0 830 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>{gradient('dg', animate=False)}</defs>
<line x1="2" y1="8" x2="828" y2="8" stroke="{base}" stroke-width="1"/>
<line x1="2" y1="8" x2="828" y2="8" stroke="url(#dg)" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="110 720">
<animate attributeName="stroke-dashoffset" values="830;0" dur="5s" repeatCount="indefinite"/>
</line>
</svg>"""


def pill(label, theme_name):
    t = THEMES[theme_name]
    w = max(122, int(len(label) * 9.6) + 58)
    cx = w // 2
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="42" viewBox="0 0 {w} 42" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>{gradient('pg', dur='7s')}</defs>
<rect x="1.5" y="1.5" width="{w - 3}" height="39" rx="19.5" stroke="url(#pg)" stroke-width="1.5" opacity="0.85">
<animate attributeName="opacity" values="0.6;1;0.6" dur="4s" repeatCount="indefinite"/>
</rect>
<circle cx="24" cy="21" r="2.4" fill="url(#pg)"/>
<text x="{cx + 7}" y="25.5" text-anchor="middle" font-family="{MONO}" font-size="11.5" letter-spacing="2.6" fill="{t['muted']}">{label}</text>
</svg>"""


def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {name} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        write(f"hero-{theme}.svg", hero(theme))
        write(f"divider-{theme}.svg", divider(theme))
        for label in ("PORTFOLIO", "LINKEDIN", "EMAIL"):
            write(f"pill-{label.lower()}-{theme}.svg", pill(label, theme))
