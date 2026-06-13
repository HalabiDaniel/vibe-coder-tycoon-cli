import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── EMPLOYEES TAB ────────────────────────

@dataclass
class EmployeesUIState:
    selected: int = 0
    filter_company: int = -1  # -1 = all

def draw_employees(win, gs: GameState, ui: EmployeesUIState):
    h, w = win.getmaxyx()
    y = 3

    safe_addstr(win, y, 2, " EMPLOYEES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, w-24, "[ H: Hire Employee ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    header = f"  {'NAME':<18} {'ROLE':<20} {'LVL':>3} {'SALARY':>8} {'MOOD':>5} {'PROD':>5} {'COMPANY':<20}"
    hline(win, y, 1, w-2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    for i, emp in enumerate(gs.employees[:h - y - 12]):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        c = gs.company_by_id(emp.company_id)
        cname = c.name[:18] if c else "—"
        mood_icon = "😊" if emp.mood > 75 else "😐" if emp.mood > 45 else "😞"
        row = (f"  {emp.name:<18} {emp.role:<20} "
               f"{'★'*emp.level:<3} ${emp.salary:>7,} "
               f" {mood_icon}{emp.mood:>2}%  {emp.productivity:>3}%  {cname}")
        safe_addstr(win, y, 1, " "*(w-2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))

        # Mood bar
        bx = w - 16
        mp = PAIR_ACCENT if emp.mood > 60 else PAIR_WARN if emp.mood > 30 else PAIR_DANGER
        progress_bar(win, y, bx, 10, emp.mood, mp, PAIR_MUTED)
        y += 1

    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    # Detail / actions for selected employee
    if gs.employees and 0 <= ui.selected < len(gs.employees):
        emp = gs.employees[ui.selected]
        mid = w // 2

        # Left: details
        safe_addstr(win, y, 2, f" {emp.name} — {emp.role} ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y += 1
        detail_rows = [
            ("Level",       "★" * emp.level),
            ("Skill",       f"{emp.skill}/100"),
            ("Mood",        f"{emp.mood}%"),
            ("Loyalty",     f"{emp.loyalty}%"),
            ("Productivity",f"{emp.productivity}%"),
            ("Salary",      f"${emp.salary:,}/mo"),
            ("Hired",       str(emp.hired_year)),
            ("Trait",       emp.trait or "None"),
        ]
        for label, val in detail_rows:
            safe_addstr(win, y, 4, f"{label:<16}", curses.color_pair(PAIR_MUTED))
            safe_addstr(win, y, 20, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
            y += 1

        # Right: actions
        actions = ["[ Train (+200cr) ]", "[ Boost Morale ]", "[ Promote ]",
                   "[ Assign to Project ]", "[ Give Rest Day ]", "[ Lay Off ]"]
        rx = mid + 2
        ry = y - len(detail_rows)
        for a in actions:
            safe_addstr(win, ry, rx, a, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ry += 2

    # Payroll summary at bottom right
    total_sal = sum(e.salary for e in gs.employees)
    safe_addstr(win, h-5, w-30, f"Total Payroll: ${total_sal:,}/mo",
                curses.color_pair(PAIR_WARN) | curses.A_BOLD)
    safe_addstr(win, h-4, 2, "Up/Down: select  |  H: hire  |  Enter: action",
                curses.color_pair(PAIR_MUTED))

