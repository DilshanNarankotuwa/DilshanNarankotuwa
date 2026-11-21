"""Draw assets/activity.svg: GitHub activity for the last 52 weeks.

Weekly contributions as colored bars, a smoothed trend line (Savitzky-Golay,
window 5, quadratic) and four totals. Data comes from the GraphQL API when
GITHUB_TOKEN is set (as it is in GitHub Actions) and from the public
contribution calendar otherwise. If nothing can be fetched, the current
figure stays as it is.

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

from build import INK, fit, panel, ramp, svg, write
from typeset import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
WEEKS = 52
SG_KERNEL, SG_NORM = [-3, 12, 17, 12, -3], 35
UA = {"User-Agent": "profile-figures (github.com)"}
DAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


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
            count = re.match(r"\s*(\d+)\s+contribution", tips.get(cid.group(1), "") if cid else "")
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
    """Most recent push to a repository other than this profile repository."""
    for ev in events:
        owner, _, name = ev.get("repo", {}).get("name", "").partition("/")
        if ev.get("type") == "PushEvent" and name.lower() != user.lower():
            when = dt.datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
            return (name if owner.lower() == user.lower() else f"{owner}/{name}"), when
    return None


# ---------------------------------------------------------------- measuring

def measure(days, today):
    dates = sorted(d for d in days if dt.date.fromisoformat(d) <= today)
    longest = run = 0
    weekday = Counter()
    for d in dates:
        run = run + 1 if days[d] else 0
        longest = max(longest, run)
        weekday[dt.date.fromisoformat(d).strftime("%A")] += days[d]
    top = max(weekday.values()) if weekday else 0
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7) - dt.timedelta(weeks=WEEKS - 1)
    weekly = [0] * WEEKS
    for d in dates:
        i = (dt.date.fromisoformat(d) - start).days // 7
        if 0 <= i < WEEKS:
            weekly[i] += days[d]
    return {"total": sum(days[d] for d in dates), "active": sum(1 for d in dates if days[d]),
            "longest": longest, "busiest": [n for n in DAYS if top and weekday[n] == top],
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
    """Catmull-Rom spline through the points, kept between baseline and top."""
    clamp = lambda y: min(floor, max(ceiling, y))
    p = [points[0]] + points + [points[-1]]
    d = f"M{p[1][0]:.1f} {p[1][1]:.1f}"
    for i in range(1, len(p) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p[i - 1], p[i], p[i + 1], p[i + 2]
        d += (f" C{x1 + (x2 - x0) / 6:.1f} {clamp(y1 + (y2 - y0) / 6):.1f} "
              f"{x2 - (x3 - x1) / 6:.1f} {clamp(y2 - (y3 - y1) / 6):.1f} {x2:.1f} {y2:.1f}")
    return d


def ago(when, now):
    days = (now - when).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} days ago"
    return f"{days // 7} weeks ago" if days < 60 else f"{days // 30} months ago"


def draw(m, push, now):
    T = Typesetter()
    W, H = 1200, 440
    X0, YT, X1, YB = 90, 136, 846, 360
    weekly, smooth = m["weekly"], savitzky_golay(m["weekly"])
    vmax = nice_ceiling(max(weekly + [1]))
    to_y = lambda v: YB - math.sqrt(max(v, 0) / vmax) * (YB - YT)
    step = (X1 - X0) / WEEKS
    to_x = lambda i: X0 + (i + 0.5) * step
    out = [panel(W, H),
           T.text("GitHub activity", 48, 70, "un", 28, INK["text"]),
           T.text(f"last 52 weeks, redrawn {now.day} {now:%b %Y}", 49, 100, "mo", 14, INK["muted"])]

    # Square-root axis, so quiet weeks stay visible next to busy ones
    ticks, last = [], None
    for v in [vmax] + [c for c in (500, 200, 100, 50, 20, 10, 5, 2, 1) if c < vmax] + [0]:
        y = to_y(v)
        if last is None or y - last >= 30 or v == 0:
            if v == 0 and ticks and y - to_y(ticks[-1]) < 30:
                ticks.pop()
            ticks.append(v)
            last = y
    for v in ticks:
        y = to_y(v)
        if v:
            out.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{INK["grid"]}"/>')
        out.append(T.text(str(v), X0 - 14, y + 4, "mo", 12, INK["dim"], anchor="end"))
    out.append(f'<line x1="{X0}" y1="{YB}" x2="{X1}" y2="{YB}" stroke="{INK["edge"]}" stroke-width="1.5"/>')
    for i in range(WEEKS):
        week = m["start"] + dt.timedelta(weeks=i)
        firsts = [week + dt.timedelta(days=k) for k in range(7) if (week + dt.timedelta(days=k)).day == 1]
        if firsts and to_x(i) > X0 + 10:
            out.append(T.text(firsts[0].strftime("%b"), to_x(i), YB + 26, "mo", 12, INK["dim"], anchor="middle"))

    for i, v in enumerate(weekly):
        if v:
            top = to_y(v)
            out.append(f'<rect x="{to_x(i) - 3.6:.1f}" y="{top:.1f}" width="7.2" height="{YB - top:.1f}" '
                       f'rx="3.6" fill="{ramp(math.sqrt(v / vmax))}"/>')
    curve = smooth_path([(to_x(i), to_y(v)) for i, v in enumerate(smooth)], YB, YT)
    out.append(f'<path d="{curve}" fill="none" stroke="#FFFFFF" stroke-opacity="0.45" stroke-width="7" filter="url(#blur)"/>')
    out.append(f'<path d="{curve}" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linejoin="round"/>')
    peak = max(range(WEEKS), key=lambda i: weekly[i])
    if weekly[peak]:
        px = min(max(to_x(peak), X0 + 14), X1 - 14)
        out.append(T.text(str(weekly[peak]), px, to_y(weekly[peak]) - 12, "mb", 14, INK["text"], anchor="middle"))

    busiest = "/".join(d[:3] for d in m["busiest"]) or "none"
    cells = [(f"{m['total']:,}", "contributions"), (str(m["active"]), "active days"),
             (str(m["longest"]), "day best streak"), (busiest, "busiest day")]
    for (value, label), (cx, cy) in zip(cells, [(892, 184), (1040, 184), (892, 282), (1040, 282)]):
        value, size = fit(T, value, "un", 38, 138, 20)
        out.append(T.text(value, cx, cy, "un", size, "url(#num)"))
        out.append(T.text(label, cx + 1, cy + 26, "mo", 13, INK["muted"]))
    if push:
        note, size = fit(T, f"last push: {push[0]}, {ago(push[1], now)}", "mo", 13, 272, 10)
        out.append(T.text(note, 893, 350, "mo", size, INK["muted"]))

    defs = ('<linearGradient id="num" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#F43F5E"/><stop offset="1" stop-color="#FDE047"/></linearGradient>'
            '<filter id="blur" x="-5%" y="-30%" width="110%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>'
            + T.defs())
    desc = (f"Weekly GitHub contributions over the last 52 weeks with a smoothed trend line. "
            f"{m['total']} contributions on {m['active']} days, best streak {m['longest']} days.")
    return svg(W, H, "".join(out), defs, title="GitHub activity", desc=desc)


def main():
    with open(os.path.join(HERE, "profile.json"), encoding="utf-8") as fh:
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
    write("activity.svg", draw(measure(days, now.date()), push, now))


if __name__ == "__main__":
    main()
