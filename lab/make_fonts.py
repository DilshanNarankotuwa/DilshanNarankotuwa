"""Rebuild lab/glyphs.json, the letter shapes the figures are drawn with.

Only needed if you want characters that glyphs.json does not have yet.

    pip install fonttools uharfbuzz
    python lab/make_fonts.py

Fonts are downloaded from the Google Fonts repository into lab/fonts/:
Manrope and JetBrains Mono, both SIL Open Font License 1.1.
"""

import io
import json
import os
import urllib.request

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
GOOGLE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
SOURCES = {
    "Manrope[wght].ttf": GOOGLE + "manrope/Manrope%5Bwght%5D.ttf",
    "JetBrainsMono[wght].ttf": GOOGLE + "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
FACES = {
    "hx": ("Manrope[wght].ttf", 800),
    "hd": ("Manrope[wght].ttf", 700),
    "hm": ("Manrope[wght].ttf", 500),
    "mo": ("JetBrainsMono[wght].ttf", 400),
    "mb": ("JetBrainsMono[wght].ttf", 700),
}
CHARSET = "".join(chr(c) for c in range(32, 127)) + "\u00b7\u2022\u2192\u00d7\u00b2\u2019\u2026\u2212\u2713"


def font_file(name):
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        with urllib.request.urlopen(SOURCES[name], timeout=60) as resp:
            data = resp.read()
        with open(path, "wb") as fh:
            fh.write(data)
    return path


def build_face(name, weight):
    font = instancer.instantiateVariableFont(TTFont(font_file(name)), {"wght": weight})
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    tt = TTFont(io.BytesIO(data))
    shaper = hb.Font(hb.Face(data))
    upm = tt["head"].unitsPerEm
    shaper.scale = (upm, upm)
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
            hbuf = hb.Buffer()
            hbuf.add_str(a + b)
            hbuf.guess_segment_properties()
            hb.shape(shaper, hbuf, {"liga": False, "calt": False, "kern": True})
            if len(hbuf.glyph_infos) == 2:
                delta = hbuf.glyph_positions[0].x_advance - glyphs[a]["w"]
                if delta:
                    kern.setdefault(a, {})[b] = delta
    return {"upm": upm, "glyphs": glyphs, "ligatures": [], "kern": kern}


def main():
    faces = {key: build_face(*spec) for key, spec in FACES.items()}
    with open(os.path.join(HERE, "glyphs.json"), "w", encoding="utf-8") as fh:
        json.dump({"faces": faces}, fh, ensure_ascii=False, separators=(",", ":"))
    for key, face in faces.items():
        print(f"{key}: {len(face['glyphs'])} glyphs, upm {face['upm']}")


if __name__ == "__main__":
    main()
