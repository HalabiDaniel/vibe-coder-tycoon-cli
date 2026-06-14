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
        ("N",               "Advance one month"),
        ("Founder: B/R/T",  "Take Break / Team Recharge / Inspire"),
        ("Employees: I/G",  "Inspirational Talk / Distraction"),
        ("Market: S/I",     "Cycle Subscription / IDE"),
        ("Q",               "Quit the game"),
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
        ("Sanity",    "Mental health (founder + staff). Low = conditions."),
        ("Touch Grass","Zero-sanity staff leave ~1mo, then auto-return."),
        ("Era",       "Game epoch. Unlocks models, IDEs, product types."),
        ("Model Score","1-10 smarts of an AI model for vibe coding."),
        ("Subscription","Your AI tier. Free→Pro→Pro+→API→Self-Hosted."),
        ("IDE",       "Editor. Boosts dev speed / cuts bugs."),
        ("Hype",      "Public interest. Drives launch spikes."),
        ("Bug Risk",  "Chance of shipping broken features."),
        ("Valuation", "Estimated company worth based on revenue."),
        ("Trait",     "An employee's special bonus ability."),
    ]
    for term, defn in glossary:
        safe_addstr(win, ry, rx+2, f"  {term:<14}", curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        safe_addstr(win, ry, rx+18, defn[:rw-20], curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, "CORE SYSTEMS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    systems = [
        "Sanity drains under crunch & high Vibe. Recharge teams.",
        "High Vibe = faster dev but more bugs and burnout.",
        "Eras unlock new AI models, IDEs, and subscription tiers.",
        "Pick a model by its score; pair it with the right IDE.",
        "API tier bills per token; Self-Hosted = open models only.",
        "Projects earn revenue once launched — track MRR.",
    ]
    for s in systems:
        safe_addstr(win, ry, rx+2, f"• {s}"[:rw-4], curses.color_pair(PAIR_MUTED))
        ry += 1

