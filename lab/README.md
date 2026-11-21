# lab

Every figure on my profile is drawn here with plain Python. Nothing to install.

| File | What it does |
|---|---|
| `profile.json` | All the text: name, title, buttons, project cards and the stack. Edit this. |
| `build.py` | Draws the hero, buttons, cards and stack into `assets/`. |
| `activity.py` | Draws `assets/activity.svg` from my contribution calendar. |
| `typeset.py` | Turns text into vector shapes, so the figures look the same on every screen. |
| `glyphs.json`, `dots.json` | Letter shapes, and the dots that spell my name. |
| `make_fonts.py` | Rebuilds those two files. Only needed if the name lines change. |
| `fonts/` | Licenses for Unbounded and JetBrains Mono (SIL Open Font License). |

## Run it yourself

```
python lab/build.py
python lab/activity.py
```

The GitHub Action in `.github/workflows/redraw.yml` runs both every morning, and whenever something in `lab/` changes.

To change the dotted name, edit `name_lines` in `profile.json`, then run:

```
pip install fonttools uharfbuzz pillow
python lab/make_fonts.py
python lab/build.py
```
