import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── FOUNDER TAB ──────────────────────────

def draw_founder(win, gs: GameState):
    h, w = win.getmaxyx()
    f = gs.founder
    bg = BACKGROUNDS[f.background_idx]
    y = 3
    mid = w // 2

    # Left: Identity
    safe_addstr(win, y, 2, " FOUNDER PROFILE ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2
    rows = [
        ("Name",          f.username),
        ("Background",    bg["name"]),
        ("Reputation",    f"{f.reputation}/100"),
        ("Burnout",       f"{f.burnout}%"),
        ("Tokens Used",   f"{f.total_tokens_used:,}K"),
        ("Companies",     str(len(gs.active_companies()))),
        ("Projects",      str(len(gs.projects))),
        ("AI Sub",        AI_SUBS[gs.active_ai_sub_idx]["name"]),
    ]
    lw = mid - 4
    for label, val in rows:
        safe_addstr(win, y, 4, f"{label:<22}", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 26, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        y += 1

    y += 1
    # Skill bars
    safe_addstr(win, y, 4, "SKILLS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    skills = [
        ("Prototyping", f.skill_prototyping),
        ("Sales",       f.skill_sales),
        ("Tech Depth",  f.skill_tech),
        ("Management",  f.skill_management),
    ]
    for name, val in skills:
        safe_addstr(win, y, 4, f"  {name:<14}", curses.color_pair(PAIR_MUTED))
        bw = lw - 22
        progress_bar(win, y, 20, bw, val, PAIR_ACCENT, PAIR_MUTED)
        safe_addstr(win, y, 20 + bw + 1, f"{val:3d}", curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1
    # Burnout bar (danger colour)
    safe_addstr(win, y, 4, "  Burnout        ", curses.color_pair(PAIR_MUTED))
    bw = lw - 22
    burn_pair = PAIR_DANGER if f.burnout > 70 else PAIR_WARN if f.burnout > 40 else PAIR_ACCENT
    progress_bar(win, y, 20, bw, f.burnout, burn_pair, PAIR_MUTED)
    safe_addstr(win, y, 20 + bw + 1, f"{f.burnout:3d}%",
                curses.color_pair(PAIR_DANGER if f.burnout > 70 else PAIR_MUTED))
    y += 2

    # Background bonus reminder
    safe_addstr(win, y, 4, f"Background: {bg['name']}", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 6, bg["desc"][:mid-8], curses.color_pair(PAIR_MUTED))
    y += 1
    bonuses = bg["bonuses"]
    bstr = (f"  Proto {bonuses['prototyping']:+d}  Sales {bonuses['sales']:+d}  "
            f"Tech {bonuses['tech_skill']:+d}  Burnout Resist {bonuses['burnout_resist']:+d}")
    safe_addstr(win, y, 6, bstr[:mid-8], curses.color_pair(PAIR_ACCENT))

    # Right: Achievements + career
    rx = mid + 2
    rw = w - mid - 4
    ry = 3
    safe_addstr(win, ry, rx, " ACHIEVEMENTS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.achievements:
        for ach in f.achievements[:8]:
            safe_addstr(win, ry, rx+2, f"🏆 {ach}", curses.color_pair(PAIR_WARN))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "No achievements yet. Go ship something.",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, " CAREER HISTORY ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.career_history:
        for entry in f.career_history[:8]:
            safe_addstr(win, ry, rx+2, f"  {entry}"[:rw-4], curses.color_pair(PAIR_MUTED))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "Your story is just beginning.",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 2
    safe_addstr(win, ry, rx, " UNLOCKED RESEARCH ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.unlocked_research:
        for res in f.unlocked_research[:6]:
            safe_addstr(win, ry, rx+2, f"✓ {res}", curses.color_pair(PAIR_ACCENT))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "Nothing unlocked yet. Visit Research.",
                    curses.color_pair(PAIR_MUTED))

