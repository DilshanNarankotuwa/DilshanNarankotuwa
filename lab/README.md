# lab

The two figures on my profile are drawn here by plain Python. Nothing to install.

| File | What it does |
|---|---|
| `identity.json` | Name, tagline and the three stage labels in Fig. 1. Edit this to change the hero text. |
| `hero.py` | Draws `assets/hero.svg` (Fig. 1): an illustrative near-infrared spectrum, sampled at seven wavelengths, standardized with SNV and read by a small network. |
| `activity.py` | Draws `assets/activity.svg` (Fig. 2): weekly contributions from the GitHub contribution calendar, smoothed with a Savitzky-Golay filter (window 5, quadratic). |
| `typeset.py` | Places text as vector outlines, so the figures look the same on every screen. |
| `glyphs.json` | Letter shapes, kerning and ligatures for CMU Serif Roman and Italic. |
| `make_glyphs.py` | Rebuilds `glyphs.json` from the font files. Only needed if you want new characters. |
| `fonts/OFL.txt` | License for the Computer Modern Unicode fonts. |

## Run it yourself

```
python lab/hero.py
python lab/activity.py
```

`activity.py` uses the GitHub GraphQL API when `GITHUB_TOKEN` is set, and the public contribution calendar page when it is not. If neither works, it leaves the current figure alone.

The workflow in `.github/workflows/redraw.yml` runs both scripts every morning and commits the figures when they change. It also runs whenever something in `lab/` changes.

## Fonts

The figures are set in CMU Serif (Computer Modern Unicode) by Andrey V. Panov, after Donald Knuth's Computer Modern. `glyphs.json` holds outlines derived from those fonts and is distributed under the SIL Open Font License 1.1, included as `fonts/OFL.txt`.
