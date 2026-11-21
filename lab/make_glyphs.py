"""Build lab/glyphs.json from the Computer Modern Unicode fonts.

You only need this if you want characters that glyphs.json does not have yet.
The figure scripts themselves use the JSON and need nothing but Python.

    pip install fonttools uharfbuzz
    python lab/make_glyphs.py path/to/cm-unicode/otf

Fonts: Computer Modern Unicode (CMU) by Andrey V. Panov, SIL Open Font License.
Download: https://ctan.org/pkg/cm-unicode
"""

import json
import os
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FACES = {
    "rm": "cmunrm.otf",  # Serif Roman
    "it": "cmunti.otf",  # Serif Italic
}

CHARSET = (
    "".join(chr(c) for c in range(32, 127))
    + "\u2018\u2019\u201c\u201d\u2026\u00d7\u00b7\u221a\u03bb\u03b8\u03b5\u03bc\u0109\u0177"
    + "\u2192\u2212\u00b0\u2248\u00b1\u2202\u03a3\u00e9\u2009"
)
LIGATURES = ["ffi", "ffl", "ff", "fi", "fl"]


def shape(font, text, features):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return buf.glyph_infos, buf.glyph_positions


def outline(glyphset, name):
    pen = SVGPathPen(glyphset, ntos=lambda n: str(round(n)))
    glyphset[name].draw(pen)
    return pen.getCommands()


def build_face(path):
    tt = TTFont(path)
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))
    upm = tt["head"].unitsPerEm
    font.scale = (upm, upm)
    cmap = tt.getBestCmap()
    glyphset = tt.getGlyphSet()
    hmtx = tt["hmtx"]
    order = tt.getGlyphOrder()

    glyphs, chars = {}, []
    for ch in CHARSET:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        glyphs[ch] = {"w": hmtx[gname][0], "d": outline(glyphset, gname)}
        chars.append(ch)

    ligatures = {}
    for lig in LIGATURES:
        infos, pos = shape(font, lig, {"liga": True, "kern": False})
        if len(infos) == 1:
            gname = order[infos[0].codepoint]
            glyphs[lig] = {"w": pos[0].x_advance, "d": outline(glyphset, gname)}
            ligatures[lig] = True

    kern = {}
    for a in chars:
        for b in chars:
            infos, pos = shape(font, a + b, {"liga": False, "kern": True})
            if len(infos) != 2:
                continue
            delta = pos[0].x_advance - glyphs[a]["w"]
            if delta:
                kern.setdefault(a, {})[b] = delta

    os2 = tt["OS/2"]
    return upm, {
        "ascender": os2.sTypoAscender,
        "descender": os2.sTypoDescender,
        "glyphs": glyphs,
        "ligatures": sorted(ligatures, key=len, reverse=True),
        "kern": kern,
    }


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "fonts"
    out = {"faces": {}}
    for key, filename in FACES.items():
        upm, face = build_face(os.path.join(src, filename))
        out["upm"] = upm
        out["faces"][key] = face
        print(f"{key}: {len(face['glyphs'])} glyphs, {sum(len(v) for v in face['kern'].values())} kerning pairs")
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphs.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {dest} ({os.path.getsize(dest) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
