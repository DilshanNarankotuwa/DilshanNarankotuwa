"""Draw assets/hero.svg: Fig. 1 of the profile.

An illustrative near-infrared spectrum (science) is sampled at seven
wavelengths and standardized with SNV (software), then read by a small
network that returns one prediction (intelligence). Text comes from
lab/identity.json. Standard library only:  python lab/hero.py
"""

import json
import math
import os

from typeset import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

W, H = 1200, 460
INK = {
    "midnight": "#0E1524",   # panel
    "edge": "#1C2840",       # panel border
    "paper": "#E8EDF4",      # name
    "graphite": "#93A1B5",   # tagline and annotations
    "rule": "#33415C",       # braces and baselines
    "infrared": "#E7A35B",   # science
    "signal": "#5ED1C4",     # intelligence
}

# Near-infrared bands typical of dried plant material: (centre nm, height, width nm)
BANDS = [
    (1195, 0.05, 40),   # C-H second overtone
    (1450, 0.33, 62),   # O-H first overtone
    (1725, 0.11, 38),   # C-H first overtone
    (1765, 0.07, 32),
    (1940, 0.46, 58),   # O-H combination (water)
    (2100, 0.24, 78),   # O-H and C-O combinations
    (2275, 0.13, 38),
    (2315, 0.17, 32),   # C-H combinations
    (2355, 0.11, 34),
    (2480, 0.12, 52),
]
LAMBDA = (1100, 2500)
SAMPLES = [1195, 1450, 1725, 1940, 2100, 2315, 2480]

# Layout
SPEC_X = (56, 640)
SPEC_BASE, SPEC_H = 368, 150
ROWS = [222 + 24 * i for i in range(7)]          # one row per sampled wavelength
VEC_RIGHT, VEC_BRACKETS = 790, (708, 804)        # right edge of the numbers, bracket x
LAYERS = [(846, ROWS), (940, [238, 266, 294, 322, 350]), (1030, [266, 294, 322]), (1110, [294])]
BRACE_Y, BRACE_DEPTH, LABEL_Y = 390, 12, 428

# Timing of the one-time reveal, in seconds
DRAW_START, DRAW_TIME = 0.2, 1.6


def absorbance(lam):
    base = 0.25 + 0.20 * (lam - LAMBDA[0]) / (LAMBDA[1] - LAMBDA[0])
    return base + sum(a * math.exp(-((lam - c) ** 2) / (2 * s * s)) for c, a, s in BANDS)


def spectrum_points(n=281):
    lams = [LAMBDA[0] + i * (LAMBDA[1] - LAMBDA[0]) / (n - 1) for i in range(n)]
    values = [absorbance(lam) for lam in lams]
    lo, hi = min(values), max(values)
    to_x = lambda lam: SPEC_X[0] + (lam - LAMBDA[0]) / (LAMBDA[1] - LAMBDA[0]) * (SPEC_X[1] - SPEC_X[0])
    to_y = lambda v: SPEC_BASE - (v - lo) / (hi - lo) * SPEC_H
    return [(to_x(l), to_y(v)) for l, v in zip(lams, values)], to_x, to_y


def snv(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    return [(v - mean) / sd for v in values]


def brace(x1, x2, y, d):
    """A horizontal curly brace opening upwards, like LaTeX's \\underbrace."""
    m, h, r = (x1 + x2) / 2, d / 2, min(d, (x2 - x1) / 4)
    return (f"M{x1:.1f} {y:.1f} Q{x1:.1f} {y + h:.1f} {x1 + r:.1f} {y + h:.1f} "
            f"L{m - r:.1f} {y + h:.1f} Q{m:.1f} {y + h:.1f} {m:.1f} {y + d:.1f} "
            f"Q{m:.1f} {y + h:.1f} {m + r:.1f} {y + h:.1f} "
            f"L{x2 - r:.1f} {y + h:.1f} Q{x2:.1f} {y + h:.1f} {x2:.1f} {y:.1f}")


def delay(t):
    return f' style="animation-delay:{t:.2f}s"'


def main():
    with open(os.path.join(HERE, "identity.json"), encoding="utf-8") as fh:
        ident = json.load(fh)
    T = Typesetter()
    out = []

    # Panel
    out.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" '
               f'fill="{INK["midnight"]}" stroke="{INK["edge"]}"/>')

    # Name and tagline
    out.append(T.text(ident["name"], 54, 100, "rm", 70, INK["paper"], tracking=-0.004))
    out.append(T.text(ident["tagline"], 57, 144, "it", 25, INK["graphite"]))

    # Science: the spectrum, drawn once like an instrument scan
    pts, to_x, to_y = spectrum_points()
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = line + f" L{SPEC_X[1]} {SPEC_BASE} L{SPEC_X[0]} {SPEC_BASE} Z"
    out.append(f'<line x1="{SPEC_X[0]}" y1="{SPEC_BASE}" x2="{SPEC_X[1]}" y2="{SPEC_BASE}" '
               f'stroke="{INK["rule"]}" stroke-width="1"/>')
    out.append(f'<path d="{area}" fill="url(#absorb)" class="fade"{delay(DRAW_START + DRAW_TIME)}/>')
    out.append(f'<path d="{line}" fill="none" stroke="url(#heat)" stroke-width="2.4" '
               f'stroke-linejoin="round" stroke-linecap="round" pathLength="1" class="draw"{delay(DRAW_START)}/>')

    # Software: seven wavelengths are sampled (rings) and standardized with SNV
    raw = [absorbance(lam) for lam in SAMPLES]
    feats = snv(raw)
    for lam, value in zip(SAMPLES, raw):
        t = DRAW_START + DRAW_TIME * (lam - LAMBDA[0]) / (LAMBDA[1] - LAMBDA[0])
        out.append(f'<circle cx="{to_x(lam):.1f}" cy="{to_y(value):.1f}" r="4.2" fill="{INK["midnight"]}" '
                   f'stroke="{INK["infrared"]}" stroke-width="1.6" class="fade"{delay(t)}/>')
    top, bottom = ROWS[0] - 16, ROWS[-1] + 12
    for bx, hook in ((VEC_BRACKETS[0], 7), (VEC_BRACKETS[1], -7)):
        out.append(f'<path d="M{bx + hook} {top} H{bx} V{bottom} H{bx + hook}" fill="none" '
                   f'stroke="{INK["graphite"]}" stroke-width="1.4"/>')
    t_vec = DRAW_START + DRAW_TIME
    for i, (y, z) in enumerate(zip(ROWS, feats)):
        label = f"{z:.2f}".replace("-", "\u2212")
        out.append(T.text(label, VEC_RIGHT, y + 5, "rm", 16, INK["paper"], anchor="end",
                          attrs=f' class="fade"{delay(t_vec + 0.07 * i)}'))

    # Intelligence: a small network reads the vector and returns one number
    t0 = t_vec + 0.7
    layers = [[(x, y) for y in ys] for x, ys in LAYERS]
    edges, nodes = [], []
    for k, layer in enumerate(layers):
        t = t0 + 0.32 * k
        last = k == len(layers) - 1
        for bx, by in layer:
            r = 6.5 if last else (3.4 if k == 0 else 4.6)
            fill = INK["signal"] if last else (INK["paper"] if k == 0 else INK["midnight"])
            stroke = INK["paper"] if k == 0 else INK["signal"]
            nodes.append(f'<circle cx="{bx}" cy="{by}" r="{r}" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="1.6" class="fade"{delay(t + 0.15)}/>')
        if k == 0:
            continue
        grad = "wire0" if k == 1 else "wire1"
        for ax, ay in layers[k - 1]:
            for bx, by in layer:
                edges.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx}" y2="{by}" '
                             f'stroke="url(#{grad})" stroke-width="1" opacity="0.34" class="fade"{delay(t)}/>')
    out.extend(edges)
    ox, oy = LAYERS[-1][0], LAYERS[-1][1][0]
    t_out = t0 + 0.32 * (len(layers) - 1) + 0.15
    out.append(f'<circle cx="{ox}" cy="{oy}" r="18" fill="{INK["signal"]}" opacity="0.35" '
               f'filter="url(#glow)" class="bloom"{delay(t_out)}/>')
    out.extend(nodes)
    out.append(T.text("\u0109", ox + 17, oy + 8, "it", 30, INK["signal"],
                      attrs=f' class="fade"{delay(t_out)}'))

    # Underbraces naming the three stages
    spans = [(SPEC_X[0], SPEC_X[1]), (VEC_BRACKETS[0] - 6, VEC_BRACKETS[1] + 6), (LAYERS[0][0] - 10, 1150)]
    for (x1, x2), label in zip(spans, ident["stages"]):
        out.append(f'<path d="{brace(x1, x2, BRACE_Y, BRACE_DEPTH)}" fill="none" '
                   f'stroke="{INK["rule"]}" stroke-width="1.3" stroke-linecap="round"/>')
        out.append(T.text(label, (x1 + x2) / 2, LABEL_Y, "it", 18, INK["graphite"], anchor="middle"))

    style = """
.draw{animation:draw %.2fs linear backwards}
@keyframes draw{from{stroke-dasharray:1 1;stroke-dashoffset:1}to{stroke-dasharray:1 1;stroke-dashoffset:0}}
.fade{animation:fade .6s ease-out backwards}
@keyframes fade{from{opacity:0}}
.bloom{transform-box:fill-box;transform-origin:center;animation:bloom 1.4s ease-out backwards}
@keyframes bloom{0%%{opacity:0;transform:scale(.3)}45%%{opacity:.9;transform:scale(1.5)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""" % DRAW_TIME

    defs = (
        f'<linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="{SPEC_X[0]}" y1="0" x2="{SPEC_X[1]}" y2="0">'
        f'<stop offset="0" stop-color="{INK["infrared"]}" stop-opacity="0.75"/>'
        f'<stop offset="1" stop-color="{INK["infrared"]}"/></linearGradient>'
        f'<linearGradient id="absorb" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{INK["infrared"]}" stop-opacity="0.12"/>'
        f'<stop offset="1" stop-color="{INK["infrared"]}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="wire0" gradientUnits="userSpaceOnUse" x1="{LAYERS[0][0]}" y1="0" x2="{LAYERS[1][0]}" y2="0">'
        f'<stop offset="0" stop-color="{INK["paper"]}" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="{INK["signal"]}"/></linearGradient>'
        f'<linearGradient id="wire1" gradientUnits="userSpaceOnUse" x1="{LAYERS[1][0]}" y1="0" x2="{LAYERS[-1][0]}" y2="0">'
        f'<stop offset="0" stop-color="{INK["signal"]}" stop-opacity="0.7"/>'
        f'<stop offset="1" stop-color="{INK["signal"]}"/></linearGradient>'
        f'<filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="7"/></filter>'
        + T.defs()
    )
    desc = (f'{ident["name"]}. {ident["tagline"]} An illustrative near-infrared spectrum is sampled '
            f'at seven wavelengths, standardized, and read by a small neural network that returns '
            f'one prediction. Braces label the three stages: {", ".join(ident["stages"])}.')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">'
        f'<title id="title">{ident["name"]}</title><desc id="desc">{desc}</desc>'
        f'<style>{style}</style><defs>{defs}</defs>{"".join(out)}</svg>\n'
    )
    dest = os.path.join(ROOT, "assets", "hero.svg")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"hero.svg written ({len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
