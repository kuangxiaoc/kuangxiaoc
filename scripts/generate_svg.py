#!/usr/bin/env python3
"""生成 README 用的动态 SVG。

设计原则：
1. 只用标准库，不装依赖 —— Actions 里跑得快，本地也能直接跑。
2. 无 token 也能跑：走公开 REST（60 次/小时，够用）；有 GITHUB_TOKEN 时
   额外走 GraphQL 拿真实 commit 贡献数与贡献日历（streak + 热力图）。
3. 网络失败不炸：降级生成占位卡片，保证 Actions 不红。

输出：
  assets/banner.svg     标题横幅（含最后更新时间）
  assets/stats.svg      数据卡：repos / stars / followers / commits / streak
  assets/grass.svg      贡献热力图（近 26 周，需 token）
  assets/activity.svg   最近公开动态
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

USER = os.getenv("PROFILE_USER", "kuangxiaoc")
TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# 淡蓝卡片配色：卡片自带浅色底 + 深色字，GitHub 浅色/深色模式下都可读
BG = "#eaf3fd"
BORDER = "#a8caf0"
FG = "#0b3d63"
MUTED = "#4a6b8a"
ACCENT = "#1f6feb"
GREEN = "#1a7f37"
PURPLE = "#8250df"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Helvetica, Arial, sans-serif"


# ---------------------------------------------------------------- HTTP helpers

def rest(path: str):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-builder",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def graphql(query: str):
    if not TOKEN:
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-builder",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.load(r)
    if payload.get("errors"):
        print(f"[warn] GraphQL errors: {payload['errors']}", file=sys.stderr)
    return payload.get("data")


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def clip(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------- data collect

def collect():
    d = {"user": None, "repos": [], "events": [], "contrib": None, "ok": True}
    try:
        d["user"] = rest(f"/users/{USER}")
        d["repos"] = rest(f"/users/{USER}/repos?per_page=100&sort=pushed")
        d["events"] = rest(f"/users/{USER}/events/public?per_page=30")
    except Exception as e:  # 网络/限流都降级
        print(f"[warn] REST 失败：{e}", file=sys.stderr)
        d["ok"] = False

    return d


CONTRIB_QUERY = """
query {
  user(login: "%s") {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""


def fetch_contrib():
    if not TOKEN:
        return None
    try:
        data = graphql(CONTRIB_QUERY % USER)
        return data["user"]["contributionsCollection"] if data else None
    except Exception as e:
        print(f"[warn] GraphQL 失败：{e}", file=sys.stderr)
        return None


def summarize(d):
    user = d["user"] or {}
    repos = d["repos"] or []
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    langs = {}
    for r in repos:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    top_langs = sorted(langs.items(), key=lambda x: -x[1])[:5]

    commits = prs = None
    streak = 0
    days = []
    c = d["contrib"]
    if c:
        commits = c.get("totalCommitContributions")
        prs = c.get("totalPullRequestContributions")
        for w in c.get("contributionCalendar", {}).get("weeks", []):
            for day in w.get("contributionDays", []):
                # GraphQL 给的是枚举，统一成 0-4 的 level 供画图用
                day["level"] = LEVEL_MAP.get(day.get("contributionLevel"), 0)
                days.append(day)
        # 连续贡献天数（从今天往回数）
        cur = 0
        for day in reversed(days):
            if day.get("contributionCount", 0) > 0:
                cur += 1
            elif day.get("date") == dt.date.today().isoformat():
                continue
            else:
                break
        streak = cur

    return {
        "repos": user.get("public_repos", len(repos)),
        "stars": stars,
        "forks": forks,
        "followers": user.get("followers", 0),
        "commits": commits,
        "prs": prs,
        "streak": streak,
        "weeks": [days[i:i + 7] for i in range(0, len(days), 7)][-26:],
        "top_langs": top_langs,
        "ok": d["ok"],
    }


EVENT_LABEL = {
    "PushEvent": "推送",
    "PullRequestEvent": "PR",
    "IssuesEvent": "Issue",
    "IssueCommentEvent": "评论",
    "CreateEvent": "新建",
    "ForkEvent": "Fork",
    "WatchEvent": "Star",
    "PullRequestReviewEvent": "Review",
}


def parse_events(events):
    """只留有信息量的事件：给别人仓库点星 / fork 属于噪音，丢了。"""
    out = []
    for e in events:
        t = e.get("type", "")
        if t in ("WatchEvent", "ForkEvent"):
            continue
        repo = (e.get("repo") or {}).get("name", "")
        payload = e.get("payload", {})
        detail = ""
        if t == "PushEvent":
            detail = clip((payload.get("commits") or [{}])[-1].get("message", ""), 46)
        elif t == "PullRequestEvent":
            detail = clip(payload.get("action", "") + " · " + (payload.get("pull_request") or {}).get("title", ""), 46)
        elif t == "IssuesEvent":
            detail = clip(payload.get("action", "") + " · " + (payload.get("issue") or {}).get("title", ""), 46)
        elif t == "CreateEvent":
            detail = payload.get("ref_type", "")
        out.append({
            "type": t,
            "label": EVENT_LABEL.get(t, t.replace("Event", "")),
            "repo": repo.split("/")[-1],
            "detail": detail,
            "at": e.get("created_at", ""),
        })
        if len(out) >= 6:
            break
    return out


def human_time(iso: str) -> str:
    try:
        t = dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except Exception:
        return ""
    delta = dt.datetime.now(dt.timezone.utc) - t
    if delta.days >= 30:
        return f"{delta.days // 30} 个月前"
    if delta.days >= 1:
        return f"{delta.days} 天前"
    h = delta.seconds // 3600
    return f"{h} 小时前" if h else "刚刚"


# ---------------------------------------------------------------- svg builders

def card_head(w: int, title: str, sub: str = "") -> list:
    parts = [
        f'<rect width="{w}" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="20" y="30" font-family="{FONT}" font-size="15" font-weight="600" fill="{FG}">{esc(title)}</text>',
    ]
    if sub:
        parts.append(f'<text x="20" y="50" font-family="{FONT}" font-size="11" fill="{MUTED}">{esc(sub)}</text>')
    return parts


def svg_banner(stats) -> str:
    w, h = 800, 150
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    langs = " · ".join(f"{n}" for n, _ in stats["top_langs"][:4]) or "Python"
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="#f7fbff"/><stop offset="55%" stop-color="#e6f1fd"/>'
        f'<stop offset="100%" stop-color="#cfe4fb"/></linearGradient>'
        f'<linearGradient id="t" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="#1f6feb"/><stop offset="100%" stop-color="#8250df"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#g)" stroke="{BORDER}"/>',
        f'<text x="36" y="66" font-family="{FONT}" font-size="30" font-weight="700" fill="url(#t)">蔡超 · Cai Chao</text>',
        f'<text x="36" y="94" font-family="{FONT}" font-size="14" fill="{FG}">LLM 应用工程 · AI Agent 工程化</text>',
        f'<text x="36" y="116" font-family="{FONT}" font-size="12" fill="{MUTED}">'
        f'浙江师范大学 电子信息（软件工程与大模型应用）在读 · 杭州</text>',
        f'<text x="{w-36}" y="66" text-anchor="end" font-family="{FONT}" font-size="12" fill="{MUTED}">{esc(langs)}</text>',
        f'<text x="{w-36}" y="86" text-anchor="end" font-family="{FONT}" font-size="11" fill="{MUTED}">'
        f'streak {stats["streak"]} 天</text>' if stats["streak"] else '',
        f'<text x="{w-36}" y="116" text-anchor="end" font-family="{FONT}" font-size="11" fill="{MUTED}">更新 {now}</text>',
        '</svg>',
    ]
    return "\n".join(p)


def svg_stats(stats) -> str:
    w, h = 800, 130
    items = [
        ("Repos", stats["repos"], ACCENT),
        ("Stars", stats["stars"], "#9a6700"),
        ("Followers", stats["followers"], GREEN),
        ("Commits", stats["commits"] if stats["commits"] is not None else "—", PURPLE),
        ("PRs", stats["prs"] if stats["prs"] is not None else "—", ACCENT),
        ("Streak", f'{stats["streak"]}d' if stats["streak"] else "—", GREEN),
    ]
    col = w // len(items)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
         f'<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
         f'<text x="20" y="26" font-family="{FONT}" font-size="12" font-weight="600" fill="{FG}">GitHub 数据</text>',
         f'<text x="{w-20}" y="26" text-anchor="end" font-family="{FONT}" font-size="10" fill="{MUTED}">'
         f'{"live" if stats["ok"] else "offline"}</text>']
    for i, (label, val, color) in enumerate(items):
        cx = i * col + col // 2
        p.append(f'<text x="{cx}" y="66" text-anchor="middle" font-family="{FONT}" font-size="24" '
                 f'font-weight="700" fill="{color}">{val}</text>')
        p.append(f'<text x="{cx}" y="88" text-anchor="middle" font-family="{FONT}" font-size="11" '
                 f'fill="{MUTED}">{label}</text>')
        if i:
            p.append(f'<line x1="{i*col}" y1="44" x2="{i*col}" y2="100" stroke="{BORDER}" stroke-width="1"/>')
    if stats["top_langs"]:
        txt = " · ".join(f"{n} {c}" for n, c in stats["top_langs"])
        p.append(f'<text x="20" y="115" font-family="{FONT}" font-size="10" fill="{MUTED}">语言分布 {esc(txt)}</text>')
    p.append('</svg>')
    return "\n".join(p)


LEVEL = ["#ccdcee", "#b6e3c6", "#7fd39a", "#46b970", "#2f9257"]
LEVEL_MAP = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
             "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def svg_grass(stats) -> str:
    weeks = stats["weeks"]
    if not weeks:
        # 无 GraphQL 数据时画一张全灰占位图，保证 README 里不会出现破图
        today = dt.date.today()
        start = today - dt.timedelta(days=25 * 7 + today.weekday())
        weeks = [[{"date": (start + dt.timedelta(days=wi * 7 + di)).isoformat(),
                   "contributionCount": 0, "level": 0} for di in range(7)] for wi in range(26)]
    cell, gap = 11, 3
    left, top = 34, 34
    w = left + len(weeks) * (cell + gap) + 20
    h = top + 7 * (cell + gap) + 34
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
         f'<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
         f'<text x="20" y="24" font-family="{FONT}" font-size="12" font-weight="600" fill="{FG}">贡献热力图</text>']
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            lv = min(int(day.get("level", 0)), 4)
            x = left + wi * (cell + gap)
            y = top + di * (cell + gap)
            p.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{LEVEL[lv]}" '
                     f'stroke="{BORDER}" stroke-width="0.5"/>')
    total = sum(d.get("contributionCount", 0) for wk in weeks for d in wk)
    p.append(f'<text x="20" y="{h-14}" font-family="{FONT}" font-size="10" fill="{MUTED}">'
             f'近 {len(weeks)} 周共 {total} 次贡献</text>')
    p.append('</svg>')
    return "\n".join(p)


def svg_activity(events) -> str:
    w = 800
    row = 44
    h = 60 + row * max(len(events), 1)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
         f'<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
         f'<text x="20" y="28" font-family="{FONT}" font-size="12" font-weight="600" fill="{FG}">最近动态</text>']
    if not events:
        p.append(f'<text x="20" y="60" font-family="{FONT}" font-size="11" fill="{MUTED}">暂无公开动态</text>')
    for i, e in enumerate(events):
        y = 52 + i * row
        p.append(f'<rect x="20" y="{y}" width="52" height="18" rx="9" fill="#d3e6fb" stroke="#8fb8ea"/>')
        p.append(f'<text x="46" y="{y+13}" text-anchor="middle" font-family="{FONT}" font-size="10" '
                 f'fill="{ACCENT}">{esc(e["label"])}</text>')
        p.append(f'<text x="84" y="{y+13}" font-family="{FONT}" font-size="12" font-weight="600" '
                 f'fill="{FG}">{esc(e["repo"])}</text>')
        if e["detail"]:
            p.append(f'<text x="84" y="{y+30}" font-family="{FONT}" font-size="10" '
                     f'fill="{MUTED}">{esc(e["detail"])}</text>')
        p.append(f'<text x="{w-20}" y="{y+13}" text-anchor="end" font-family="{FONT}" font-size="10" '
                 f'fill="{MUTED}">{human_time(e["at"])}</text>')
        if i:
            p.append(f'<line x1="20" y1="{y-6}" x2="{w-20}" y2="{y-6}" stroke="{BORDER}" stroke-width="1"/>')
    p.append('</svg>')
    return "\n".join(p)


# ---------------------------------------------------------------- main

def write(name: str, content: str):
    if not content:
        return
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    print(f"wrote {path} ({len(content)} bytes)")


def main():
    d = collect()
    d["contrib"] = fetch_contrib()
    stats = summarize(d)
    events = parse_events(d["events"])

    write("banner.svg", svg_banner(stats))
    write("stats.svg", svg_stats(stats))
    write("grass.svg", svg_grass(stats))
    write("activity.svg", svg_activity(events))
    print("done. graphql:", bool(d["contrib"]), "rest_ok:", d["ok"])


if __name__ == "__main__":
    main()
