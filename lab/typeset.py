"""Set text as vector outlines, so the figures look the same on every screen.

Letter shapes come from lab/glyphs.json (Unbounded and JetBrains Mono, SIL OFL).
Each glyph is stored once in <defs> and placed with <use>, which keeps files small.
Standard library only.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


class Typesetter:
    def __init__(self, path=os.path.join(HERE, "glyphs.json")):
        with open(path, encoding="utf-8") as fh:
            self.faces = json.load(fh)["faces"]
        self._used = {}

    def _tokens(self, text, face):
        f = self.faces[face]
        out, i = [], 0
        while i < len(text):
            for lig in f["ligatures"]:
                if text.startswith(lig, i):
                    out.append(lig)
                    i += len(lig)
                    break
            else:
                out.append(text[i] if text[i] in f["glyphs"] else "?")
                i += 1
        return out

    def layout(self, text, face="mo", size=16, tracking=0.0):
        """Glyph keys with x positions in font units, and the width in pixels."""
        f = self.faces[face]
        keys = self._tokens(text, face)
        placed, x = [], 0.0
        for i, key in enumerate(keys):
            placed.append((key, x))
            x += f["glyphs"][key]["w"]
            if i + 1 < len(keys):
                x += f["kern"].get(key, {}).get(keys[i + 1], 0) + tracking * f["upm"]
        return placed, x * size / f["upm"]

    def width(self, text, face="mo", size=16, tracking=0.0):
        return self.layout(text, face, size, tracking)[1]

    def _glyph_id(self, face, key):
        gid = f"{face}-" + "-".join(f"{ord(c):x}" for c in key)
        self._used.setdefault(gid, self.faces[face]["glyphs"][key]["d"])
        return gid

    def text(self, text, x, y, face="mo", size=16, fill="currentColor",
             anchor="start", tracking=0.0, attrs=""):
        """An SVG group drawing `text` with its baseline at (x, y)."""
        placed, w = self.layout(text, face, size, tracking)
        x -= {"middle": w / 2, "end": w}.get(anchor, 0)
        s = size / self.faces[face]["upm"]
        glyphs = self.faces[face]["glyphs"]
        uses = "".join(f'<use xlink:href="#{self._glyph_id(face, k)}" x="{gx:.0f}"/>'
                       for k, gx in placed if glyphs[k]["d"])
        return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.5f} {-s:.5f})" '
                f'fill="{fill}"{attrs}>{uses}</g>')

    def defs(self):
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._used.items())
