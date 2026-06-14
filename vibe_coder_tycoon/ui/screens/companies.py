import curses
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import (
    COMPANY_LEGAL_STRUCTURES, COMPANY_FOCUSES, COMPANY_FOCUS_AREAS,
    COMPANY_LEGAL_STYLES, OFFICE_LEVELS, FUNDING_STYLES,
    RISK_APPETITES, MONTH_NAMES, AUTO_DEPOSIT_CYCLE,
)
from ...models import GameState, Company
from ...engine.systems.companies import (
    get_focus_data, get_legal_data, get_office_data,
    get_office_employee_cap, get_all_unlocked_roles,
    next_legal_structure, get_synergy_bonus,
)


# ─────────────────────── COMPANIES TAB ────────────────────────

@dataclass
class CompaniesUIState:
    view: str = "list"       # "list" | "new" | "deposit" | "withdraw" | "holding" | "infra"
    selected: int = 0
    infra_gpu_sel: int = 0   # selection index into available GPU generations
    new_fields: list = field(default_factory=lambda: [
        {"label": "Company Name",      "value": "", "max": 30, "type": "text"},
        {"label": "Legal Structure",   "value": "", "type": "options",
         "options": COMPANY_LEGAL_STYLES, "selected": 0},
        {"label": "Focus Area",        "value": "", "type": "options",
         "options": COMPANY_FOCUS_AREAS, "selected": 0},
        {"label": "Funding Style",     "value": "", "type": "options",
         "options": FUNDING_STYLES,       "selected": 0},
        {"label": "Risk Appetite",     "value": "", "type": "options",
         "options": RISK_APPETITES,       "selected": 0},
        {"label": "Starting Cash ($)", "value": "2000", "max": 10, "type": "text"},
    ])
    new_focused: int = 0
    message: str = ""
    finance_amount: str = ""


def draw_companies(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3

    if ui.view == "new":
        _draw_new_company_form(win, gs, ui)
        return

    if ui.view in ("deposit", "withdraw"):
        _draw_finance_prompt(win, gs, ui, h, w)
        return

    if ui.view == "holding":
        if gs.companies and 0 <= ui.selected < len(gs.companies):
            _draw_holding_view(win, gs, ui, gs.companies[ui.selected], h, w)
        return

    if ui.view == "infra":
        if gs.companies and 0 <= ui.selected < len(gs.companies):
            _draw_infra_view(win, gs, ui, gs.companies[ui.selected], h, w)
        return

    # ── List header ───────────────────────────────────────────────
    safe_addstr(win, y, 2, " COMPANIES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 16,
                f"({len(gs.companies)} total, {len(gs.active_companies())} active)",
                curses.color_pair(PAIR_MUTED))
    y += 2

    header = (f"  {'COMPANY NAME':<26} {'LEGAL':<16} {'FOCUS':<16} "
              f"{'CASH':>9} {'MRR':>8}  {'STATUS':<8}")
    hline(win, y, 1, w - 2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w - 2, PAIR_BORDER)
    y += 1

    for i, c in enumerate(gs.companies):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        status = "Active" if c.active else "Closed"
        legal_short = _short_legal(c.legal_style)
        row = (f"  {c.name:<26} {legal_short:<16} {c.focus_area:<16} "
               f"${c.cash:>8,} ${c.monthly_revenue:>7,}  {status}")
        safe_addstr(win, y, 1, " " * (w - 2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))
        y += 1

    y += 1
    hline(win, y, 1, w - 2, PAIR_BORDER)
    y += 2

    if gs.companies and 0 <= ui.selected < len(gs.companies):
        c = gs.companies[ui.selected]
        _draw_company_detail(win, gs, ui, c, y, h, w)

    safe_addstr(win, h - 4, 2,
                "↑↓:sel  D:deposit  W:withdraw  T:auto-dep  C:cover  O:office  L:legal  I:infra  H:holding  F:funding",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_company_detail(win, gs: GameState, ui, c, y, h, w):
    f = gs.founder
    profit = c.monthly_revenue - c.monthly_expenses
    pp = PAIR_ACCENT if profit >= 0 else PAIR_DANGER

    emp_count = len(gs.employees_for_company(c.id))
    emp_cap = get_office_employee_cap(c)
    office_data = get_office_data(c.office_level)
    office_name = office_data["name"] if office_data else "—"
    upgrade_cost = office_data.get("upgrade_cost", 0) if office_data else 0
    next_office = get_office_data(c.office_level + 1) if upgrade_cost > 0 else None

    legal_data = get_legal_data(c.legal_style)
    next_legal = next_legal_structure(c.legal_style)

    focus_data = get_focus_data(c.focus_area)
    synergy = get_synergy_bonus(gs, c)

    # Split into left and right panels
    mid = w // 2

    # Left: balance sheet + finance toggles
    left_rows = [
        ("Founded",      f"{MONTH_NAMES[c.founded_month-1]} {c.founded_year}"),
        ("Risk",         c.risk_appetite),
        ("Funding",      c.funding_style),
        ("Company Cash", f"${c.cash:,}"),
        ("Monthly Rev",  f"${c.monthly_revenue:,}"),
        ("Monthly Exp",  f"${c.monthly_expenses:,}"),
        ("Net/Month",    f"${profit:+,}"),
        ("Debt",         f"${c.debt:,}" if c.debt else "None"),
        ("Months Neg.",  str(c.months_negative) if c.months_negative else "—"),
    ]
    lx = 4
    ly = y
    for label, val in left_rows:
        if ly >= h - 9:
            break
        safe_addstr(win, ly, lx, f"{label:<16}", curses.color_pair(PAIR_MUTED))
        vp = pp if "Net" in label else PAIR_ACCENT
        safe_addstr(win, ly, lx + 16, val, curses.color_pair(vp) | curses.A_BOLD)
        ly += 1

    ly += 1
    # Finance toggles
    if ly < h - 9:
        auto_label = f"{c.auto_deposit_pct}%" if c.auto_deposit_pct else "OFF"
        auto_p = PAIR_ACCENT if c.auto_deposit_pct else PAIR_MUTED
        safe_addstr(win, ly, lx, "Auto-deposit:", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ly, lx + 14, f"[{auto_label:>4}] T:cycle", curses.color_pair(auto_p) | curses.A_BOLD)
        ly += 1
    if ly < h - 9:
        cover_label = "ON " if c.cover_from_personal else "OFF"
        cover_p = PAIR_ACCENT if c.cover_from_personal else PAIR_MUTED
        safe_addstr(win, ly, lx, "Cover-personal:", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ly, lx + 16, f"[{cover_label}] C:toggle", curses.color_pair(cover_p) | curses.A_BOLD)
        ly += 1
    if ly < h - 9:
        safe_addstr(win, ly, lx, f"Personal Cash:  ${f.personal_cash:,.0f}",
                    curses.color_pair(PAIR_MUTED))
        ly += 1

    # Right: office + legal + focus info
    rx = mid + 2
    ry = y

    # Office section
    if ry < h - 9:
        safe_addstr(win, ry, rx, "OFFICE", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 1
    if ry < h - 9:
        safe_addstr(win, ry, rx, f"Level {c.office_level}: {office_name}", curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        ry += 1
    if ry < h - 9:
        cap_p = PAIR_DANGER if emp_count >= emp_cap else PAIR_MUTED
        safe_addstr(win, ry, rx, f"Employees: {emp_count}/{emp_cap}", curses.color_pair(cap_p))
        ry += 1
    if ry < h - 9:
        if next_office and upgrade_cost > 0:
            can_up = "✓" if c.cash >= upgrade_cost else "✗"
            safe_addstr(win, ry, rx,
                        f"[O] Upgrade→Lv{c.office_level+1} ${upgrade_cost:,} {can_up}",
                        curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
        else:
            safe_addstr(win, ry, rx, "Max office level reached", curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1

    # Legal section
    if ry < h - 9:
        safe_addstr(win, ry, rx, "LEGAL STRUCTURE", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 1
    if ry < h - 9:
        safe_addstr(win, ry, rx, c.legal_style, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        ry += 1
    if legal_data and ry < h - 9:
        vc_str = "VC eligible" if legal_data["vc_eligible"] else "No VC"
        ipo_str = "IPO eligible" if legal_data["ipo_eligible"] else "No IPO"
        safe_addstr(win, ry, rx, f"{vc_str} | {ipo_str}", curses.color_pair(PAIR_MUTED))
        ry += 1
    if ry < h - 9:
        if next_legal:
            cash_ok = c.cash >= next_legal["unlock_cash"]
            req = next_legal.get("unlock_research")
            res_ok = (req is None) or (req in gs.founder.unlocked_research)
            can_up = "✓" if (cash_ok and res_ok) else "✗"
            safe_addstr(win, ry, rx,
                        f"[L] →{next_legal['name']} ${next_legal['unlock_cash']:,} {can_up}",
                        curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
        else:
            safe_addstr(win, ry, rx, "Max legal structure", curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1

    # Focus section
    if ry < h - 9:
        safe_addstr(win, ry, rx, "FOCUS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 1
    if ry < h - 9:
        safe_addstr(win, ry, rx, c.focus_area, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        ry += 1
    if focus_data and ry < h - 9:
        bonuses = []
        if focus_data["dev_speed_mult"] != 1.0:
            bonuses.append(f"Dev {focus_data['dev_speed_mult']:.0%}")
        if focus_data["token_cost_mult"] != 1.0:
            bonuses.append(f"Token {focus_data['token_cost_mult']:.0%}")
        if focus_data["revenue_mult"] != 1.0:
            bonuses.append(f"Rev {focus_data['revenue_mult']:.0%}")
        if focus_data["hype_mult"] != 1.0:
            bonuses.append(f"Hype {focus_data['hype_mult']:.0%}")
        if bonuses and ry < h - 9:
            safe_addstr(win, ry, rx, "  ".join(bonuses), curses.color_pair(PAIR_MUTED))
            ry += 1
    if synergy < 1.0 and ry < h - 9:
        safe_addstr(win, ry, rx, f"Synergy bonus active! ({synergy:.0%} cost)",
                    curses.color_pair(PAIR_ACCENT))
        ry += 1
    if focus_data and focus_data["name"] == "Holding Company" and ry < h - 9:
        subs = [comp for comp in gs.companies if comp.parent_company_id == c.id]
        safe_addstr(win, ry, rx, f"[H] Holding view ({len(subs)} subs)",
                    curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
        ry += 1


def _draw_holding_view(win, gs: GameState, ui, holding: Company, h: int, w: int):
    y = 3
    safe_addstr(win, y, 2, f" HOLDING: {holding.name} ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    subsidiaries = [c for c in gs.companies if c.parent_company_id == holding.id and c.active]
    independents = [c for c in gs.companies
                    if c.id != holding.id and c.parent_company_id == -1 and c.active]

    if subsidiaries:
        safe_addstr(win, y, 2, "SUBSIDIARIES", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y += 1
        total_cash = sum(c.cash for c in subsidiaries)
        total_mrr = sum(c.monthly_revenue for c in subsidiaries)
        for c in subsidiaries:
            synergy = get_synergy_bonus(gs, c)
            syn_tag = " ⚡synergy" if synergy < 1.0 else ""
            safe_addstr(win, y, 4,
                        f"  {c.name:<28} {c.focus_area:<16} ${c.cash:>8,} MRR${c.monthly_revenue:>6,}{syn_tag}",
                        curses.color_pair(PAIR_PANEL))
            y += 1
        y += 1
        safe_addstr(win, y, 4, f"Portfolio total:  Cash ${total_cash:,}   MRR ${total_mrr:,}/mo",
                    curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        y += 2
    else:
        safe_addstr(win, y, 2, "No subsidiaries yet. Set parent_company on another company to add one.",
                    curses.color_pair(PAIR_MUTED))
        y += 2

    if independents:
        safe_addstr(win, y, 2, "INDEPENDENT COMPANIES (can be added as subsidiaries):",
                    curses.color_pair(PAIR_MUTED))
        y += 1
        for c in independents:
            safe_addstr(win, y, 4, f"  {c.name:<28} {c.focus_area}",
                        curses.color_pair(PAIR_MUTED))
            y += 1

    if subsidiaries:
        safe_addstr(win, h - 4, 2,
                    "S: sweep all subsidiary cash up to holding",
                    curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2, "Esc: back", curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 2, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_infra_view(win, gs: GameState, ui, c: Company, h: int, w: int):
    from ...constants import HOSTING_PROVIDERS, GPU_GENERATIONS, DATACENTER_TIERS
    from ...engine.systems.infra import (
        get_hosting, get_datacenter, company_active_users,
        get_token_cost_multiplier, hosting_monthly_cost, compute_sale_revenue,
        available_gpus,
    )

    y = 3
    safe_addstr(win, y, 2, f" INFRASTRUCTURE: {c.name} ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    mid = w // 2
    users = company_active_users(gs, c)
    host = get_hosting(c.hosting_provider)
    cap = host["capacity"]
    over = users > cap
    load_p = PAIR_DANGER if over else (PAIR_WARN if users > cap * 0.75 else PAIR_ACCENT)

    # ── Left column: hosting + datacenter ──────────────────────
    lx = 4
    ly = y
    safe_addstr(win, ly, lx, "HOSTING  [P: cycle provider]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Provider : {c.hosting_provider}",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Load     : {users:,} / {cap:,} users",
                curses.color_pair(load_p)); ly += 1
    if over:
        safe_addstr(win, ly, lx, "⚠ OVER CAPACITY — outage risk!",
                    curses.color_pair(PAIR_DANGER) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Est. cost: ${hosting_monthly_cost(gs, c):,}/mo",
                curses.color_pair(PAIR_MUTED)); ly += 2

    dc = get_datacenter(c.datacenter_tier)
    nxt = get_datacenter(c.datacenter_tier + 1)
    safe_addstr(win, ly, lx, "DATACENTER  [D: upgrade]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Tier {c.datacenter_tier}: {dc['name']}",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Token cut: {dc['per_token_reduction']:.0%}   "
                f"Compute: {c.compute_capacity:,}u", curses.color_pair(PAIR_MUTED)); ly += 1
    if nxt["tier"] > c.datacenter_tier:
        ok = "✓" if c.cash >= nxt["cost"] else "✗"
        safe_addstr(win, ly, lx, f"[D] →{nxt['name']} ${nxt['cost']:,} {ok}",
                    curses.color_pair(PAIR_BUTTON) | curses.A_BOLD); ly += 1
    else:
        safe_addstr(win, ly, lx, "Max datacenter tier reached", curses.color_pair(PAIR_MUTED)); ly += 1
    ly += 1

    sale_label = "ON" if c.compute_for_sale else "OFF"
    sale_p = PAIR_ACCENT if c.compute_for_sale else PAIR_MUTED
    safe_addstr(win, ly, lx, "COMPUTE SALES  [S: toggle]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); ly += 1
    safe_addstr(win, ly, lx, f"Selling : [{sale_label}]", curses.color_pair(sale_p) | curses.A_BOLD)
    if c.compute_for_sale and c.compute_capacity > 0:
        safe_addstr(win, ly, lx + 18, f"~${compute_sale_revenue(gs, c):,}/mo",
                    curses.color_pair(PAIR_ACCENT))
    ly += 1
    if c.datacenter_tier <= 0:
        safe_addstr(win, ly, lx, "(needs a datacenter)", curses.color_pair(PAIR_MUTED)); ly += 1

    # ── Right column: GPU shop + inventory ─────────────────────
    rx = mid + 2
    ry = y
    tok_mult = get_token_cost_multiplier(gs, c)
    safe_addstr(win, ry, rx, "GPUs  [↑↓ select, G: buy]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); ry += 1
    safe_addstr(win, ry, rx, f"Owned: {len(c.gpu_inventory)}   "
                f"Dev token cost: {tok_mult:.0%}",
                curses.color_pair(PAIR_ACCENT)); ry += 1
    hline(win, ry, rx, w - rx - 2, PAIR_BORDER); ry += 1

    avail = {g["name"] for g in available_gpus(gs)}
    ui.infra_gpu_sel = max(0, min(ui.infra_gpu_sel, len(GPU_GENERATIONS) - 1))
    for i, g in enumerate(GPU_GENERATIONS):
        if ry >= h - 5:
            break
        unlocked = g["name"] in avail
        is_sel = (i == ui.infra_gpu_sel)
        owned_n = sum(1 for gp in c.gpu_inventory if isinstance(gp, dict) and gp.get("name") == g["name"])
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        lock = "" if unlocked else f" 🔒{g['year']}"
        own = f" x{owned_n}" if owned_n else ""
        safe_addstr(win, ry, rx, " " * (w - rx - 2), curses.color_pair(rp))
        safe_addstr(win, ry, rx,
                    f"{prefix}{g['name']:<14} ${g['cost']:>6,}  -{g['token_reduction']:.0%}{own}{lock}",
                    curses.color_pair(rp if is_sel else (PAIR_ACCENT if unlocked else PAIR_MUTED)))
        ry += 1

    safe_addstr(win, h - 3, 2,
                "P:hosting  D:datacenter  S:compute-sale  ↑↓:GPU  G:buy GPU  Esc:back",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 2, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_finance_prompt(win, gs: GameState, ui, h, w):
    c = gs.companies[ui.selected] if gs.companies and 0 <= ui.selected < len(gs.companies) else None
    action_label = "DEPOSIT to Company" if ui.view == "deposit" else "WITHDRAW to Personal"
    y = h // 2 - 4
    bw = 50
    bx = (w - bw) // 2
    draw_box(win, y, bx, 7, bw, PAIR_BORDER, action_label, PAIR_TITLE)
    y += 2
    if c:
        safe_addstr(win, y, bx + 3, f"Company: {c.name}", curses.color_pair(PAIR_MUTED))
        y += 1
        if ui.view == "deposit":
            safe_addstr(win, y, bx + 3,
                        f"Personal: ${gs.founder.personal_cash:,.0f}  →  Co: ${c.cash:,}",
                        curses.color_pair(PAIR_MUTED))
        else:
            safe_addstr(win, y, bx + 3,
                        f"Co: ${c.cash:,}  →  Personal: ${gs.founder.personal_cash:,.0f}",
                        curses.color_pair(PAIR_MUTED))
        y += 1
        safe_addstr(win, y, bx + 3, f"Amount: ${ui.finance_amount}█",
                    curses.color_pair(PAIR_INPUT_FOCUS) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2,
                "Type amount and Enter to confirm  |  Esc: cancel",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 4, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_new_company_form(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " NEW COMPANY ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    bw = min(72, w - 4)
    bx = (w - bw) // 2
    draw_box(win, y, bx, len(ui.new_fields) * 3 + 6, bw, PAIR_BORDER,
             "COMPANY SETUP", PAIR_TITLE)
    y += 1

    for i, f in enumerate(ui.new_fields):
        is_focus = (i == ui.new_focused)
        fy = y + i * 3
        la = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
              else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_focus else "  "
        safe_addstr(win, fy, bx + 2, f"{prefix}{f['label']}", la)

        if f["type"] == "options":
            opts = f["options"]
            sel  = f["selected"]
            prev = f"‹ {opts[(sel-1)%len(opts)][:14]}"
            curr = f"  [{opts[sel][:24]}]  "
            nxt  = f"{opts[(sel+1)%len(opts)][:14]} ›"
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, fy + 1, bx + 4, prev[:16], curses.color_pair(PAIR_MUTED))
            safe_addstr(win, fy + 1, bx + 20, curr,
                        curses.color_pair(ip) | (curses.A_BOLD if is_focus else 0))
            safe_addstr(win, fy + 1, bx + 48, nxt[:16], curses.color_pair(PAIR_MUTED))

            # Show focus description inline when this field is focused
            if is_focus and f["label"] == "Focus Area":
                focus_d = get_focus_data(opts[sel])
                if focus_d:
                    desc = focus_d["desc"][:bw - 8]
                    safe_addstr(win, fy + 2, bx + 4, desc, curses.color_pair(PAIR_MUTED))
            elif is_focus and f["label"] == "Legal Structure":
                legal_d = get_legal_data(opts[sel])
                if legal_d:
                    desc = legal_d["desc"][:bw - 8]
                    safe_addstr(win, fy + 2, bx + 4, desc, curses.color_pair(PAIR_MUTED))
        else:
            val = f["value"]
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, fy + 1, bx + 2, f" {val:<{bw-8}} "[:bw - 4],
                        curses.color_pair(ip))

    btn_y = y + len(ui.new_fields) * 3 + 2
    safe_addstr(win, btn_y, bx + 4, "[ Create Company → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
    safe_addstr(win, btn_y, bx + 26, "[ Cancel ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)

    if ui.message:
        mp = PAIR_ACCENT if "created" in ui.message.lower() else PAIR_DANGER
        safe_addstr(win, btn_y + 2, bx + 4, ui.message,
                    curses.color_pair(mp) | curses.A_BOLD)

    safe_addstr(win, h - 3, 2,
                "↑↓: field  |  ◄/►: options  |  Type: text  |  Enter: create  |  Esc: back",
                curses.color_pair(PAIR_MUTED))


def _short_legal(name: str) -> str:
    for s in COMPANY_LEGAL_STRUCTURES:
        if s["name"] == name:
            return s["short"]
    # Legacy names
    short_map = {
        "Solo Hustle": "Solo", "Tiny Studio": "Studio", "Indie Lab": "Indie Lab",
        "Garage Startup": "Garage", "Growth Startup": "Growth",
        "Holding Company": "Holding", "Mega Corp": "Mega Corp",
    }
    return short_map.get(name, name[:12])
