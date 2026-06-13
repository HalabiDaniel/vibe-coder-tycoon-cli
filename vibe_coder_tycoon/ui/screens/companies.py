import curses
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import (
    COMPANY_LEGAL_STYLES, COMPANY_FOCUS_AREAS, FUNDING_STYLES,
    RISK_APPETITES, MONTH_NAMES, AUTO_DEPOSIT_CYCLE,
)
from ...models import GameState


# ─────────────────────── COMPANIES TAB ────────────────────────

@dataclass
class CompaniesUIState:
    view: str = "list"       # "list" | "detail" | "new" | "deposit" | "withdraw"
    selected: int = 0
    new_fields: list = field(default_factory=lambda: [
        {"label": "Company Name",     "value": "", "max": 30, "type": "text"},
        {"label": "Legal Style",      "value": "", "type": "options",
         "options": COMPANY_LEGAL_STYLES, "selected": 0},
        {"label": "Focus Area",       "value": "", "type": "options",
         "options": COMPANY_FOCUS_AREAS,  "selected": 0},
        {"label": "Funding Style",    "value": "", "type": "options",
         "options": FUNDING_STYLES,        "selected": 0},
        {"label": "Risk Appetite",    "value": "", "type": "options",
         "options": RISK_APPETITES,        "selected": 0},
        {"label": "Starting Cash ($)", "value": "2000", "max": 10, "type": "text"},
    ])
    new_focused: int = 0
    message: str = ""
    finance_amount: str = ""   # typed amount for deposit/withdraw


def draw_companies(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3

    if ui.view == "new":
        _draw_new_company_form(win, gs, ui)
        return

    if ui.view in ("deposit", "withdraw"):
        _draw_finance_prompt(win, gs, ui, h, w)
        return

    # Header
    safe_addstr(win, y, 2, " COMPANIES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 16,
                f"({len(gs.companies)} total, {len(gs.active_companies())} active)",
                curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y, w - 20, "[ N: New Company ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    # List header
    header = (f"  {'COMPANY NAME':<26} {'LEGAL STYLE':<16} {'FOCUS':<16} "
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
        row = (f"  {c.name:<26} {c.legal_style:<16} {c.focus_area:<16} "
               f"${c.cash:>8,} ${c.monthly_revenue:>7,}  {status}")
        safe_addstr(win, y, 1, " " * (w - 2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))
        y += 1

    y += 1
    hline(win, y, 1, w - 2, PAIR_BORDER)
    y += 2

    # Detail panel for selected company
    if gs.companies and 0 <= ui.selected < len(gs.companies):
        c = gs.companies[ui.selected]
        _draw_company_detail(win, gs, ui, c, y, h, w)

    # Status bar
    safe_addstr(win, h - 4, 2,
                "Up/Down:select  N:new  D:deposit  W:withdraw  T:auto-deposit%  C:cover-personal",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_company_detail(win, gs: GameState, ui, c, y, h, w):
    """Render balance sheet + finance toggles + action buttons for selected company."""
    f = gs.founder
    profit = c.monthly_revenue - c.monthly_expenses
    pp = PAIR_ACCENT if profit >= 0 else PAIR_DANGER
    mid = w // 2

    # Left column: balance sheet
    detail_rows = [
        ("Founded",       f"{MONTH_NAMES[c.founded_month-1]} {c.founded_year}"),
        ("Risk Appetite", c.risk_appetite),
        ("Funding",       c.funding_style),
        ("Company Cash",  f"${c.cash:,}"),
        ("Monthly Rev",   f"${c.monthly_revenue:,}"),
        ("Monthly Exp",   f"${c.monthly_expenses:,}"),
        ("Net / Month",   f"${profit:+,}"),
        ("Debt",          f"${c.debt:,}" if c.debt else "None"),
        ("Valuation",     f"${c.valuation:,}"),
        ("Office Level",  str(c.office_level)),
        ("Reputation",    f"{c.reputation}/100"),
        ("Mood",          f"{c.mood}%"),
        ("Months Neg.",   str(c.months_negative) if c.months_negative else "—"),
    ]
    for label, val in detail_rows:
        if y >= h - 8:
            break
        safe_addstr(win, y, 4, f"{label:<18}", curses.color_pair(PAIR_MUTED))
        vp = pp if "Net" in label else PAIR_ACCENT
        safe_addstr(win, y, 22, val, curses.color_pair(vp) | curses.A_BOLD)
        y += 1

    y += 1

    # Finance toggles (right side of detail)
    auto_label = f"{c.auto_deposit_pct}%" if c.auto_deposit_pct else "OFF"
    cover_label = "ON " if c.cover_from_personal else "OFF"
    cover_pair  = PAIR_ACCENT if c.cover_from_personal else PAIR_MUTED
    auto_pair   = PAIR_ACCENT if c.auto_deposit_pct else PAIR_MUTED

    if y < h - 8:
        safe_addstr(win, y, 4,
                    f"Auto-deposit:  ", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 19, f"[{auto_label:>4}]",
                    curses.color_pair(auto_pair) | curses.A_BOLD)
        safe_addstr(win, y, 28, "T: cycle (0→10→25→50%)",
                    curses.color_pair(PAIR_MUTED))
        y += 1

    if y < h - 8:
        safe_addstr(win, y, 4,
                    f"Cover personal:", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 20, f"[{cover_label}]",
                    curses.color_pair(cover_pair) | curses.A_BOLD)
        safe_addstr(win, y, 28, "C: toggle",
                    curses.color_pair(PAIR_MUTED))
        y += 1

    # Personal cash reminder
    if y < h - 6:
        safe_addstr(win, y, 4,
                    f"Personal Cash: ${f.personal_cash:,.0f}",
                    curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1

    # Action buttons
    if y < h - 5:
        actions = [
            "[ D: Deposit→Co ]",
            "[ W: Withdraw→Personal ]",
            "[ Add Project ]",
            "[ Hire Employee ]",
        ]
        ax = 4
        for a in actions:
            if ax + len(a) + 2 > w - 4:
                break
            safe_addstr(win, y, ax, a, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ax += len(a) + 2


def _draw_finance_prompt(win, gs: GameState, ui, h, w):
    """Overlay prompt for deposit/withdraw amount."""
    c = gs.companies[ui.selected] if gs.companies and 0 <= ui.selected < len(gs.companies) else None
    action_label = "DEPOSIT to Company" if ui.view == "deposit" else "WITHDRAW to Personal"
    y = h // 2 - 4
    bw = 50
    bx = (w - bw) // 2
    draw_box(win, y, bx, 7, bw, PAIR_BORDER, action_label, PAIR_TITLE)
    y += 2
    if c:
        safe_addstr(win, y, bx + 3,
                    f"Company: {c.name}", curses.color_pair(PAIR_MUTED))
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
                "Type amount and press Enter to confirm  |  Esc: cancel",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 4, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


def _draw_new_company_form(win, gs: GameState, ui: CompaniesUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " NEW COMPANY ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    bw = min(60, w - 4)
    bx = (w - bw) // 2
    draw_box(win, y, bx, len(ui.new_fields) * 3 + 4, bw, PAIR_BORDER,
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
            curr = f"  [{opts[sel][:20]}]  "
            nxt  = f"{opts[(sel+1)%len(opts)][:14]} ›"
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, fy + 1, bx + 4, prev[:16], curses.color_pair(PAIR_MUTED))
            safe_addstr(win, fy + 1, bx + 20, curr,
                        curses.color_pair(ip) | (curses.A_BOLD if is_focus else 0))
            safe_addstr(win, fy + 1, bx + 44, nxt[:16], curses.color_pair(PAIR_MUTED))
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
                "Up/Down: field  |  ◄/►: options  |  Type: text  |  Enter: create  |  Esc: back",
                curses.color_pair(PAIR_MUTED))
