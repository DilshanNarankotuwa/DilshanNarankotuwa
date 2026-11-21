"""Rebuild lab/glyphs.json (letter shapes) and lab/dots.json (the dotted name).

Only needed after changing "name_lines" in lab/profile.json, or to add characters.

    pip install fonttools uharfbuzz pillow
    python lab/make_fonts.py

Fonts are downloaded from the Google Fonts repository into lab/fonts/:
Unbounded (NaN) and JetBrains Mono (JetBrains), both SIL Open Font License 1.1.
"""

import io
import json
import os
import urllib.request

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
GOOGLE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
SOURCES = {
    "Unbounded[wght].ttf": GOOGLE + "unbounded/Unbounded%5Bwght%5D.ttf",
    "JetBrainsMono[wght].ttf": GOOGLE + "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
FACES = {
    "un": ("Unbounded[wght].ttf", 700),
    "mo": ("JetBrainsMono[wght].ttf", 400),
    "mb": ("JetBrainsMono[wght].ttf", 700),
}
DOT_FACE = ("Unbounded[wght].ttf", 800)
CHARSET = "".join(chr(c) for c in range(32, 127)) + "\u00b7\u2022\u2192\u00d7\u00b2\u2019\u2026\u2212\u0177\u2605\u2713"


def font_file(name):
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        with urllib.request.urlopen(SOURCES[name], timeout=60) as resp:
            data = resp.read()
        with open(path, "wb") as fh:
            fh.write(data)
    return path


def static_instance(name, weight):
    font = instancer.instantiateVariableFont(TTFont(font_file(name)), {"wght": weight})
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    return TTFont(io.BytesIO(data)), data


def build_face(name, weight):
    tt, data = static_instance(name, weight)
    font = hb.Font(hb.Face(data))
    upm = tt["head"].unitsPerEm
    font.scale = (upm, upm)
    cmap, glyphset, hmtx = tt.getBestCmap(), tt.getGlyphSet(), tt["hmtx"]
    glyphs, chars = {}, []
    for ch in CHARSET:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        pen = SVGPathPen(glyphset, ntos=lambda n: str(round(n)))
        glyphset[gname].draw(pen)
        glyphs[ch] = {"w": hmtx[gname][0], "d": pen.getCommands()}
        chars.append(ch)
    kern = {}
    for a in chars:
        for b in chars:
            buf = hb.Buffer()
            buf.add_str(a + b)
            buf.guess_segment_properties()
            hb.shape(font, buf, {"liga": False, "calt": False, "kern": True})
            if len(buf.glyph_infos) == 2:
                delta = buf.glyph_positions[0].x_advance - glyphs[a]["w"]
                if delta:
                    kern.setdefault(a, {})[b] = delta
    return {"upm": upm, "glyphs": glyphs, "ligatures": [], "kern": kern}


def dotted_lines(lines, spacing, max_width):
    """Sample each line of the name on a triangular grid of dots."""
    _, data = static_instance(*DOT_FACE)
    k = 4  # supersampling factor
    out = []
    for spec in lines:
        size = spec["size"]
        for _ in range(2):
            font = ImageFont.truetype(io.BytesIO(data), round(size * k))
            left, top, right, bottom = font.getbbox(spec["text"])
            if (right - left) / k <= max_width:
                break
            size *= max_width / ((right - left) / k)
        pad = 8 * k
        img = Image.new("L", (right - left + 2 * pad, bottom - top + 2 * pad), 0)
        ImageDraw.Draw(img).text((pad - left, pad - top), spec["text"], font=font, fill=255)
        step, row_h = spacing * k, spacing * k * 0.866
        points, row, y = [], 0, row_h / 2
        while y < img.height:
            x = step / 2 + (step / 2 if row % 2 else 0)
            while x < img.width:
                if img.getpixel((int(x), int(y))) > 150:
                    points.append([round((x - pad) / k, 1), round((y - pad) / k, 1)])
                x += step
            y += row_h
            row += 1
        out.append({"text": spec["text"], "size": round(size, 1), "width": round((right - left) / k, 1),
                    "height": round((bottom - top) / k, 1), "points": points})
    return out


def main():
    with open(os.path.join(HERE, "profile.json"), encoding="utf-8") as fh:
        profile = json.load(fh)
    faces = {key: build_face(*spec) for key, spec in FACES.items()}
    with open(os.path.join(HERE, "glyphs.json"), "w", encoding="utf-8") as fh:
        json.dump({"faces": faces}, fh, ensure_ascii=False, separators=(",", ":"))
    lines = dotted_lines(profile["name_lines"], profile["dot_spacing"], profile["dot_max_width"])
    with open(os.path.join(HERE, "dots.json"), "w", encoding="utf-8") as fh:
        json.dump({"lines": lines}, fh, separators=(",", ":"))
    for key, face in faces.items():
        print(f"{key}: {len(face['glyphs'])} glyphs, upm {face['upm']}")
    print("dots:", ", ".join(f"{l['text']} {len(l['points'])} (size {l['size']})" for l in lines))


if __name__ == "__main__":
    main()
