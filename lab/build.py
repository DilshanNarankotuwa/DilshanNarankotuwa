"""Draw the static figures in assets/: hero, contact buttons, experience,
project cards and skills.

All text lives in lab/profile.json. Standard library only:  python lab/build.py
"""

import json
import math
import os
import random

from typeset import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

INK = {"bg": "#0E131C", "panel": "#131A26", "edge": "#222C3D", "line": "#1A2231",
       "grid": "#1A2231", "text": "#F1F5F9", "soft": "#CBD5E1", "muted": "#94A3B8", "dim": "#64748B",
       "accent": "#60A5FA"}
ACC_A, ACC_B, WARM = "#3B82F6", "#22D3EE", "#F59E0B"


# ------------------------------------------------------------------ helpers

def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(t):
    """The single accent: blue to cyan."""
    return mix(ACC_A, ACC_B, min(1.0, max(0.0, t)))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w, h, body, defs="", style="", title="", desc=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            + (f"<style>{style}</style>" if style else "") + f"<defs>{defs}</defs>{body}</svg>\n")


def panel(w, h, r=20):
    return (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" '
            f'fill="{INK["bg"]}" stroke="{INK["edge"]}" stroke-width="1.5"/>')


ACCENT_DEF = (f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">'
              f'<stop offset="0" stop-color="{ACC_A}"/><stop offset="1" stop-color="{ACC_B}"/></linearGradient>')


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


def pills(T, tags, x, y, max_x):
    out = []
    for tag in tags:
        w = T.width(tag, "mo", 13) + 26
        if x + w > max_x:
            break
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="30" rx="15" '
                   f'fill="{INK["line"]}" stroke="{INK["edge"]}"/>'
                   + T.text(tag, x + 13, y + 20, "mo", 13, INK["soft"]))
        x += w + 8
    return "".join(out)


# --------------------------------------------------------------------- hero

def boundary_plot(x0, y0, w, h):
    """Two classes and the curved decision boundary a classifier learned."""
    rng = random.Random(4)
    px0, py0, px1, py1 = x0 + 22, y0 + 22, x0 + w - 22, y0 + h - 22
    sx = lambda u: px0 + u * (px1 - px0)
    sy = lambda v: py1 - v * (py1 - py0)
    edge = lambda u: 0.52 + 0.22 * math.sin(3.1 * u - 0.6) - 0.12 * u
    curve = [(sx(i / 60), sy(edge(i / 60))) for i in range(61)]
    line = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in curve)
    out = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="16" fill="{INK["panel"]}" stroke="{INK["edge"]}"/>',
           f'<path d="{line} L{px1} {py0} L{px0} {py0} Z" fill="{WARM}" fill-opacity="0.07"/>',
           f'<path d="{line} L{px1} {py1} L{px0} {py1} Z" fill="{ACC_A}" fill-opacity="0.08"/>']
    for i in range(1, 4):
        gx, gy = px0 + (px1 - px0) * i / 4, py0 + (py1 - py0) * i / 4
        out.append(f'<line x1="{gx:.1f}" y1="{py0}" x2="{gx:.1f}" y2="{py1}" stroke="{INK["line"]}"/>'
                   f'<line x1="{px0}" y1="{gy:.1f}" x2="{px1}" y2="{gy:.1f}" stroke="{INK["line"]}"/>')
    dots = 0
    while dots < 110:
        u, v = rng.uniform(0.03, 0.97), rng.uniform(0.04, 0.96)
        gap = v - edge(u)
        if abs(gap) < 0.05:
            continue
        above = gap > 0
        if rng.random() < 0.04:
            above = not above
        color = WARM if above else ACC_B
        out.append(f'<circle cx="{sx(u):.1f}" cy="{sy(v):.1f}" r="4.2" fill="{color}" fill-opacity="0.9"/>')
        dots += 1
    out.append(f'<path d="{line}" fill="none" stroke="{INK["text"]}" stroke-width="2.2" '
               f'stroke-dasharray="7 6" stroke-linecap="round"/>')
    return "".join(out)


def hero(p):
    T = Typesetter()
    W, H = 1200, 420
    out = [panel(W, H), f'<rect x="64" y="70" width="56" height="4" rx="2" fill="url(#acc)"/>']
    name, size = fit(T, p["name"], "hx", 58, 640)
    out.append(T.text(name, 62, 148, "hx", size, INK["text"], tracking=-0.01))
    out.append(T.text(p["title"], 64, 196, "hd", 28, INK["accent"]))
    out.append(T.text(p["statement"], 64, 236, "hm", 19, INK["muted"]))
    out.append(f'<line x1="64" y1="284" x2="700" y2="284" stroke="{INK["edge"]}"/>')
    for i, (label, value) in enumerate(p["facts"]):
        x = 64 + i * 330
        value, vs = fit(T, value, "hd", 17, 310)
        out.append(T.text(label, x, 322, "mo", 12, INK["dim"], tracking=0.08))
        out.append(T.text(value, x, 350, "hd", vs, INK["text"]))
    out.append(boundary_plot(780, 56, 360, 308))
    desc = f'{p["name"]}, {p["title"]}. {p["statement"]} ' + " ".join(f"{a.title()}: {b}." for a, b in p["facts"])
    write("hero.svg", svg(W, H, "".join(out), ACCENT_DEF + T.defs(), title=p["name"], desc=desc))


# ------------------------------------------------------------------ buttons

ICONS = {
    "mail": '<rect x="-10" y="-7.5" width="20" height="15" rx="2.5"/><path d="M-9 -5.5 L0 1.5 L9 -5.5"/>',
    "linkedin": '<rect x="-10" y="-10" width="20" height="20" rx="4.5"/>'
                '<path d="M-5 -1.5 V5.5 M-5 -5 V-4.8 M-0.5 5.5 V-1.5 M-0.5 2 C-0.5 -2.2 5 -2.6 5 1.5 V5.5"/>',
    "web": '<circle r="10"/><ellipse rx="4.2" ry="10"/><path d="M-10 0 H10"/>',
}


def button(b):
    T = Typesetter()
    h = 56
    w = round(h + T.width(b["label"], "hd", 18) + 26)
    body = (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{INK["panel"]}" '
            f'stroke="{INK["edge"]}" stroke-width="1.5"/>'
            f'<g transform="translate({h / 2 + 2} {h / 2})" fill="none" stroke="{INK["accent"]}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[b["icon"]]}</g>'
            + T.text(b["label"], h + 2, h / 2 + 6.5, "hd", 18, INK["text"]))
    write(b["file"], svg(w, h, body, T.defs(), title=b["label"], desc=b["label"]))


# --------------------------------------------------------------- experience

def experience(e):
    T = Typesetter()
    W, H = 1200, 290
    out = [panel(W, H), f'<rect x="48" y="48" width="40" height="4" rx="2" fill="url(#acc)"/>',
           T.text(e["company"], 48, 96, "hx", 32, INK["text"]),
           T.text(e["role"], 48, 128, "hd", 19, INK["accent"]),
           T.text(e["period"], 48, 156, "mo", 13, INK["dim"]),
           f'<line x1="420" y1="48" x2="420" y2="182" stroke="{INK["edge"]}"/>']
    for i, point in enumerate(e["points"]):
        y = 82 + i * 44
        text, size = fit(T, point, "hm", 18, 680)
        out.append(f'<circle cx="460" cy="{y - 6}" r="4" fill="url(#acc)"/>')
        out.append(T.text(text, 478, y, "hm", size, INK["soft"]))
    out.append(f'<line x1="48" y1="210" x2="{W - 48}" y2="210" stroke="{INK["line"]}"/>')
    out.append(pills(T, e["tags"], 48, 228, W - 48))
    desc = f'{e["role"]} at {e["company"]}, {e["period"]}. ' + " ".join(pt + "." for pt in e["points"])
    write("experience.svg", svg(W, H, "".join(out), ACCENT_DEF + T.defs(), title=e["company"], desc=desc))


# ---------------------------------------------------------------- projects

def project(c):
    T = Typesetter()
    W, H = 600, 290
    out = [panel(W, H, 18), f'<rect x="36" y="36" width="40" height="4" rx="2" fill="url(#acc)"/>',
           T.text(c["category"], 36, 68, "mo", 12, INK["dim"], tracking=0.08)]
    title, ts = fit(T, c["title"], "hd", 27, 360)
    out.append(T.text(title, 36, 110, "hd", ts, INK["text"]))
    for i, line in enumerate(c["lines"]):
        out.append(T.text(line, 36, 148 + i * 25, "hm", 16, INK["muted"]))
    metric, ms = fit(T, c["metric"], "hx", 30, 170)
    out.append(T.text(metric, W - 36, 84, "hx", ms, INK["accent"], anchor="end"))
    out.append(T.text(c["metric_label"], W - 36, 108, "mo", 12, INK["dim"], anchor="end"))
    out.append(pills(T, c["tags"], 36, 222, W - 36))
    desc = f'{c["title"]}: {" ".join(c["lines"])} {c["metric"]} {c["metric_label"]}. Built with {", ".join(c["tags"])}.'
    write(c["file"], svg(W, H, "".join(out), ACCENT_DEF + T.defs(), title=c["title"], desc=desc))


# ------------------------------------------------------------------ skills

def skills(groups):
    T = Typesetter()
    W = 1200
    rows = max(len(items) for _, items in groups)
    H = 120 + rows * 32
    col = (W - 96) / len(groups)
    out = [panel(W, H)]
    for i, (head, items) in enumerate(groups):
        x = 48 + i * col
        if i:
            out.append(f'<line x1="{x - 18:.1f}" y1="44" x2="{x - 18:.1f}" y2="{H - 40}" stroke="{INK["line"]}"/>')
        out.append(f'<rect x="{x:.1f}" y="44" width="28" height="4" rx="2" fill="url(#acc)"/>')
        head, hs = fit(T, head, "hd", 17, col - 30)
        out.append(T.text(head, x, 80, "hd", hs, INK["accent"]))
        for j, item in enumerate(items):
            out.append(T.text(item, x, 118 + j * 32, "hm", 16, INK["soft"]))
    desc = " ".join(f"{h}: {', '.join(items)}." for h, items in groups)
    write("skills.svg", svg(W, H, "".join(out), ACCENT_DEF + T.defs(), title="Skills", desc=desc))


def main():
    with open(os.path.join(HERE, "profile.json"), encoding="utf-8") as fh:
        p = json.load(fh)
    hero(p)
    for b in p["buttons"]:
        button(b)
    experience(p["experience"])
    for c in p["projects"]:
        project(c)
    skills(p["skills"])


if __name__ == "__main__":
    main()
