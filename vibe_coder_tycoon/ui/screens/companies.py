import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── COMPANIES TAB ────────────────────────

@dataclass
class CompaniesUIState:
    view: str = "list"       # "list" | "detail" | "new"
    selected: int = 0
    new_fields: list = field(default_factory=lambda: [
        {"label": "Company Name",   "value": "", "max": 30, "type": "text"},
        {"label": "Legal Style",    "value": "", "type": "options",
         "options": COMPANY_LEGAL_STYLES, "selected": 0},
        {"label": "Focus Area",     "value": "", "type": "options",
         "options": COMPANY_FOCUS_AREAS,  "selected": 0},
        {"label": "Funding Style",  "value": "", "type": "options",
         "options": FUNDING_STYLES,        "selected": 0},
        {"label": "Risk Appetite",  "value": "", "type": "options",
         "options": RISK_APPETITES,        "selected": 0},
        {"label": "Starting Cash ($)", "value": "2000", "max": 10, "type": "text"},
    ])
    new_focused: int = 0
    message: str = ""

def draw_companies(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3

    if ui.view == "new":
        _draw_new_company_form(win, gs, ui)
        return

    # Header
    safe_addstr(win, y, 2, " COMPANIES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 16, f"({len(gs.companies)} total, {len(gs.active_companies())} active)",
                curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y, w-20, "[ N: New Company ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    # List
    header = f"  {'COMPANY NAME':<26} {'LEGAL STYLE':<16} {'FOCUS':<16} {'CASH':>9} {'MRR':>8}  {'STATUS':<8}"
    hline(win, y, 1, w-2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    for i, c in enumerate(gs.companies):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        status = "Active" if c.active else "Closed"
        row = (f"  {c.name:<26} {c.legal_style:<16} {c.focus_area:<16} "
               f"${c.cash:>8,} ${c.monthly_revenue:>7,}  {status}")
        safe_addstr(win, y, 1, " "*(w-2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))
        y += 1

    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 2

    # Detail panel for selected company
    if gs.companies and 0 <= ui.selected < len(gs.companies):
        c = gs.companies[ui.selected]
        projs = gs.projects_for_company(c.id)
        emps  = gs.employees_for_company(c.id)
        profit = c.monthly_revenue - c.monthly_expenses
        pp = PAIR_ACCENT if profit >= 0 else PAIR_DANGER

        mid = w // 2
        lw = mid - 2

        # Company detail left
        detail_rows = [
            ("Founded",      f"{MONTH_NAMES[c.founded_month-1]} {c.founded_year}"),
            ("Risk Appetite",c.risk_appetite),
            ("Funding",      c.funding_style),
            ("Monthly Rev",  f"${c.monthly_revenue:,}"),
            ("Monthly Exp",  f"${c.monthly_expenses:,}"),
            ("Net / Month",  f"${profit:+,}"),
            ("Debt",         f"${c.debt:,}" if c.debt else "None"),
            ("Valuation",    f"${c.valuation:,}"),
            ("Reputation",   f"{c.reputation}/100"),
            ("Mood",         f"{c.mood}%"),
            ("Projects",     str(len(projs))),
            ("Employees",    str(len(emps))),
        ]
        for label, val in detail_rows:
            if y >= h - 4:
                break
            safe_addstr(win, y, 4, f"{label:<18}", curses.color_pair(PAIR_MUTED))
            vp = pp if "Net" in label else PAIR_ACCENT
            safe_addstr(win, y, 22, val, curses.color_pair(vp) | curses.A_BOLD)
            y += 1

        # Actions
        actions = ["[ Open Dashboard ]", "[ Add Project ]", "[ Hire Employee ]",
                   "[ Rename ]", "[ Sell ]", "[ Close ]"]
        ax = 4
        for a in actions:
            safe_addstr(win, min(y+1, h-4), ax, a, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ax += len(a) + 2

    safe_addstr(win, h-4, 2, "Up/Down: select  |  N: new company  |  Enter: open",
                curses.color_pair(PAIR_MUTED))

def _draw_new_company_form(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " NEW COMPANY ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    bw = min(60, w - 4)
    bx = (w - bw) // 2
    draw_box(win, y, bx, len(ui.new_fields)*3 + 4, bw, PAIR_BORDER, "COMPANY SETUP", PAIR_TITLE)
    y += 1

    for i, f in enumerate(ui.new_fields):
        is_focus = (i == ui.new_focused)
        fy = y + i * 3
        la = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
              else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_focus else "  "
        safe_addstr(win, fy, bx+2, f"{prefix}{f['label']}", la)

        if f["type"] == "options":
            opts = f["options"]
            sel  = f["selected"]
            prev = f"‹ {opts[(sel-1)%len(opts)][:14]}"
            curr = f"  [{opts[sel][:20]}]  "
            nxt  = f"{opts[(sel+1)%len(opts)][:14]} ›"
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, fy+1, bx+4, prev[:16], curses.color_pair(PAIR_MUTED))
            safe_addstr(win, fy+1, bx+20, curr, curses.color_pair(ip) | (curses.A_BOLD if is_focus else 0))
            safe_addstr(win, fy+1, bx+44, nxt[:16], curses.color_pair(PAIR_MUTED))
        else:
            val = f["value"]
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, fy+1, bx+2, f" {val:<{bw-8}} "[:bw-4], curses.color_pair(ip))

    btn_y = y + len(ui.new_fields)*3 + 2
    safe_addstr(win, btn_y, bx+4, "[ Create Company → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
    safe_addstr(win, btn_y, bx+26, "[ Cancel ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)

    if ui.message:
        mp = PAIR_ACCENT if "created" in ui.message.lower() else PAIR_DANGER
        safe_addstr(win, btn_y+2, bx+4, ui.message, curses.color_pair(mp) | curses.A_BOLD)

    safe_addstr(win, h-3, 2, "Up/Down: field  |  ◄/►: options  |  Type: text  |  Enter: create  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

