import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── RESEARCH TAB ─────────────────────────

@dataclass
class ResearchUIState:
    cat_sel: int = 0
    item_sel: int = 0

def draw_research(win, gs: GameState, ui: ResearchUIState):
    h, w = win.getmaxyx()
    y = 3
    mid = w // 3

    safe_addstr(win, y, 2, " RESEARCH TREE ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 20, "Unlock new capabilities across 8 domains.",
                curses.color_pair(PAIR_MUTED))
    y += 2

    # Left: Category list
    safe_addstr(win, y, 2, "CATEGORIES", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    for i, (cat, _) in enumerate(RESEARCH_CATEGORIES):
        is_sel = (i == ui.cat_sel)
        cp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        unlocked = sum(1 for item in RESEARCH_CATEGORIES[i][1]
                       if item in gs.founder.unlocked_research)
        total = len(RESEARCH_CATEGORIES[i][1])
        safe_addstr(win, y + i*2, 2, " "*(mid-4), curses.color_pair(cp))
        safe_addstr(win, y + i*2, 2, f" {prefix}{cat:<18} {unlocked}/{total}",
                    curses.color_pair(cp))

    # Right: Items in selected category
    rx = mid + 4
    rw = w - rx - 2
    ry = 5

    cat_name, cat_items = RESEARCH_CATEGORIES[ui.cat_sel]
    safe_addstr(win, ry, rx, f" {cat_name.upper()} UNLOCKS ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 2

    for j, item in enumerate(cat_items):
        is_sel = (j == ui.item_sel)
        is_unlocked = (item in gs.founder.unlocked_research)
        prefix = "▶ " if is_sel else "  "
        icon = "✓ " if is_unlocked else "○ "
        cp = (PAIR_BADGE_GREEN if is_unlocked else
              PAIR_HIGHLIGHT if is_sel else PAIR_PANEL)
        safe_addstr(win, ry, rx, " "*(rw-2), curses.color_pair(cp))
        safe_addstr(win, ry, rx, f" {prefix}{icon}{item}",
                    curses.color_pair(cp) | (curses.A_BOLD if is_sel else 0))

        if is_sel and not is_unlocked:
            safe_addstr(win, ry+1, rx+4, "Cost: 500 tokens + $200",
                        curses.color_pair(PAIR_WARN))
            safe_addstr(win, ry+1, rx+30, "[ Enter: Unlock ]",
                        curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        elif is_sel and is_unlocked:
            safe_addstr(win, ry+1, rx+4, "Already unlocked. Effect: active.",
                        curses.color_pair(PAIR_ACCENT))
        ry += 3

    safe_addstr(win, h-4, 2,
                "Up/Down: category  |  ◄/►: items  |  Enter: unlock",
                curses.color_pair(PAIR_MUTED))

