import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── PROJECTS TAB ─────────────────────────

@dataclass
class ProjectsUIState:
    view: str = "list"      # "list" | "new" | "dev"
    selected: int = 0
    filter_status: str = "All"
    new_fields: list = field(default_factory=lambda: [
        {"label": "Project Name",    "value": "", "max": 30, "type": "text"},
        {"label": "Project Type",    "type": "options", "options": PROJECT_TYPES,  "selected": 0},
        {"label": "AI Tool",         "type": "options", "options": [s["name"] for s in AI_SUBS], "selected": 0},
        {"label": "Tech Stack",      "type": "options", "options": TECH_STACKS,    "selected": 0},
        {"label": "Market Niche",    "type": "options", "options": NICHES,         "selected": 0},
        {"label": "Feature Scope",   "type": "options", "options": ["Lean MVP", "Standard", "Feature-Rich", "Overengineered"], "selected": 0},
        {"label": "Budget (USD)",    "value": "500",    "max": 10, "type": "text"},
        {"label": "Dev Time (weeks)","value": "4",      "max": 3,  "type": "text"},
    ])
    new_focused: int = 0
    new_step: int = 0   # 0=company select, 1=config, 2=review
    new_company_idx: int = 0
    message: str = ""
    dev_project_idx: int = -1   # index into gs.projects for dev view

def draw_projects(win, gs: GameState, ui: ProjectsUIState):
    h, w = win.getmaxyx()

    if ui.view == "new":
        _draw_new_project_wizard(win, gs, ui)
        return

    y = 3
    filters = ["All", "In Dev", "Dev Complete", "Launched", "Growing", "Failed", "Archived", "Sold"]
    safe_addstr(win, y, 2, " PROJECTS  ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    fx = 16
    for f in filters:
        is_sel = (f == ui.filter_status)
        fp = PAIR_TAB_ACTIVE if is_sel else PAIR_TAB_INACTIVE
        safe_addstr(win, y, fx, f" {f} ", curses.color_pair(fp))
        fx += len(f) + 3
    safe_addstr(win, y, w-20, "[ N: New Project ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    visible = [p for p in gs.projects
               if ui.filter_status == "All" or p.status == ui.filter_status
               or (ui.filter_status == "In Dev" and p.status == "Dev Complete")]

    header = f"  {'NAME':<20} {'COMPANY':<22} {'TYPE':<16} {'STATUS':<10} {'MRR':>7} {'USERS':>7}"
    hline(win, y, 1, w-2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    for i, p in enumerate(visible[:h - y - 10]):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        c = gs.company_by_id(p.company_id)
        cname = c.name[:20] if c else "—"
        mrr = f"${p.revenue:,}" if p.revenue else "—"
        users = f"{p.users:,}" if p.users else "—"
        row = f"  {p.name:<20} {cname:<22} {p.ptype:<16} {'':10} {mrr:>7} {users:>7}"
        safe_addstr(win, y, 1, " "*(w-2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))
        bx = 2 + 20 + 22 + 16 + 2 + 2
        badge(win, y, bx, p.status, status_pair(p.status))
        if p.status == "In Dev":
            progress_bar(win, y, bx + len(p.status) + 5, 10, p.progress, PAIR_BADGE_BLUE, PAIR_MUTED)
        y += 1

    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    # Detail panel
    if visible and 0 <= ui.selected < len(visible):
        p = visible[ui.selected]
        safe_addstr(win, y, 2, f" Detail: {p.name} ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y += 1
        mid = w // 2
        details = [
            ("Stack",         p.stack),
            ("Niche",         p.niche),
            ("AI Model",      p.model),
            ("MRR",           f"${p.revenue:,}"),
            ("Users",         f"{p.users:,}"),
            ("Tokens Used",   f"{p.tokens_used:,}K"),
            ("Bug Count",     str(p.bug_count)),
            ("Hype",          f"{p.hype}/100"),
            ("Tech Debt",     f"{p.tech_debt}/100"),
            ("Team Morale",   f"{p.morale}%"),
            ("Lifetime Rev",  f"${p.lifetime_revenue:,}"),
            ("Launch Date",   p.launch_date if p.launch_date else "—"),
        ]
        col_w = (w-4) // 3
        for j, (k, v) in enumerate(details):
            if y + j//3 >= h - 6:
                break
            col = j % 3
            row_off = j // 3
            dx = 4 + col * col_w
            safe_addstr(win, y+row_off, dx, f"{k}: ", curses.color_pair(PAIR_MUTED))
            safe_addstr(win, y+row_off, dx+len(k)+2, v, curses.color_pair(PAIR_ACCENT))

        act_y = y + (len(details)-1)//3 + 2
        if p.status in ("In Dev", "Dev Complete"):
            dev_label = "[ Enter: Open Dev Dashboard ]"
            safe_addstr(win, min(act_y, h-5), 4, dev_label,
                        curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
            ax = 4 + len(dev_label) + 2
        else:
            ax = 4
        other_actions = ["[ Sunset ]", "[ View Analytics ]", "[ Archive ]"]
        for act in other_actions:
            safe_addstr(win, min(act_y, h-5), ax, act, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ax += len(act) + 2

    safe_addstr(win, h-4, 2,
                "Up/Down: select  |  ◄/►: filter  |  N: new project  |  Enter: dev dashboard",
                curses.color_pair(PAIR_MUTED))

def _draw_new_project_wizard(win, gs: GameState, ui: ProjectsUIState):
    h, w = win.getmaxyx()
    bw = min(64, w - 4)
    bx = (w - bw) // 2

    if ui.new_step == 0:
        # Step 1: Company selection
        safe_addstr(win, 3, 2, " NEW PROJECT — Step 1 of 3: Choose Company ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y = 5
        for i, c in enumerate(gs.active_companies()):
            is_sel = (i == ui.new_company_idx)
            prefix = "▶ " if is_sel else "  "
            cp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
            safe_addstr(win, y + i*2, bx + 2, " "*(bw-4), curses.color_pair(cp))
            safe_addstr(win, y + i*2, bx + 2,
                        f"{prefix}{c.name:<28} {c.focus_area:<18} ${c.cash:,}",
                        curses.color_pair(cp))
        btn_y = y + len(gs.active_companies())*2 + 2
        safe_addstr(win, btn_y, bx+4, "[ Next: Configure Project → ]",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        safe_addstr(win, h-3, 2, "Up/Down: select  |  Enter: next  |  Esc: cancel",
                    curses.color_pair(PAIR_MUTED))

    elif ui.new_step == 1:
        # Step 2: Project config
        safe_addstr(win, 3, 2, " NEW PROJECT — Step 2 of 3: Configure ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y = 5
        draw_box(win, y, bx, len(ui.new_fields)*3 + 4, bw, PAIR_BORDER, "PROJECT DETAILS", PAIR_TITLE)
        y += 1

        for i, f in enumerate(ui.new_fields):
            is_focus = (i == ui.new_focused)
            fy = y + i * 3
            la = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
                  else curses.color_pair(PAIR_MUTED))
            prefix = "▶ " if is_focus else "  "
            safe_addstr(win, fy, bx+2, f"{prefix}{f['label']}", la)

            if f.get("type") == "options":
                opts = f["options"]
                sel  = f["selected"]
                prev = f"‹ {opts[(sel-1)%len(opts)][:14]}"
                curr = f"  [{opts[sel][:20]}]  "
                nxt  = f"{opts[(sel+1)%len(opts)][:14]} ›"
                ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
                safe_addstr(win, fy+1, bx+4, prev[:16], curses.color_pair(PAIR_MUTED))
                safe_addstr(win, fy+1, bx+20, curr, curses.color_pair(ip) | (curses.A_BOLD if is_focus else 0))
                safe_addstr(win, fy+1, bx+44, nxt[:14], curses.color_pair(PAIR_MUTED))
            else:
                val = f["value"]
                ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
                safe_addstr(win, fy+1, bx+2, f" {val:<{bw-8}} "[:bw-4], curses.color_pair(ip))

        btn_y = y + len(ui.new_fields)*3 + 2
        safe_addstr(win, btn_y, bx+4, "[ Review & Launch → ]",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        safe_addstr(win, h-3, 2,
                    "Up/Down: field  |  ◄/►: options  |  Type: text  |  Enter: review  |  Esc: back",
                    curses.color_pair(PAIR_MUTED))

    elif ui.new_step == 2:
        # Step 3: Review
        safe_addstr(win, 3, 2, " NEW PROJECT — Step 3 of 3: Review & Confirm ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y = 5

        name     = ui.new_fields[0]["value"] or "Unnamed"
        ptype    = PROJECT_TYPES[ui.new_fields[1]["selected"]]
        sub_name = [s["name"] for s in AI_SUBS][ui.new_fields[2]["selected"]]
        stack    = TECH_STACKS[ui.new_fields[3]["selected"]]
        niche    = NICHES[ui.new_fields[4]["selected"]]
        scope    = ["Lean MVP", "Standard", "Feature-Rich", "Overengineered"][ui.new_fields[5]["selected"]]
        try:    budget = int(ui.new_fields[6]["value"])
        except: budget = 500
        try:    weeks  = int(ui.new_fields[7]["value"])
        except: weeks  = 4

        sub_idx = ui.new_fields[2]["selected"]
        bug_risk = AI_SUBS[sub_idx]["bug_risk"]
        cost_est = budget + weeks * 200
        launch_risk = "HIGH" if weeks < 3 else "MEDIUM" if weeks < 7 else "LOW"
        hype_est = "HIGH" if scope == "Feature-Rich" else "MEDIUM"

        active = gs.active_companies()
        company_name = active[ui.new_company_idx].name if active else "None"

        draw_box(win, y, bx, 18, bw, PAIR_BORDER, "PROJECT SUMMARY", PAIR_TITLE)
        review_rows = [
            ("Company",        company_name),
            ("Name",           name),
            ("Type",           ptype),
            ("AI Tool",        sub_name),
            ("Stack",          stack),
            ("Niche",          niche),
            ("Feature Scope",  scope),
            ("Budget",         f"${budget:,}"),
            ("Dev Time",       f"{weeks} weeks"),
            ("Est. Cost",      f"${cost_est:,}"),
            ("Launch Risk",    launch_risk),
            ("Bug Risk",       f"{'HIGH' if bug_risk > 3 else 'MEDIUM' if bug_risk > 2 else 'LOW'}"),
            ("Hype Potential", hype_est),
            ("Burnout Impact", f"{'HIGH' if weeks > 6 else 'MEDIUM' if weeks > 3 else 'LOW'}"),
        ]
        for i, (label, val) in enumerate(review_rows):
            ry = y + 1 + i
            safe_addstr(win, ry, bx+4, f"{label:<20}", curses.color_pair(PAIR_MUTED))
            vp = PAIR_DANGER if val in ("HIGH", "OVERENGINEERED") else \
                 PAIR_WARN  if val == "MEDIUM" else PAIR_ACCENT
            safe_addstr(win, ry, bx+24, val, curses.color_pair(vp) | curses.A_BOLD)

        btn_y = y + 16
        safe_addstr(win, btn_y, bx+4, "[ Confirm & Start Project ]",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        safe_addstr(win, btn_y, bx+34, "[ Go Back ]",
                    curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)

        if ui.message:
            safe_addstr(win, btn_y+2, bx+4, ui.message,
                        curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)

        safe_addstr(win, h-3, 2, "Enter: start project  |  Esc: back to config",
                    curses.color_pair(PAIR_MUTED))

