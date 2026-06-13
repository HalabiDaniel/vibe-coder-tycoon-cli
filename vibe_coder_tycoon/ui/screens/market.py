import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── MARKET TAB ───────────────────────────

def draw_market(win, gs: GameState):
    h, w = win.getmaxyx()
    y = 3
    mid = w // 2
    lw = mid - 3

    safe_addstr(win, y, 2, " MARKET & TRENDS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    month = MONTH_NAMES[gs.month-1]
    safe_addstr(win, y+1, 2, f"  {month} {gs.year}  —  AI Builder Confidence Index: 78/100",
                curses.color_pair(PAIR_MUTED))
    y += 3

    # Trending niches
    trends = [
        ("AI Wrapper Tools",   "+42%", "🔥🔥🔥", "Extremely hot"),
        ("B2B Automation",     "+28%", "🔥🔥",   "Growing"),
        ("EdTech",             "+11%", "🔥",     "Stable uptick"),
        ("Fintech Consumer",   "+7%",  "📈",     "Steady"),
        ("Social Networking",  "-3%",  "📉",     "Declining"),
        ("No-Code Platforms",  "-12%", "🧊",     "Cooling off"),
    ]

    safe_addstr(win, y, 2, "NICHE TREND REPORT", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER)
    y += 1
    for niche, pct, heat, label in trends:
        pp = PAIR_ACCENT if pct.startswith("+") else PAIR_DANGER
        safe_addstr(win, y, 4, f"  {heat}  {niche:<22} {pct:<7} {label}", curses.color_pair(pp))
        y += 1

    y += 1
    # AI sub pricing
    safe_addstr(win, y, 2, "AI SUBSCRIPTION MARKET", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER)
    y += 1
    safe_addstr(win, y, 4, f"  {'NAME':<20} {'$/mo':>6}  {'QUALITY':<9}  NOTE",
                curses.color_pair(PAIR_MUTED) | curses.A_BOLD)
    y += 1
    current_sub = AI_SUBS[gs.active_ai_sub_idx]["name"]
    for sub in AI_SUBS:
        is_cur = (sub["name"] == current_sub)
        cp = PAIR_BADGE_GREEN if is_cur else PAIR_MUTED
        cur = "← ACTIVE" if is_cur else ""
        cost = f"${sub['cost']}" if sub["cost"] else "Free"
        qual = "█" * sub["quality"] + "░" * (5 - sub["quality"])
        safe_addstr(win, y, 4, f"  {sub['name']:<20} {cost:>6}  {qual}  {sub['desc'][:24]}  {cur}",
                    curses.color_pair(cp))
        y += 1

    # Right column: Rivals + infrastructure
    rx = mid + 2
    rw = w - mid - 4
    ry = 3 + 3

    safe_addstr(win, ry, rx, "COMPETITOR ACTIVITY", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    rivals = [
        ("SnapStack LLC",    "AI Wrapper",     "$14K MRR", "↑ Fast"),
        ("CloudCastle",      "SaaS Infra",     "$9K MRR",  "→ Stable"),
        ("DeployGoblin Co.", "CLI Tools",      "$3.5K MRR","↓ Slowing"),
        ("BirdBoard Inc.",   "Social Tool",    "$1K MRR",  "↓ Dying"),
        ("HuntProductive",   "Productivity",   "$22K MRR", "↑ Surging"),
    ]
    for rname, rtype, rmrr, rtrend in rivals:
        safe_addstr(win, ry, rx+2, f"{rname:<20} {rtype:<16} {rmrr:<10} {rtrend}",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, "INVESTOR MOOD", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    safe_addstr(win, ry, rx+2, "Angel Market:   Bullish on AI tooling", curses.color_pair(PAIR_ACCENT))
    ry += 1
    safe_addstr(win, ry, rx+2, "VC Market:      Cautious — focused on B2B", curses.color_pair(PAIR_WARN))
    ry += 1
    safe_addstr(win, ry, rx+2, "Platform Mood:  RepoRealm star count rising", curses.color_pair(PAIR_MUTED))
    ry += 1
    safe_addstr(win, ry, rx+2, "IndieScroll:    Solo devs trending", curses.color_pair(PAIR_ACCENT))

    ry += 2
    safe_addstr(win, ry, rx, "PLATFORM NEWS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    platform_news = [
        "⚠️  SnapStack pricing up 30% next quarter",
        "📉 CloudCastle outage caused 6hr downtime",
        "🔥 IndieScroll launch day record: 8K visitors",
        "💸 DeployGoblin acquired for $2M (rumoured)",
    ]
    for pn in platform_news:
        safe_addstr(win, ry, rx+2, pn[:rw-4], curses.color_pair(PAIR_MUTED))
        ry += 1

