import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── END DEMO SCREEN ──────────────────────

def draw_demo_end(win, gs: GameState):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)

    center_text(win, 2, "╔═════════════════════════════════════════╗",
                curses.color_pair(PAIR_BORDER))
    center_text(win, 3, "║        FOUNDER REPORT — DEMO COMPLETE        ║",
                curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 4, "╚═════════════════════════════════════════╝",
                curses.color_pair(PAIR_BORDER))

    total_rev  = sum(p.lifetime_revenue for p in gs.projects)
    total_users = sum(p.users for p in gs.projects)
    launched   = len([p for p in gs.projects if p.status not in ("In Dev",)])
    failed     = len([p for p in gs.projects if p.status == "Failed"])
    companies  = len(gs.companies)

    # Rank calculation
    score = total_rev // 100 + total_users // 10 + gs.founder.reputation
    if score > 500:    rank = "🏆 Tech Visionary"
    elif score > 200:  rank = "🚀 Serial Founder"
    elif score > 80:   rank = "⚡ Vibe Coder"
    elif score > 20:   rank = "🌱 Early Builder"
    else:              rank = "🐣 Rookie Founder"

    best_project = max(gs.projects, key=lambda p: p.lifetime_revenue, default=None)
    worst_project = max(gs.projects, key=lambda p: p.bug_count, default=None)

    rows = [
        ("Companies Created",   str(companies)),
        ("Projects Launched",   str(launched)),
        ("Projects Failed",     str(failed)),
        ("Total Revenue",       f"${total_rev:,}"),
        ("Total Users",         f"{total_users:,}"),
        ("Founder Reputation",  f"{gs.founder.reputation}/100"),
        ("Final Burnout",       f"{gs.founder.burnout}%"),
        ("Biggest Win",         best_project.name if best_project else "—"),
        ("Biggest Disaster",    worst_project.name if worst_project else "—"),
        ("Final Founder Rank",  rank),
    ]
    bw = 52
    bx = (w - bw) // 2
    by = 6
    draw_box(win, by, bx, len(rows)+4, bw, PAIR_BORDER, "FINAL STATS", PAIR_TITLE)
    for i, (label, val) in enumerate(rows):
        ry = by + 2 + i
        safe_addstr(win, ry, bx+4, f"{label:<28}", curses.color_pair(PAIR_MUTED))
        vp = PAIR_ACCENT if "Revenue" in label or "Win" in label else PAIR_WARN
        safe_addstr(win, ry, bx+32, val, curses.color_pair(vp) | curses.A_BOLD)

    # ── Colourful, bordered "Thanks for playing" send-off ──
    tw = 50
    tx = (w - tw) // 2
    ty = by + len(rows) + 5

    safe_addstr(win, ty,   tx, "╔" + "═" * (tw - 2) + "╗",
                curses.color_pair(PAIR_BORDER) | curses.A_BOLD)
    for r in range(1, 5):
        safe_addstr(win, ty + r, tx,          "║", curses.color_pair(PAIR_BORDER) | curses.A_BOLD)
        safe_addstr(win, ty + r, tx + tw - 1, "║", curses.color_pair(PAIR_BORDER) | curses.A_BOLD)
    safe_addstr(win, ty + 5, tx, "╚" + "═" * (tw - 2) + "╝",
                curses.color_pair(PAIR_BORDER) | curses.A_BOLD)

    center_text(win, ty + 1, "⚡ THANKS FOR PLAYING ⚡",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    center_text(win, ty + 2, "V I B E   C O D E R   T Y C O O N",
                curses.color_pair(PAIR_WARN) | curses.A_BOLD)
    center_text(win, ty + 4, "Build fast.  Ship often.  Don't burn out.",
                curses.color_pair(PAIR_ACCENT))

    center_text(win, ty + 7,
                "Press Q to exit  •  R to start a new game",
                curses.color_pair(PAIR_MUTED))

