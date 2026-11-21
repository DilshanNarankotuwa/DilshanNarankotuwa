"""Set text as vector outlines, so figures look the same on every screen.

Glyph outlines come from lab/glyphs.json (Computer Modern Unicode, SIL OFL).
Each glyph is stored once in <defs> and placed with <use>, which keeps files small.
Standard library only.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


class Typesetter:
    def __init__(self, path=os.path.join(HERE, "glyphs.json")):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.upm = data["upm"]
        self.faces = data["faces"]
        self._used = {}

    def _tokens(self, text, face):
        """Split text into glyph keys, using ligatures where the face has them."""
        f = self.faces[face]
        ligatures, glyphs = f["ligatures"], f["glyphs"]
        out, i = [], 0
        while i < len(text):
            for lig in ligatures:
                if text.startswith(lig, i):
                    out.append(lig)
                    i += len(lig)
                    break
            else:
                ch = text[i]
                out.append(ch if ch in glyphs else "?")
                i += 1
        return out

    def layout(self, text, face="rm", size=16, tracking=0.0):
        """Return [(glyph key, x in font units)] and the width in pixels."""
        f = self.faces[face]
        glyphs, kern = f["glyphs"], f["kern"]
        keys = self._tokens(text, face)
        placed, x = [], 0.0
        for i, key in enumerate(keys):
            placed.append((key, x))
            x += glyphs[key]["w"]
            if i + 1 < len(keys):
                x += kern.get(key, {}).get(keys[i + 1], 0) + tracking * self.upm
        return placed, x * size / self.upm

    def width(self, text, face="rm", size=16, tracking=0.0):
        return self.layout(text, face, size, tracking)[1]

    def _glyph_id(self, face, key):
        gid = f"{face}-" + "-".join(f"{ord(c):x}" for c in key)
        if gid not in self._used:
            self._used[gid] = self.faces[face]["glyphs"][key]["d"]
        return gid

    def text(self, text, x, y, face="rm", size=16, fill="currentColor",
             anchor="start", tracking=0.0, attrs=""):
        """An SVG group that draws `text` with its baseline at (x, y)."""
        placed, w = self.layout(text, face, size, tracking)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upm
        uses = "".join(
            f'<use xlink:href="#{self._glyph_id(face, key)}" x="{gx:.0f}"/>'
            for key, gx in placed
            if key != " " and self.faces[face]["glyphs"][key]["d"]
        )
        return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.5f} {-s:.5f})" '
                f'fill="{fill}"{attrs}>{uses}</g>')

    def defs(self):
        """Every glyph used so far, ready to drop inside <defs>."""
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._used.items())
