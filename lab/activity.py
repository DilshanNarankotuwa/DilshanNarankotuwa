"""Draw assets/activity.svg: Fig. 2 of the profile.

Weekly GitHub contributions for the last 52 weeks, drawn like a spectrum:
raw weekly counts as sticks, a Savitzky-Golay smoothed curve on top, and a
small table of measurements beside the plot.

Data comes from the GraphQL API when GITHUB_TOKEN is set (as it is inside
GitHub Actions) and from the public contribution calendar page otherwise.
If nothing can be fetched, the existing figure is left untouched.

Standard library only:  python lab/activity.py
"""

import datetime as dt
import json
import math
import os
import re
import sys
import urllib.request
from collections import Counter

from typeset import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEST = os.path.join(ROOT, "assets", "activity.svg")

INK = {
    "midnight": "#0E1524",
    "edge": "#1C2840",
    "paper": "#E8EDF4",
    "graphite": "#93A1B5",
    "rule": "#33415C",
    "grid": "#1E2A41",
    "signal": "#5ED1C4",
}
W, H = 1200, 400
PLOT = (100, 140, 860, 336)          # x0, y_top, x1, y_base
TABLE_X = (904, 1144)
WEEKS = 52
SG_KERNEL = [-3, 12, 17, 12, -3]     # Savitzky-Golay, window 5, quadratic
SG_NORM = 35
UA = {"User-Agent": "profile-figures (github.com)"}


# ----------------------------------------------------------------- fetching

def http(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def calendar_graphql(user, token):
    query = """query($login: String!) { user(login: $login) { contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""
    body = json.dumps({"query": query, "variables": {"login": user}}).encode()
    raw = http("https://api.github.com/graphql", body,
               {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    weeks = json.loads(raw)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def calendar_html(user):
    page = http(f"https://github.com/users/{user}/contributions")
    tips = dict(re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page))
    days = {}
    for cell in re.findall(r"<td\b[^>]*\bdata-date=[^>]*>", page):
        date = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', cell)
        if not date:
            continue
        count = re.search(r'data-count="(\d+)"', cell)
        if count is None:
            cid = re.search(r'\bid="([^"]+)"', cell)
            text = tips.get(cid.group(1), "") if cid else ""
            count = re.match(r"\s*(\d+)\s+contribution", text)
        days[date.group(1)] = int(count.group(1)) if count else 0
    if not days:
        raise ValueError("calendar page had no day cells")
    return days


def latest_push(user, token):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    events = json.loads(http(f"https://api.github.com/users/{user}/events/public?per_page=50", headers=headers))
    return pick_push(events, user)


def pick_push(events, user):
    """Most recent push to a repository other than the profile repository itself."""
    for ev in events:
        repo = ev.get("repo", {}).get("name", "")
        owner, _, name = repo.partition("/")
        if ev.get("type") == "PushEvent" and name.lower() != user.lower():
            when = dt.datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
            return (name if owner.lower() == user.lower() else repo), when
    return None


# ---------------------------------------------------------------- measuring

def measure(days, today):
    dates = sorted(d for d in days if dt.date.fromisoformat(d) <= today)
    total = sum(days[d] for d in dates)
    active = sum(1 for d in dates if days[d] > 0)
    longest = run = 0
    for d in dates:
        run = run + 1 if days[d] else 0
        longest = max(longest, run)
    weekday = Counter()
    for d in dates:
        weekday[dt.date.fromisoformat(d).strftime("%A")] += days[d]
    top = max(weekday.values()) if weekday else 0
    busiest = [name for name in ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
               if top and weekday[name] == top]
    # Weeks start on Sunday, like the calendar on a GitHub profile
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7) - dt.timedelta(weeks=WEEKS - 1)
    weekly = [0] * WEEKS
    for d in dates:
        i = (dt.date.fromisoformat(d) - start).days // 7
        if 0 <= i < WEEKS:
            weekly[i] += days[d]
    return {"total": total, "active": active, "longest": longest, "busiest": busiest,
            "weekly": weekly, "start": start}


def savitzky_golay(values):
    padded = values[2:0:-1] + values + values[-2:-4:-1]
    return [max(0.0, sum(k * padded[i + j] for j, k in enumerate(SG_KERNEL)) / SG_NORM)
            for i in range(len(values))]


# ------------------------------------------------------------------ drawing

def nice_ceiling(v):
    for step in (5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
        if v <= step:
            return step
    return math.ceil(v / 10000) * 10000


def smooth_path(points, floor, ceiling):
    """Catmull-Rom spline through points, kept between the baseline and the top."""
    clamp = lambda y: min(floor, max(ceiling, y))
    p = [points[0]] + points + [points[-1]]
    d = f"M{p[1][0]:.1f} {p[1][1]:.1f}"
    for i in range(1, len(p) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (x1 + (x2 - x0) / 6, clamp(y1 + (y2 - y0) / 6))
        c2 = (x2 - (x3 - x1) / 6, clamp(y2 - (y3 - y1) / 6))
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {x2:.1f} {y2:.1f}"
    return d


def ago(when, now):
    days = (now - when).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{days // 7} weeks ago"
    return f"{days // 30} months ago"


def fit(T, text, face, size, max_w, min_size=14):
    while size > min_size and T.width(text, face, size) > max_w:
        size -= 1
    while T.width(text, face, size) > max_w and len(text) > 2:
        text = text[:-2] + "\u2026"
    return text, size


def draw(m, push, now):
    T = Typesetter()
    x0, top, x1, base = PLOT
    h = base - top
    weekly, smooth = m["weekly"], savitzky_golay(m["weekly"])
    vmax = nice_ceiling(max(weekly + [1]))
    to_y = lambda v: base - math.sqrt(max(v, 0) / vmax) * h
    step = (x1 - x0) / WEEKS
    to_x = lambda i: x0 + (i + 0.5) * step
    out = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" '
           f'fill="{INK["midnight"]}" stroke="{INK["edge"]}"/>']

    out.append(T.text("Contribution spectrum", 56, 70, "rm", 30, INK["paper"]))
    out.append(T.text("Weekly contributions over the last 52 weeks, smoothed with a Savitzky-Golay filter",
                      57, 99, "it", 18, INK["graphite"]))
    out.append(T.text(f"redrawn {now.day} {now:%B %Y}", TABLE_X[1], 70, "it", 17, INK["graphite"], anchor="end"))

    # Square-root axis: quiet weeks stay visible next to busy ones
    ticks, last_y = [], None
    for v in [vmax] + [c for c in (500, 200, 100, 50, 20, 10, 5, 2, 1) if c < vmax] + [0]:
        y = to_y(v)
        if last_y is None or y - last_y >= 30 or v == 0:
            if v == 0 and ticks and y - to_y(ticks[-1]) < 30:
                ticks.pop()
            ticks.append(v)
            last_y = y
    for v in ticks:
        y = to_y(v)
        if v:
            out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{INK["grid"]}" stroke-width="1"/>')
        out.append(T.text(str(v), x0 - 14, y + 5, "rm", 16, INK["graphite"], anchor="end"))
    out.append(f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="{INK["rule"]}" stroke-width="1"/>')

    # Months along the bottom
    for i in range(WEEKS):
        week = m["start"] + dt.timedelta(weeks=i)
        firsts = [week + dt.timedelta(days=k) for k in range(7) if (week + dt.timedelta(days=k)).day == 1]
        if firsts and to_x(i) > x0 + 10:
            label = firsts[0].strftime("%b %Y" if firsts[0].month == 1 else "%b")
            out.append(T.text(label, to_x(i), base + 27, "rm", 16, INK["graphite"], anchor="middle"))

    # Raw weekly counts as sticks, smoothed curve and its shadow on top
    for i, v in enumerate(weekly):
        if v:
            out.append(f'<line x1="{to_x(i):.1f}" y1="{base}" x2="{to_x(i):.1f}" y2="{to_y(v):.1f}" '
                       f'stroke="{INK["paper"]}" stroke-opacity="0.45" stroke-width="2.2" stroke-linecap="round"/>')
    pts = [(to_x(i), to_y(v)) for i, v in enumerate(smooth)]
    curve = smooth_path(pts, base, top)
    out.append(f'<path d="{curve} L{pts[-1][0]:.1f} {base} L{pts[0][0]:.1f} {base} Z" fill="url(#shade)"/>')
    out.append(f'<path d="{curve}" fill="none" stroke="{INK["signal"]}" stroke-width="2.4" stroke-linejoin="round"/>')

    peak = max(range(WEEKS), key=lambda i: weekly[i])
    if weekly[peak]:
        px = min(max(to_x(peak), x0 + 12), x1 - 12)
        out.append(T.text(str(weekly[peak]), px, to_y(weekly[peak]) - 10, "rm", 17, INK["paper"], anchor="middle"))

    # Measurements
    rows = [("contributions", f"{m['total']:,}"),
            ("active days", f"{m['active']}"),
            ("longest streak", f"{m['longest']} day" + ("s" if m["longest"] != 1 else "")),
            ("busiest day", " & ".join(d[:3] for d in m["busiest"]) if len(m["busiest"]) > 1
             else (m["busiest"][0] if m["busiest"] else "none yet"))]
    if push:
        repo, when = push
        rows += [("latest push", repo), ("pushed", ago(when, now))]
    y = 158 if len(rows) > 4 else 186
    for key, value in rows:
        key_w = T.width(key, "it", 18)
        value, size = fit(T, value, "rm", 24, TABLE_X[1] - TABLE_X[0] - key_w - 16)
        out.append(T.text(key, TABLE_X[0], y, "it", 18, INK["graphite"]))
        out.append(T.text(value, TABLE_X[1], y, "rm", size, INK["paper"], anchor="end"))
        y += 36

    defs = (f'<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{INK["signal"]}" stop-opacity="0.22"/>'
            f'<stop offset="1" stop-color="{INK["signal"]}" stop-opacity="0"/></linearGradient>' + T.defs())
    desc = (f"Weekly GitHub contributions over the last 52 weeks, with a smoothed curve. "
            f"{m['total']} contributions on {m['active']} days; longest streak {m['longest']} days.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">'
            f'<title id="title">Contribution spectrum</title><desc id="desc">{desc}</desc>'
            f'<defs>{defs}</defs>{"".join(out)}</svg>\n')


def main():
    with open(os.path.join(HERE, "identity.json"), encoding="utf-8") as fh:
        user = json.load(fh)["username"]
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    now = dt.datetime.now(dt.timezone.utc)

    days = None
    sources = ([("GraphQL API", lambda: calendar_graphql(user, token))] if token else []) + \
              [("calendar page", lambda: calendar_html(user))]
    for name, fetch in sources:
        try:
            days = fetch()
            print(f"calendar: {len(days)} days from the {name}")
            break
        except Exception as exc:
            print(f"calendar: {name} failed ({exc})", file=sys.stderr)
    if not days:
        print("No contribution data; keeping the current figure.", file=sys.stderr)
        return

    try:
        push = latest_push(user, token)
    except Exception as exc:
        print(f"latest push: skipped ({exc})", file=sys.stderr)
        push = None

    svg = draw(measure(days, now.date()), push, now)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"activity.svg written ({len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
