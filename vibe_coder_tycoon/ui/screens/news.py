import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── NEWS TAB ─────────────────────────────

@dataclass
class NewsUIState:
    selected: int = 0

def draw_news(win, gs: GameState, ui: NewsUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " TECH NEWS FEED ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 20, "Fictional market intelligence for your decision-making.",
                curses.color_pair(PAIR_MUTED))
    y += 2

    categories = list(set(n["category"] for n in gs.news_feed))
    cat_x = 2
    safe_addstr(win, y, 2, "All  ", curses.color_pair(PAIR_TAB_ACTIVE))
    cat_x += 6
    for cat in categories:
        safe_addstr(win, y, cat_x, f"{cat}  ", curses.color_pair(PAIR_TAB_INACTIVE))
        cat_x += len(cat) + 3
    y += 2

    mid = w // 2
    lw = mid - 2

    # News list
    for i, item in enumerate(gs.news_feed[:min(len(gs.news_feed), h - y - 8)]):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        icon = item.get("icon", "📰")
        headline = item["headline"]
        category = item["category"]
        date = item["date"]
        safe_addstr(win, y + i*2, 1, " "*(lw), curses.color_pair(rp))
        safe_addstr(win, y + i*2, 2, f" {icon} {headline[:lw-12]}",
                    curses.color_pair(rp))
        safe_addstr(win, y + i*2 + 1, 4, f"  [{category}]  {date}",
                    curses.color_pair(PAIR_MUTED))

    # Detail panel
    rx = mid + 2
    rw = w - mid - 4
    if gs.news_feed and 0 <= ui.selected < len(gs.news_feed):
        item = gs.news_feed[ui.selected]
        ry = y
        safe_addstr(win, ry, rx, " STORY DETAIL ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 2
        safe_addstr(win, ry, rx+2, item["icon"] + " " + item["headline"][:rw-6],
                    curses.color_pair(PAIR_WARN) | curses.A_BOLD)
        ry += 2
        safe_addstr(win, ry, rx+2, f"Category: {item['category']}   Date: {item['date']}",
                    curses.color_pair(PAIR_MUTED))
        ry += 2
        effect_text = item.get("effect") or "No immediate gameplay effect."
        safe_addstr(win, ry, rx+2, "Effect:", curses.color_pair(PAIR_TITLE))
        safe_addstr(win, ry+1, rx+4, str(effect_text)[:rw-6], curses.color_pair(PAIR_MUTED))

    safe_addstr(win, h-4, 2, "Up/Down: select story  |  Enter: read full story",
                curses.color_pair(PAIR_MUTED))

