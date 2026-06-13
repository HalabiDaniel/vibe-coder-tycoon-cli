import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── HELP TAB ─────────────────────────────

def draw_help(win):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " HELP & TUTORIAL ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    mid = w // 2

    # Left: Tutorial + game loop
    safe_addstr(win, y, 2, "THE VIBE CODER LOOP", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    loop_steps = [
        "1. Create or join a company",
        "2. Choose your AI subscription",
        "3. Start a project — pick tools, stack, and niche",
        "4. Spend time and money to develop it",
        "5. Handle random events and market shifts",
        "6. Launch the product and earn revenue (or fail)",
        "7. Improve your founder skills and unlock research",
        "8. Hire employees, manage morale, avoid burnout",
        "9. Build a second company — then a third",
        "10. The demo ends after 12 months",
    ]
    for step in loop_steps:
        safe_addstr(win, y, 4, step, curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1
    safe_addstr(win, y, 2, "KEYBINDINGS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    keybinds = [
        ("Tab / Shift+Tab", "Switch between tabs"),
        ("Arrow Keys",      "Navigate lists and forms"),
        ("Enter",           "Confirm / open selection"),
        ("Esc",             "Go back / cancel"),
        ("N",               "Advance one month (Dashboard)"),
        ("Q",               "Quit the game"),
        ("H",               "Open this help screen"),
    ]
    for key, desc in keybinds:
        safe_addstr(win, y, 4, f"  {key:<20} {desc}", curses.color_pair(PAIR_MUTED))
        y += 1

    # Right: Glossary
    rx = mid + 2
    rw = w - mid - 4
    ry = 5
    safe_addstr(win, ry, rx, "GLOSSARY", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    glossary = [
        ("MRR",       "Monthly Recurring Revenue"),
        ("Burnout",   "Founder mental health drain. Affects all output."),
        ("Tokens",    "AI compute units consumed per action."),
        ("Hype",      "Public interest in a project. Drives launch spikes."),
        ("Tech Debt", "Code quality debt. Causes bugs over time."),
        ("Bug Risk",  "Chance of shipping broken features."),
        ("Chaos",     "Unpredictability of the AI model."),
        ("Valuation", "Estimated company worth based on revenue."),
        ("Morale",    "Team happiness. Affects productivity."),
        ("Trait",     "An employee's special bonus ability."),
        ("Runway",    "Months of cash left at current burn rate."),
    ]
    for term, defn in glossary:
        safe_addstr(win, ry, rx+2, f"  {term:<14}", curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        safe_addstr(win, ry, rx+18, defn[:rw-20], curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, "CORE SYSTEMS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    systems = [
        "Burnout accumulates monthly. Rest your founder.",
        "Projects earn revenue once launched — track MRR.",
        "Companies can be sold, merged, or closed.",
        "Research unlocks permanent founder upgrades.",
        "News events may affect market conditions.",
        "The demo ends at 12 months — make them count.",
    ]
    for s in systems:
        safe_addstr(win, ry, rx+2, f"• {s}"[:rw-4], curses.color_pair(PAIR_MUTED))
        ry += 1

