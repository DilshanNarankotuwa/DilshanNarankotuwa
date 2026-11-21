# lab

The figures on my profile are drawn here with plain Python. Nothing to install.

| File | What it does |
|---|---|
| `profile.json` | All the text: headline, experience, projects and skills. Edit this. |
| `build.py` | Draws the hero, buttons, experience, project cards and skills into `assets/`. |
| `activity.py` | Draws `assets/activity.svg` from my contribution calendar. |
| `typeset.py` | Turns text into vector shapes, so the figures look the same on every screen. |
| `glyphs.json` | Letter shapes for Manrope and JetBrains Mono. |
| `make_fonts.py` | Rebuilds `glyphs.json`. Only needed for new characters. |
| `fonts/` | Font licenses (SIL Open Font License). |

The GitHub Action in `.github/workflows/redraw.yml` runs `build.py` and `activity.py` every morning, and whenever something in `lab/` changes.
