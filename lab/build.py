"""Draw the static figures in assets/: hero, contact buttons, project cards and stack.

All text lives in lab/profile.json. Standard library only:  python lab/build.py
"""

import json
import os
import random
import re

from typeset import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

INK = {"bg": "#0B0D1A", "panel": "#0F1226", "edge": "#262A45", "grid": "#161A33",
       "text": "#F4F5FB", "muted": "#9298BC", "dim": "#4C527A", "prompt": "#8B9BFF"}
RAMP = ["#7C3AED", "#C026D3", "#F43F5E", "#FB923C", "#FDE047"]
COLORS = {"cyan": "#22D3EE", "green": "#4ADE80", "pink": "#F472B6", "yellow": "#FACC15",
          "violet": "#A78BFA", "orange": "#FB923C", "blue": "#60A5FA", "fuchsia": "#E879F9",
          "rose": "#F43F5E"}
MOTION = ("@keyframes f{from{opacity:0}}.f{animation:f .8s ease-out backwards}"
          "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")


# ------------------------------------------------------------------ helpers

def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(t):
    """Violet to yellow, like a plasma colormap."""
    t = min(1.0, max(0.0, t)) * (len(RAMP) - 1)
    i = min(int(t), len(RAMP) - 2)
    return mix(RAMP[i], RAMP[i + 1], t - i)


def gradient(gid, colors, x1=0, y1=0, x2=1, y2=0, units=""):
    n = len(colors) - 1
    stops = "".join(f'<stop offset="{i / n:.2f}" stop-color="{c}"/>' for i, c in enumerate(colors))
    u = f' gradientUnits="{units}"' if units else ""
    return f'<linearGradient id="{gid}"{u} x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w, h, body, defs="", style="", title="", desc=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            + (f"<style>{style}</style>" if style else "") + f"<defs>{defs}</defs>{body}</svg>\n")


def panel(w, h, r=24):
    return (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" '
            f'fill="{INK["bg"]}" stroke="{INK["edge"]}" stroke-width="1.5"/>')


def delay(t):
    return f' class="f" style="animation-delay:{t:.2f}s"'


def write(name, content):
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"{name}: {len(content.encode()) / 1024:.1f} KB")


def fit(T, text, face, size, max_w, min_size=12):
    while size > min_size and T.width(text, face, size) > max_w:
        size -= 1
    while T.width(text, face, size) > max_w and len(text) > 2:
        text = text[:-2] + "\u2026"
    return text, size


# --------------------------------------------------------------------- hero

def code_tokens(code):
    tokens = re.findall(r"\s+|[A-Za-z_][A-Za-z_0-9]*|.", code)
    out = []
    for i, tok in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if re.match(r"[A-Za-z_]", tok):
            color = COLORS["cyan"] if nxt == "(" else COLORS["orange"] if nxt == "=" else INK["text"]
        else:
            color = INK["muted"]
        out.append((tok, color))
    return out


def hero(p, dots):
    T = Typesetter()
    W, H = 1200, 640
    X0, Y0, X1, Y1 = 96, 92, 1060, 480
    out, defs = [panel(W, H)], []

    # The notebook cell that "produced" this figure
    x = 48
    for tok, color in [("In [1]: ", INK["prompt"])] + code_tokens(p["code"]):
        out.append(T.text(tok, x, 56, "mo", 17, color))
        x += T.width(tok, "mo", 17)

    # Axes
    for i in range(1, 8):
        gx = X0 + (X1 - X0) * i / 8
        out.append(f'<line x1="{gx:.1f}" y1="{Y0}" x2="{gx:.1f}" y2="{Y1}" stroke="{INK["grid"]}"/>')
    for i in range(1, 4):
        gy = Y0 + (Y1 - Y0) * i / 4
        out.append(f'<line x1="{X0}" y1="{gy:.1f}" x2="{X1}" y2="{gy:.1f}" stroke="{INK["grid"]}"/>')
    out.append(f'<path d="M{X0} {Y0} V{Y1} H{X1}" fill="none" stroke="{INK["dim"]}" stroke-width="1.5"/>')
    for i, label in ((0, "0"), (4, "0.5"), (8, "1")):
        out.append(T.text(label, X0 + (X1 - X0) * i / 8, Y1 + 26, "mo", 13, INK["dim"], anchor="middle"))
    for i, label in ((2, "0.5"), (4, "1")):
        out.append(T.text(label, X0 - 12, Y1 - (Y1 - Y0) * i / 4 + 5, "mo", 13, INK["dim"], anchor="end"))

    # The name, as a scatter plot
    lines, gap = dots["lines"], 30
    block = sum(l["height"] for l in lines) + gap * (len(lines) - 1)
    top, left = Y0 + (Y1 - Y0 - block) / 2 + 4, X0 + 44
    pts, boxes = [], []
    for line in lines:
        boxes.append((left - 8, top - 8, left + line["width"] + 8, top + line["height"] + 8))
        pts += [(left + px, top + py) for px, py in line["points"]]
        top += line["height"] + gap
    xlo, xhi = min(q[0] for q in pts), max(q[0] for q in pts)
    ylo, yhi = min(q[1] for q in pts), max(q[1] for q in pts)

    for i, (bx0, by0, bx1, by1) in enumerate(boxes):
        color = ("#7C3AED", "#FB923C")[i % 2]
        defs.append(f'<radialGradient id="neb{i}"><stop offset="0" stop-color="{color}" stop-opacity="{0.30 - 0.08 * i:.2f}"/>'
                    f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        out.append(f'<ellipse cx="{(bx0 + bx1) / 2:.0f}" cy="{(by0 + by1) / 2:.0f}" rx="{(bx1 - bx0) * 0.62:.0f}" '
                   f'ry="{(by1 - by0) * 1.25:.0f}" fill="url(#neb{i})"/>')

    rng = random.Random(11)
    n_txt = f"n = {len(pts):,}"
    lw = T.width(n_txt, "mo", 14) + 48
    legend = (X1 - 16 - lw, Y0 + 16, X1 - 16, Y0 + 54)
    noise = []
    while len(noise) < 150:
        nx, ny = rng.uniform(X0 + 14, X1 - 14), rng.uniform(Y0 + 14, Y1 - 14)
        if any(a < nx < c and b < ny < d for a, b, c, d in boxes + [legend]):
            continue
        noise.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="2" fill="{ramp((nx - X0) / (X1 - X0))}" '
                     f'opacity="0.45"{delay(0.3 + rng.random() * 1.4)}/>')
    out.extend(noise)

    r = round(p["dot_spacing"] * 0.37, 2)
    for x, y in pts:
        t = 0.82 * (x - xlo) / (xhi - xlo) + 0.18 * (y - ylo) / (yhi - ylo)
        sx, sy = rng.uniform(X0 + 10, X1 - 10), rng.uniform(Y0 + 10, Y1 - 10)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{ramp(t)}" class="d" '
                   f'style="--x:{sx - x:.0f}px;--y:{sy - y:.0f}px;animation-delay:{0.2 + rng.random() * 0.9:.2f}s"/>')

    # Legend and colorbar
    lx, ly = legend[0], legend[1]
    out.append(f'<g{delay(2.0)}><rect x="{lx:.1f}" y="{ly}" width="{lw:.1f}" height="38" rx="10" '
               f'fill="{INK["panel"]}" stroke="{INK["edge"]}"/>'
               f'<circle cx="{lx + 20:.1f}" cy="{ly + 19}" r="5.5" fill="{ramp(0.55)}"/>'
               + T.text(n_txt, lx + 34, ly + 24, "mo", 14, INK["text"]) + "</g>")
    cb = 1096
    defs.append(gradient("cbar", list(reversed(RAMP)), 0, 0, 0, 1))
    out.append(f'<rect x="{cb}" y="{Y0 + 4}" width="14" height="{Y1 - Y0 - 8}" rx="7" fill="url(#cbar)"/>')
    for t, label in ((0, "1.0"), (0.5, "0.5"), (1, "0.0")):
        out.append(T.text(label, cb + 24, Y0 + 4 + t * (Y1 - Y0 - 8) + 5, "mo", 13, INK["muted"]))
    mid = (Y0 + Y1) / 2
    out.append(f'<g transform="rotate(-90 1174 {mid})">'
               + T.text(p["colorbar_label"], 1174, mid, "mo", 15, INK["muted"], anchor="middle") + "</g>")

    # Title in the plasma gradient, then the subtitle
    ts, tr, tx, ty = 46, 0.05, X0, 568
    tw = T.width(p["title"], "un", ts, tr)
    defs.append(gradient("tg", RAMP, tx, 0, tx + tw, 0, "userSpaceOnUse"))
    defs.append(f'<mask id="tm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                + T.text(p["title"], tx, ty, "un", ts, "#FFFFFF", tracking=tr) + "</mask>")
    out.append(f'<rect x="{tx - 4}" y="{ty - ts}" width="{tw + 8:.0f}" height="{ts + 14}" fill="url(#tg)" '
               f'mask="url(#tm)"{delay(1.5)}/>')
    out.append(T.text(p["subtitle"], tx + 2, ty + 38, "mo", 17, INK["muted"], attrs=delay(1.8)))

    style = (".d{animation:d 1.8s cubic-bezier(.16,.84,.24,1) backwards}"
             "@keyframes d{from{transform:translate(var(--x),var(--y));fill:#2E3354}}" + MOTION)
    desc = (f"{p['name']}, data scientist. The name is drawn as a scatter plot of {len(pts)} points "
            f"colored from violet to yellow, inside a notebook-style figure with a colorbar labeled "
            f"{p['colorbar_label']}.")
    write("hero.svg", svg(W, H, "".join(out), "".join(defs) + T.defs(), style, p["name"], desc))
    return len(pts)


# ------------------------------------------------------------------ buttons

ICONS = {
    "mail": '<rect x="-10" y="-7.5" width="20" height="15" rx="2.5"/><path d="M-9 -5.5 L0 1.5 L9 -5.5"/>',
    "linkedin": '<rect x="-10" y="-10" width="20" height="20" rx="4.5"/>'
                '<path d="M-5 -1.5 V5.5 M-5 -5 V-4.8 M-0.5 5.5 V-1.5 M-0.5 2 C-0.5 -2.2 5 -2.6 5 1.5 V5.5"/>',
    "web": '<circle r="10"/><ellipse rx="4.2" ry="10"/><path d="M-10 0 H10"/>',
}


def button(b):
    T = Typesetter()
    h = 64
    c1, c2 = COLORS[b["colors"][0]], COLORS[b["colors"][1]]
    w = round(h + 4 + T.width(b["label"], "un", 19) + 30)
    body = (f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{(h - 3) / 2}" '
            f'fill="{INK["bg"]}" stroke="url(#edge)" stroke-width="2"/>'
            f'<circle cx="{h / 2 + 2}" cy="{h / 2}" r="21" fill="{c1}" fill-opacity="0.16"/>'
            f'<g transform="translate({h / 2 + 2} {h / 2})" fill="none" stroke="{c1}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[b["icon"]]}</g>'
            + T.text(b["label"], h + 4, h / 2 + 7, "un", 19, INK["text"]))
    defs = gradient("edge", [c1, c2], 0, 0, w, 0, "userSpaceOnUse") + T.defs()
    write(b["file"], svg(w, h, body, defs, title=b["label"], desc=b["label"]))


# -------------------------------------------------------------------- cards

def frame(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{INK["panel"]}" stroke="{INK["edge"]}"/>'


def viz_scatter(T, x, y, w, h, acc):
    rng = random.Random(5)
    a0, b0, a1, b1 = x + 24, y + h - 22, x + w - 20, y + 20
    out = [frame(x, y, w, h),
           f'<path d="M{a0} {b1} V{b0} H{a1}" fill="none" stroke="{INK["dim"]}" stroke-width="1.5"/>',
           f'<line x1="{a0}" y1="{b0}" x2="{a1}" y2="{b1}" stroke="#FFFFFF" stroke-opacity="0.4" '
           f'stroke-width="1.5" stroke-dasharray="5 6"/>']
    for _ in range(44):
        t = rng.random()
        v = min(0.97, max(0.03, t + rng.gauss(0, 0.08)))
        out.append(f'<circle cx="{a0 + 6 + t * (a1 - a0 - 12):.1f}" cy="{b0 - 6 - v * (b0 - b1 - 12):.1f}" '
                   f'r="4.2" fill="{ramp(t)}" fill-opacity="0.92"/>')
    return "".join(out)


def viz_bars(T, x, y, w, h, acc):
    vals = [1.0, 0.88, 0.79, 0.68, 0.58, 0.47, 0.37]
    bh, gap = 14, 8.5
    top = y + (h - (len(vals) * bh + (len(vals) - 1) * gap)) / 2
    out = [frame(x, y, w, h)]
    for i, v in enumerate(vals):
        out.append(f'<rect x="{x + 22}" y="{top + i * (bh + gap):.1f}" width="{(w - 44) * v:.1f}" '
                   f'height="{bh}" rx="7" fill="{ramp(1 - i / (len(vals) - 1))}"/>')
    return "".join(out)


def viz_graph(T, x, y, w, h, acc):
    nodes = {"CPU": (x + 50, y + 42), "RAM": (x + w - 50, y + 42), "MB": (x + w / 2, y + h / 2),
             "GPU": (x + 50, y + h - 42), "PSU": (x + w - 50, y + h - 42)}
    mx, my = nodes["MB"]
    out = [frame(x, y, w, h)]
    for name, (nx, ny) in nodes.items():
        if name != "MB":
            out.append(f'<line x1="{mx}" y1="{my}" x2="{nx}" y2="{ny}" stroke="{acc}" stroke-opacity="0.55" stroke-width="2"/>')
            cx, cy = (mx + nx) / 2, (my + ny) / 2
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="{INK["panel"]}" stroke="#4ADE80" stroke-width="1.6"/>'
                       f'<path d="M{cx - 3.5:.1f} {cy:.1f} L{cx - 1:.1f} {cy + 2.6:.1f} L{cx + 3.8:.1f} {cy - 2.8:.1f}" '
                       f'fill="none" stroke="#4ADE80" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    for name, (nx, ny) in nodes.items():
        hub = name == "MB"
        if hub:
            out.append(f'<rect x="{nx - 27}" y="{ny - 14}" width="54" height="28" rx="9" fill="{INK["panel"]}"/>')
        out.append(f'<rect x="{nx - 27}" y="{ny - 14}" width="54" height="28" rx="9" fill="{acc if hub else INK["panel"]}" '
                   f'fill-opacity="{0.22 if hub else 1}" stroke="{acc}" stroke-width="1.6"/>')
        out.append(T.text(name, nx, ny + 4.5, "mb", 12, INK["text"], anchor="middle"))
    return "".join(out)


def viz_ensemble(T, x, y, w, h, acc):
    out = [frame(x, y, w, h)]
    ox, oy = x + w - 42, y + h / 2
    for i, color in enumerate((COLORS["violet"], COLORS["fuchsia"], COLORS["cyan"])):
        tx, ty = x + 50, y + 38 + i * (h - 76) / 2
        out.append(f'<path d="M{tx + 30} {ty - 2} C{tx + 80} {ty - 2} {ox - 50} {oy} {ox - 16} {oy}" fill="none" '
                   f'stroke="{color}" stroke-opacity="0.6" stroke-width="1.8"/>')
        leaves = [(tx - 24, ty + 18), (tx - 8, ty + 18), (tx + 8, ty + 18), (tx + 24, ty + 18)]
        kids = [(tx - 16, ty + 2), (tx + 16, ty + 2)]
        edges = [((tx, ty - 14), k) for k in kids] + [(kids[0], leaves[0]), (kids[0], leaves[1]),
                                                      (kids[1], leaves[2]), (kids[1], leaves[3])]
        for (a, b), (c, d) in edges:
            out.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{color}" stroke-opacity="0.7" stroke-width="1.5"/>')
        for (cx, cy) in [(tx, ty - 14)] + kids + leaves:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{color}"/>')
    out.append(f'<circle cx="{ox}" cy="{oy}" r="24" fill="{acc}" fill-opacity="0.12"/>'
               f'<circle cx="{ox}" cy="{oy}" r="14" fill="url(#out)"/>')
    return "".join(out)


VIZ = {"scatter": viz_scatter, "bars": viz_bars, "graph": viz_graph, "ensemble": viz_ensemble}


def card(c, cats):
    T = Typesetter()
    W, H = 600, 340
    acc = COLORS[c["accent"]]
    defs = (f'<radialGradient id="glow" cx="0.92" cy="0.02" r="0.85"><stop offset="0" stop-color="{acc}" '
            f'stop-opacity="0.32"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>'
            + gradient("out", [RAMP[1], RAMP[3]], 0, 0, 1, 1))
    out = [panel(W, H, 22), f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#glow)"/>']
    badge = c["badge"].upper()
    out.append(f'<rect x="32" y="30" width="{T.width(badge, "mb", 12, 0.08) + 28:.1f}" height="28" rx="14" '
               f'fill="{acc}" fill-opacity="0.14" stroke="{acc}" stroke-opacity="0.65"/>')
    out.append(T.text(badge, 46, 49, "mb", 12, acc, tracking=0.08))
    y = 106
    for line in c["title"]:
        text, size = fit(T, line, "un", 30, 318, 22)
        out.append(T.text(text, 31, y, "un", size, INK["text"]))
        y += 38
    y += 2
    for line in c["lines"]:
        out.append(T.text(line, 33, y, "mo", 15, INK["muted"]))
        y += 23
    out.append(VIZ[c["viz"]](T, 364, 72, 204, 176, acc))
    x = 32
    for text, cat in c["tags"]:
        col = cats[cat][1]
        tw = T.width(text, "mo", 13) + 26
        out.append(f'<rect x="{x:.1f}" y="276" width="{tw:.1f}" height="32" rx="16" fill="{col}" '
                   f'fill-opacity="0.12" stroke="{col}" stroke-opacity="0.5"/>')
        out.append(T.text(text, x + 13, 297, "mo", 13, col))
        x += tw + 8
    desc = f'{" ".join(c["title"])}. {" ".join(c["lines"])}. Built with {", ".join(t for t, _ in c["tags"])}.'
    write(c["file"], svg(W, H, "".join(out), defs + T.defs(), title=" ".join(c["title"]), desc=desc))


# -------------------------------------------------------------------- stack

def stack(p):
    T = Typesetter()
    s = p["stack"]
    cats = s["categories"]
    TW, G, cols, Y = 112, 10, 9, 34
    X = (1200 - (cols * TW + (cols - 1) * G)) / 2
    W, H = 1200, Y * 2 + 3 * TW + 2 * G
    out = [panel(W, H)]
    for n, sym, name, cat, row, col in s["elements"]:
        c = cats[cat][1]
        x, y = X + (col - 1) * (TW + G), Y + (row - 1) * (TW + G)
        size = 12
        while T.width(name, "mo", size) > TW - 14 and size > 9:
            size -= 0.5
        out.append('<g>'
                   f'<rect x="{x:.1f}" y="{y}" width="{TW}" height="{TW}" rx="14" fill="{c}" fill-opacity="0.10" '
                   f'stroke="{c}" stroke-opacity="0.6" stroke-width="1.5"/>'
                   + T.text(str(n), x + 12, y + 22, "mo", 12, c)
                   + T.text(sym, x + TW / 2, y + 70, "un", 34, c, anchor="middle")
                   + T.text(name, x + TW / 2, y + 95, "mo", size, INK["muted"], anchor="middle") + "</g>")
    cx = (X + TW + G + X + 8 * (TW + G) - G) / 2
    out.append(T.text(s["title"], cx, Y + 54, "un", 28, INK["text"], anchor="middle"))
    items = list(cats.values())
    widths = [T.width(label, "mo", 13) + 18 for label, _ in items]
    lx = cx - (sum(widths) + 18 * (len(items) - 1)) / 2
    for (label, color), w in zip(items, widths):
        out.append(f'<circle cx="{lx + 5:.1f}" cy="{Y + 85}" r="5" fill="{color}"/>')
        out.append(T.text(label, lx + 16, Y + 90, "mo", 13, INK["muted"]))
        lx += w + 18
    desc = "Tools I use, laid out like a periodic table: " + ", ".join(e[2] for e in s["elements"]) + "."
    write("stack.svg", svg(W, H, "".join(out), T.defs(), "", s["title"], desc))


def main():
    with open(os.path.join(HERE, "profile.json"), encoding="utf-8") as fh:
        p = json.load(fh)
    with open(os.path.join(HERE, "dots.json"), encoding="utf-8") as fh:
        dots = json.load(fh)
    hero(p, dots)
    for b in p["buttons"]:
        button(b)
    for c in p["cards"]:
        card(c, p["stack"]["categories"])
    stack(p)


if __name__ == "__main__":
    main()
