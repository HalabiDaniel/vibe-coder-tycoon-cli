import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── DASHBOARD TAB ────────────────────────

def draw_dashboard(win, gs: GameState, selected_company_idx: int):
    h, w = win.getmaxyx()
    y_start = 3
    mid = w // 2

    active = gs.active_companies()

    # Left column
    lw = mid - 2

    # Company selector
    safe_addstr(win, y_start, 2, " ACTIVE COMPANIES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y = y_start + 1
    for i, c in enumerate(active):
        is_sel = (i == selected_company_idx)
        pf = "▶ " if is_sel else "  "
        cp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        safe_addstr(win, y, 2, " " * (lw - 1), curses.color_pair(cp))
        safe_addstr(win, y, 2, f" {pf}{c.name:<24} ${c.cash:>8,}", curses.color_pair(cp))
        y += 1

    y += 1
    hline(win, y, 2, lw - 2, PAIR_BORDER)
    y += 1

    # Overview of selected company
    if active and 0 <= selected_company_idx < len(active):
        c = active[selected_company_idx]
        profit = c.monthly_revenue - c.monthly_expenses
        pp = PAIR_ACCENT if profit >= 0 else PAIR_DANGER

        # Phase 13 — rival market pressure across this company's live verticals
        from ...engine.systems.rivals import saturation_factor
        live_verts = {p.ptype for p in gs.projects
                      if p.company_id == c.id and p.status in ("Launched", "Growing")
                      and not p.discontinued}
        if live_verts:
            avg_sat = sum(saturation_factor(gs, v) for v in live_verts) / len(live_verts)
            pressure_pct = int((1.0 - avg_sat) * 100)
            pressure_val = "None" if pressure_pct <= 0 else f"-{pressure_pct}% sales"
        else:
            pressure_val = "—"

        rows = [
            ("Founded",       f"{MONTH_NAMES[c.founded_month-1]} {c.founded_year}"),
            ("Legal Style",   c.legal_style),
            ("Focus",         c.focus_area),
            ("Monthly Rev",   f"${c.monthly_revenue:,}"),
            ("Monthly Exp",   f"${c.monthly_expenses:,}"),
            ("Net / Month",   f"${profit:+,}"),
            ("Debt",          f"${c.debt:,}" if c.debt else "None"),
            ("Valuation",     f"${c.valuation:,}"),
            ("Reputation",    f"{c.reputation}/100"),
            ("Rival Pressure", pressure_val),
            ("Office",        ["", "Bedroom", "Co-Work", "Private Office", "HQ"][c.office_level]),
            ("Company Mood",  f"{c.mood}%"),
            ("Active Projects", str(len([p for p in gs.projects if p.company_id == c.id
                                         and p.status not in ("Failed", "Sunset")]))),
            ("Employees",     str(len([e for e in gs.employees if e.company_id == c.id]))),
        ]
        for label, val in rows:
            safe_addstr(win, y, 4, f"{label:<20}", curses.color_pair(PAIR_MUTED))
            pair = pp if "Net" in label else PAIR_ACCENT
            safe_addstr(win, y, 24, val, curses.color_pair(pair) | curses.A_BOLD)
            y += 1

        y += 1
        for label, val, maxval, fp in [
            ("Reputation", c.reputation, 100, PAIR_ACCENT),
            ("Mood",       c.mood,       100, PAIR_BADGE_BLUE),
        ]:
            safe_addstr(win, y, 4, f" {label:<12}", curses.color_pair(PAIR_MUTED))
            bw = lw - 22
            progress_bar(win, y, 18, bw, val, fp, PAIR_MUTED)
            safe_addstr(win, y, 18 + bw + 1, f"{val:3d}%", curses.color_pair(PAIR_MUTED))
            y += 1

    # Right column
    rx = mid + 1
    rw = w - mid - 3

    # Global stats
    safe_addstr(win, y_start, rx, " FOUNDER COMMAND CENTER ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry = y_start + 1
    total_rev  = sum(c.monthly_revenue for c in active)
    total_exp  = sum(c.monthly_expenses for c in active)
    total_proj = len([p for p in gs.projects if p.status not in ("Failed", "Sunset")])
    global_rows = [
        ("Date",           f"{MONTH_NAMES[gs.month-1]} {gs.year}"),
        ("Total Cash",     f"${gs.total_cash():,}"),
        ("Monthly Revenue",f"${total_rev:,}"),
        ("Monthly Expenses",f"${total_exp:,}"),
        ("Founder Burnout",f"{gs.founder.burnout}%"),
        ("Founder Rep",    f"{gs.founder.reputation}/100"),
        ("Active Projects",str(total_proj)),
        ("AI Subscription",AI_SUBS[gs.active_ai_sub_idx]["name"]),
        ("Months Elapsed", f"{gs.months_elapsed} / {DEMO_MONTH_LIMIT}"),
    ]
    for label, val in global_rows:
        safe_addstr(win, ry, rx+2, f"{label:<22}", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ry, rx+24, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        ry += 1

    ry += 1
    hline(win, ry, rx, rw - 1, PAIR_BORDER)
    ry += 1

    # Current goal
    safe_addstr(win, ry, rx+2, "CURRENT GOAL", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if gs.months_elapsed == 0:
        goal = "Launch your first project and earn $1,000 MRR."
    elif total_rev < 1000:
        goal = "Reach $1,000 MRR across all companies."
    elif total_rev < 5000:
        goal = "Scale to $5,000 MRR and hire your first employee."
    elif gs.founder.burnout > 70:
        goal = "Manage burnout before it derails your companies."
    else:
        goal = "Build toward a second company or a major launch."
    safe_addstr(win, ry, rx+2, f"  {goal}"[:rw-4], curses.color_pair(PAIR_WARN))
    ry += 2

    # Recent events feed
    safe_addstr(win, ry, rx+2, "RECENT EVENTS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    event_pairs = {"good": PAIR_ACCENT, "warn": PAIR_WARN, "bad": PAIR_DANGER, "neutral": PAIR_MUTED}
    for icon, msg, kind, date in gs.events[:min(8, h - ry - 3)]:
        ep = event_pairs.get(kind, PAIR_MUTED)
        safe_addstr(win, ry, rx+2, f"{icon} ", curses.color_pair(ep))
        safe_addstr(win, ry, rx+5, msg[:rw-18], curses.color_pair(ep))
        safe_addstr(win, ry, rx+rw-10, date[:8], curses.color_pair(PAIR_MUTED))
        ry += 1

    # Bottom hints
    safe_addstr(win, h-4, 2, "N: Advance Month  |  Up/Down: select company  |  Enter: open company",
                curses.color_pair(PAIR_MUTED))

