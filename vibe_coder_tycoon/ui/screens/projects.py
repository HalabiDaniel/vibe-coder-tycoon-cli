import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


# ─────────────────────── UI HELPERS ───────────────────────────

def _sparkline(values: list, width: int = 14) -> str:
    """Return a text sparkline for the given revenue history list."""
    if not values:
        return "—" * width
    CHARS = " ▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    recent = values[-width:]
    if mx == mn:
        return "▄" * len(recent)
    return "".join(CHARS[min(8, int((v - mn) / (mx - mn) * 8))] for v in recent)


def _btn(win, y: int, x: int, label: str, pair: int):
    safe_addstr(win, y, x, label, curses.color_pair(pair) | curses.A_BOLD)


# ─────────────────────── PROJECTS TAB ─────────────────────────

@dataclass
class ProjectsUIState:
    view: str = "list"      # "list" | "new" | "dev" | "templates"
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
        {"label": "Template",        "type": "options", "options": ["None"], "selected": 0},
    ])
    new_focused: int = 0
    new_step: int = 0   # 0=company select, 1=config, 2=review
    new_company_idx: int = 0
    message: str = ""
    dev_project_idx: int = -1   # index into gs.projects for dev view
    # Phase 8 — template build sub-view
    tmpl_company_idx: int = 0
    tmpl_type_idx: int = 0
    tmpl_message: str = ""

def draw_projects(win, gs: GameState, ui: ProjectsUIState):
    h, w = win.getmaxyx()

    if ui.view == "new":
        _draw_new_project_wizard(win, gs, ui)
        return

    if ui.view == "templates":
        _draw_templates_view(win, gs, ui)
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
    safe_addstr(win, y, w-30, "[ N: New ] [ B: Templates ]",
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
        ver_tag = f"  v{p.version}" if p.version > 1 else ""
        safe_addstr(win, y, 2, f" Detail: {p.name}{ver_tag} ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y += 1

        # Core details (always shown)
        details = [
            ("Stack",        p.stack),
            ("Niche",        p.niche),
            ("AI Model",     p.model),
            ("MRR",          f"${p.revenue:,}"),
            ("Lifetime Rev", f"${p.lifetime_revenue:,}"),
            ("Tokens Used",  f"{p.tokens_used:,}K"),
            ("Bug Count",    str(p.bug_count)),
            ("Hype",         f"{p.hype}/100"),
            ("Launch Date",  p.launch_date if p.launch_date else "—"),
        ]

        # Phase 3 fields for launched products
        if p.status in ("Launched", "Growing", "Sunset"):
            obso_pct = (p.age_months / p.obsolescence_months) if p.obsolescence_months else 0
            if obso_pct >= 1.0:
                obso_label = "Obsolete"
            elif obso_pct >= 0.75:
                obso_label = "Aging"
            elif obso_pct >= 0.5:
                obso_label = "Maturing"
            else:
                obso_label = "Fresh"
            auto_tag = f"Every {p.auto_update_interval}mo" if p.auto_update_interval else "Off"
            details.extend([
                ("Rev Model",    p.revenue_model or "—"),
                ("Age",          f"{p.age_months}mo  [{obso_label}]"),
                ("Active Users", f"{p.active_users:,}"),
                ("Churn Rate",   f"{p.churn_rate:.1%}/mo"),
                ("Auto-Update",  auto_tag),
            ])

        col_w = (w - 4) // 3
        for j, (k, v) in enumerate(details):
            if y + j // 3 >= h - 8:
                break
            col = j % 3
            row_off = j // 3
            dx = 4 + col * col_w
            safe_addstr(win, y + row_off, dx, f"{k}: ", curses.color_pair(PAIR_MUTED))
            safe_addstr(win, y + row_off, dx + len(k) + 2, v, curses.color_pair(PAIR_ACCENT))

        detail_rows = (len(details) - 1) // 3 + 1
        act_y = y + detail_rows + 1

        # Revenue sparkline for launched products
        rev_hist = getattr(p, "revenue_history", [])
        if rev_hist and p.status in ("Launched", "Growing") and act_y < h - 7:
            spark = _sparkline(rev_hist)
            safe_addstr(win, act_y, 4, "Revenue trend: ", curses.color_pair(PAIR_MUTED))
            safe_addstr(win, act_y, 19, spark, curses.color_pair(PAIR_ACCENT))
            peak = max(rev_hist)
            safe_addstr(win, act_y, 19 + len(spark) + 1,
                        f"  peak ${peak:,}", curses.color_pair(PAIR_MUTED))
            act_y += 1

        # Action buttons
        ax = 4
        btn_y = min(act_y, h - 5)
        if p.status in ("In Dev", "Dev Complete"):
            _btn(win, btn_y, ax, "[ Enter: Dev Dashboard ]", PAIR_BUTTON_FOCUS)
        elif p.status in ("Launched", "Growing"):
            for label, pair in [
                ("[ U: Minor Update ]",    PAIR_BUTTON),
                ("[ M: Major Revision ]",  PAIR_BUTTON),
                ("[ V: New Version ]",     PAIR_BUTTON),
                ("[ S: Sunset ]",          PAIR_BUTTON),
                ("[ A: Auto-Update ]",     PAIR_BUTTON),
            ]:
                safe_addstr(win, btn_y, ax, label, curses.color_pair(pair) | curses.A_BOLD)
                ax += len(label) + 2
                if ax > w - 20:
                    btn_y += 1
                    ax = 4
                    if btn_y >= h - 3:
                        break

    safe_addstr(win, h-4, 2,
                "↑↓:select  ◄/►:filter  N:new  B:templates  Enter:dev  U/M/V/S/A:product actions",
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
        _mopts   = ui.new_fields[2].get("options", [s["name"] for s in AI_SUBS])
        sub_name = _mopts[ui.new_fields[2]["selected"]] if _mopts else "—"
        stack    = TECH_STACKS[ui.new_fields[3]["selected"]]
        niche    = NICHES[ui.new_fields[4]["selected"]]
        scope    = ["Lean MVP", "Standard", "Feature-Rich", "Overengineered"][ui.new_fields[5]["selected"]]
        try:    budget = int(ui.new_fields[6]["value"])
        except: budget = 500
        try:    weeks  = int(ui.new_fields[7]["value"])
        except: weeks  = 4

        from ...engine.systems.models_ai import get_model_stats
        bug_risk = get_model_stats(gs, sub_name)["bug_risk"]
        cost_est = budget + weeks * 200
        launch_risk = "HIGH" if weeks < 3 else "MEDIUM" if weeks < 7 else "LOW"
        hype_est = "HIGH" if scope == "Feature-Rich" else "MEDIUM"

        active = gs.active_companies()
        company_name = active[ui.new_company_idx].name if active else "None"

        tmpl_field = ui.new_fields[8] if len(ui.new_fields) > 8 else None
        tmpl_name = "—"
        if tmpl_field:
            opts = tmpl_field.get("options", ["None"])
            sel = tmpl_field.get("selected", 0)
            if 0 <= sel < len(opts):
                tmpl_name = opts[sel]

        draw_box(win, y, bx, 19, bw, PAIR_BORDER, "PROJECT SUMMARY", PAIR_TITLE)
        review_rows = [
            ("Company",        company_name),
            ("Name",           name),
            ("Type",           ptype),
            ("AI Tool",        sub_name),
            ("Stack",          stack),
            ("Niche",          niche),
            ("Feature Scope",  scope),
            ("Template",       tmpl_name),
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

        btn_y = y + 17
        safe_addstr(win, btn_y, bx+4, "[ Confirm & Start Project ]",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        safe_addstr(win, btn_y, bx+34, "[ Go Back ]",
                    curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)

        if ui.message:
            safe_addstr(win, btn_y+2, bx+4, ui.message,
                        curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)

        safe_addstr(win, h-3, 2, "Enter: start project  |  Esc: back to config",
                    curses.color_pair(PAIR_MUTED))


def _draw_templates_view(win, gs: GameState, ui: ProjectsUIState):
    from ...engine.systems.templates import templates_for_company, get_template_def

    h, w = win.getmaxyx()
    safe_addstr(win, 3, 2, " TEMPLATE WORKSHOP ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, 3, 24, "Internal assets that boost future builds",
                curses.color_pair(PAIR_MUTED))

    active = gs.active_companies()
    if not active:
        safe_addstr(win, 6, 4, "Create a company first.", curses.color_pair(PAIR_DANGER))
        safe_addstr(win, h-3, 2, "Esc: back", curses.color_pair(PAIR_MUTED))
        return

    ui.tmpl_company_idx = max(0, min(ui.tmpl_company_idx, len(active) - 1))
    company = active[ui.tmpl_company_idx]
    ui.tmpl_type_idx = max(0, min(ui.tmpl_type_idx, len(TEMPLATE_TYPES) - 1))

    mid = w // 2

    # ── Left: build a new template ─────────────────────────────
    y = 5
    safe_addstr(win, y, 2, "BUILD NEW TEMPLATE", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, mid - 4, PAIR_BORDER); y += 1

    safe_addstr(win, y, 4, "Company  ‹C›:", curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y, 18, f"{company.name}  (${company.cash:,})",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    y += 2

    tdef = TEMPLATE_TYPES[ui.tmpl_type_idx]
    safe_addstr(win, y, 4, "Type  ‹↑↓›:", curses.color_pair(PAIR_MUTED))
    y += 1
    for i, t in enumerate(TEMPLATE_TYPES):
        is_sel = (i == ui.tmpl_type_idx)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        safe_addstr(win, y, 4, " " * (mid - 8), curses.color_pair(rp))
        safe_addstr(win, y, 4,
                    f"{prefix}{t['name']:<20} {t['base_days']}d  ${t['build_cost']:,}",
                    curses.color_pair(rp))
        y += 1

    y += 1
    safe_addstr(win, y, 4, tdef["desc"][:mid - 6], curses.color_pair(PAIR_MUTED) | curses.A_DIM)
    y += 2
    can_afford = company.cash >= tdef["build_cost"]
    bp = PAIR_BUTTON_FOCUS if can_afford else PAIR_MUTED
    safe_addstr(win, y, 4, f"[ Enter: Build {tdef['name']} (${tdef['build_cost']:,}) ]",
                curses.color_pair(bp) | curses.A_BOLD)

    # ── Right: existing templates for this company ─────────────
    rx = mid + 2
    ry = 5
    owned = templates_for_company(gs, company.id)
    safe_addstr(win, ry, rx, f"{company.name}'s TEMPLATES ({len(owned)})",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, w - rx - 2, PAIR_BORDER); ry += 1

    if not owned:
        safe_addstr(win, ry, rx, "None yet — build one on the left.",
                    curses.color_pair(PAIR_MUTED))
    else:
        for t in owned:
            if ry >= h - 5:
                break
            safe_addstr(win, ry, rx, t.name, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
            ry += 1
            safe_addstr(win, ry, rx + 2,
                        f"Design+{t.design_bonus:.0f}  Tech+{t.tech_bonus:.0f}  "
                        f"Time-{t.time_reduction:.0%}  Bugs-{t.bug_reduction:.0%}",
                        curses.color_pair(PAIR_MUTED))
            ry += 1

    # In-progress template builds
    building = [p for p in gs.projects if getattr(p, "is_template", False) and p.status == "In Dev"]
    if building and ry < h - 6:
        ry += 1
        safe_addstr(win, ry, rx, "BUILDING…", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 1
        for p in building:
            if ry >= h - 5:
                break
            safe_addstr(win, ry, rx, f"{p.template_type}  {p.progress}%  "
                        f"(manage in Projects → Enter)", curses.color_pair(PAIR_WARN))
            ry += 1

    if ui.tmpl_message:
        mp = PAIR_ACCENT if "✓" in ui.tmpl_message else PAIR_DANGER
        safe_addstr(win, h - 4, 2, ui.tmpl_message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2,
                "↑↓: template type  |  C: cycle company  |  Enter: build  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

