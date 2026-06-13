#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║         VIBE CODER TYCOON  —  Terminal Demo          ║
║     A pixel-art tycoon game for the AI dev era       ║
╚══════════════════════════════════════════════════════╝
  Run:  python3 vibe_coder_tycoon.py
  Quit: Q  |  Navigate: Arrow Keys / Tab / Enter
"""

import curses
import random
import time
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────── COLOUR PALETTE ───────────────────────
# Using 256-color xterm palette where available.
# C_* constants are (fg, bg) pairs assigned to curses color pairs.

PAIR_TOPBAR      = 1   # Top HUD bar
PAIR_TAB_ACTIVE  = 2   # Active tab
PAIR_TAB_INACTIVE= 3   # Inactive tab
PAIR_PANEL       = 4   # Main panel background
PAIR_HIGHLIGHT   = 5   # Selected row / focused element
PAIR_ACCENT      = 6   # Green accent (money, good news)
PAIR_DANGER      = 7   # Red accent (bad news, low stats)
PAIR_WARN        = 8   # Yellow warning
PAIR_TITLE       = 9   # Section titles
PAIR_BORDER      = 10  # Box-drawing borders
PAIR_MUTED       = 11  # Dimmed / secondary text
PAIR_INPUT_FOCUS = 12  # Focused text field
PAIR_INPUT_IDLE  = 13  # Idle text field
PAIR_BUTTON      = 14  # Button
PAIR_BUTTON_FOCUS= 15  # Focused button
PAIR_BADGE_BLUE  = 16  # Blue status badge
PAIR_BADGE_GREEN = 17  # Green status badge
PAIR_BADGE_AMBER = 18  # Amber status badge
PAIR_BADGE_RED   = 19  # Red status badge
PAIR_TICKER      = 20  # Ticker / event feed text
PAIR_LOGO        = 21  # Logo gradient-like colour

def init_colors():
    curses.start_color()
    curses.use_default_colors()

    def p(pair, fg, bg): curses.init_pair(pair, fg, bg)

    # We rely on 256-colour support (most modern terminals)
    # Deep navy background: 17 = dark blue, 233 = near-black
    # Accent green: 82, amber: 214, cyan: 51, soft white: 252

    BG       = 17    # deep navy
    BG2      = 18    # slightly lighter navy (panel interior)
    BG_TAB   = 234   # very dark, for inactive tabs
    FG       = 252   # near-white text
    FG_DIM   = 245   # muted grey text
    GREEN    = 82
    RED      = 196
    AMBER    = 214
    CYAN     = 51
    BLUE     = 33
    PURPLE   = 141
    PINK     = 205
    LOGO_FG  = 214   # amber for logo

    p(PAIR_TOPBAR,       FG,     17)
    p(PAIR_TAB_ACTIVE,   232,    82)    # black on green
    p(PAIR_TAB_INACTIVE, FG_DIM, BG_TAB)
    p(PAIR_PANEL,        FG,     232)   # near-black panel
    p(PAIR_HIGHLIGHT,    232,    CYAN)  # black on cyan
    p(PAIR_ACCENT,       GREEN,  232)
    p(PAIR_DANGER,       RED,    232)
    p(PAIR_WARN,         AMBER,  232)
    p(PAIR_TITLE,        CYAN,   232)
    p(PAIR_BORDER,       BLUE,   232)
    p(PAIR_MUTED,        FG_DIM, 232)
    p(PAIR_INPUT_FOCUS,  232,    CYAN)
    p(PAIR_INPUT_IDLE,   FG,     235)
    p(PAIR_BUTTON,       232,    BLUE)
    p(PAIR_BUTTON_FOCUS, 232,    GREEN)
    p(PAIR_BADGE_BLUE,   232,    BLUE)
    p(PAIR_BADGE_GREEN,  232,    GREEN)
    p(PAIR_BADGE_AMBER,  232,    AMBER)
    p(PAIR_BADGE_RED,    232,    RED)
    p(PAIR_TICKER,       AMBER,  232)
    p(PAIR_LOGO,         LOGO_FG,17)

# ─────────────────────── DUMMY GAME DATA ───────────────────────

TABS = ["Dashboard", "Projects", "New Project", "Employees", "Finance", "Market", "Events"]

AI_MODELS = [
    "GPT-4o",
    "Claude 3.5 Sonnet",
    "Gemini 1.5 Pro",
    "Llama 3.1 70B",
    "Mistral Large",
    "DeepSeek Coder V2",
    "Grok 2",
    "(Build Your Own)",
]

PROJECT_TYPES = [
    "SaaS Web App",
    "Mobile App",
    "Browser Extension",
    "CLI Tool",
    "API / Backend",
    "AI Wrapper",
    "Discord Bot",
    "No-Code Template",
]

TECH_STACKS = [
    "Next.js + Vercel",
    "React Native + Expo",
    "Python + FastAPI",
    "Node.js + Express",
    "Svelte + Cloudflare",
    "Electron Desktop",
    "Bubble.io",
    "Replit + Nix",
]

NICHES = [
    "Productivity",
    "Fintech",
    "Healthcare",
    "EdTech",
    "E-Commerce",
    "Social / Community",
    "Gaming Tools",
    "Developer Tools",
    "Content Creation",
    "B2B Automation",
]

@dataclass
class Project:
    name: str
    ptype: str
    model: str
    stack: str
    niche: str
    status: str       # "In Dev", "Launched", "Growing", "Sunset", "Failed"
    progress: int     # 0-100
    revenue: int      # monthly USD
    users: int
    moral: int        # 0-100 (mental health of dev team)
    tokens_used: int  # AI token count in thousands

@dataclass
class Employee:
    name: str
    role: str
    level: int        # 1-5
    salary: int       # monthly USD
    mood: int         # 0-100
    skill: int        # 0-100
    hired_year: int

@dataclass
class GameState:
    player_name: str = "DanielH"
    company_name: str = "CedarTech Inc."
    year: int = 2024
    month: int = 3
    cash: int = 12_400
    monthly_revenue: int = 3_200
    monthly_expenses: int = 1_850
    reputation: int = 67
    compute_credits: int = 4_200
    mental_health: int = 74
    office_level: int = 2        # 1=Bedroom, 2=Co-work, 3=Office, 4=HQ
    active_ai_sub: str = "Claude 3.5 Sonnet"
    projects: list = field(default_factory=list)
    employees: list = field(default_factory=list)
    events: list = field(default_factory=list)
    loans: list = field(default_factory=list)

def make_dummy_state() -> GameState:
    gs = GameState()
    gs.projects = [
        Project("FormFlux", "SaaS Web App", "GPT-4o", "Next.js + Vercel",
                "Productivity", "Growing", 100, 1_850, 342, 88, 14_200),
        Project("PocketLedger", "Mobile App", "Claude 3.5 Sonnet", "React Native + Expo",
                "Fintech", "In Dev", 63, 0, 0, 71, 8_750),
        Project("CronBot Pro", "Discord Bot", "Llama 3.1 70B", "Node.js + Express",
                "Developer Tools", "Launched", 100, 440, 91, 55, 3_100),
        Project("NicheNest", "AI Wrapper", "GPT-4o", "Next.js + Vercel",
                "Content Creation", "Failed", 100, 0, 0, 22, 21_400),
        Project("StudyStack", "SaaS Web App", "Gemini 1.5 Pro", "Svelte + Cloudflare",
                "EdTech", "In Dev", 28, 0, 0, 90, 2_300),
    ]
    gs.employees = [
        Employee("Amma Osei",   "Frontend Dev",   3, 3_200, 82, 71, 2023),
        Employee("Taro Naka",   "Backend Dev",    2, 2_600, 68, 58, 2024),
        Employee("Luna Park",   "UI/UX Designer", 2, 2_400, 91, 65, 2023),
        Employee("Ike Okafor",  "AI Engineer",    4, 4_100, 75, 84, 2022),
        Employee("Zara Malik",  "Growth Hacker",  1, 1_900, 60, 44, 2024),
    ]
    gs.events = [
        ("🔥", "FormFlux hit $1.8K MRR milestone!",        "good",   "Mar 2024"),
        ("⚠️", "Compute costs spiked 34% this month.",      "warn",   "Mar 2024"),
        ("💸", "Loan repayment due: $800",                  "warn",   "Mar 2024"),
        ("📰", "AI bubble concerns circulating on HN.",     "neutral","Feb 2024"),
        ("🚀", "Ike Okafor levelled up to AI Eng IV!",     "good",   "Feb 2024"),
        ("❌", "NicheNest sunset — $21K tokens wasted.",    "bad",    "Jan 2024"),
        ("💬", "New user review: 'FormFlux saved my week'", "good",   "Jan 2024"),
        ("📉", "Zara Malik mood dropped to 60.",            "warn",   "Jan 2024"),
        ("🏦", "Micro-loan approved: $5,000 @ 9% APR",     "good",   "Dec 2023"),
        ("🛠️", "CronBot Pro launched on Product Hunt.",     "good",   "Dec 2023"),
    ]
    gs.loans = [
        {"lender": "StartupBank",  "amount": 5_000, "rate": 9.0,  "remaining": 3_800, "monthly": 420},
        {"lender": "MicroVenture", "amount": 2_500, "rate": 14.5, "remaining": 2_100, "monthly": 260},
    ]
    return gs

# ─────────────────────── DRAWING HELPERS ───────────────────────

def safe_addstr(win, y, x, text, attr=0):
    """Write string, silently ignoring out-of-bounds errors."""
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x < 0:
            return
        available = w - x - 1
        if available <= 0:
            return
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass

def hline(win, y, x, width, pair):
    safe_addstr(win, y, x, "─" * width, curses.color_pair(pair))

def box_title(win, y, x, w, title, pair_border, pair_title):
    safe_addstr(win, y,   x, "┌" + "─"*(w-2) + "┐", curses.color_pair(pair_border))
    t = f" {title} "
    tx = x + (w - len(t)) // 2
    safe_addstr(win, y, tx, t, curses.color_pair(pair_title) | curses.A_BOLD)

def box_bottom(win, y, x, w, pair_border):
    safe_addstr(win, y, x, "└" + "─"*(w-2) + "┘", curses.color_pair(pair_border))

def box_side(win, y, x, w, pair_border):
    safe_addstr(win, y, x,   "│", curses.color_pair(pair_border))
    safe_addstr(win, y, x+w-1,"│", curses.color_pair(pair_border))

def progress_bar(win, y, x, width, pct, pair_fill, pair_empty):
    filled = int(width * pct / 100)
    safe_addstr(win, y, x, "█" * filled,           curses.color_pair(pair_fill))
    safe_addstr(win, y, x+filled, "░"*(width-filled), curses.color_pair(pair_empty))

def badge(win, y, x, text, pair):
    safe_addstr(win, y, x, f" {text} ", curses.color_pair(pair) | curses.A_BOLD)

def status_pair(status):
    return {
        "In Dev":   PAIR_BADGE_BLUE,
        "Launched": PAIR_BADGE_AMBER,
        "Growing":  PAIR_BADGE_GREEN,
        "Failed":   PAIR_BADGE_RED,
        "Sunset":   PAIR_BADGE_RED,
    }.get(status, PAIR_BADGE_BLUE)

# ─────────────────────── TOP BAR ───────────────────────────────

def draw_topbar(win, gs: GameState):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(0, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))

    # Logo
    logo = " ⚡ VIBE CODER TYCOON "
    safe_addstr(win, 0, 1, logo, curses.color_pair(PAIR_LOGO) | curses.A_BOLD)

    # Stats strip
    profit = gs.monthly_revenue - gs.monthly_expenses
    profit_str = f"+${profit:,}" if profit >= 0 else f"-${abs(profit):,}"
    profit_pair = PAIR_ACCENT if profit >= 0 else PAIR_DANGER

    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    date_str = f"{month_names[gs.month-1]} {gs.year}"

    stats = [
        (f"  {gs.company_name}",          curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD),
        (f"   📅 {date_str}",              curses.color_pair(PAIR_TOPBAR)),
        (f"   💰 ${gs.cash:,}",            curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD),
        (f"   📈 {profit_str}/mo",         curses.color_pair(profit_pair) | curses.A_BOLD),
        (f"   🖥️  {gs.compute_credits:,}cr", curses.color_pair(PAIR_TOPBAR)),
        (f"   🧠 MH:{gs.mental_health}%",  curses.color_pair(PAIR_TOPBAR)),
        (f"   ⭐ Rep:{gs.reputation}",     curses.color_pair(PAIR_TOPBAR)),
        (f"   🏢 {['','Bedroom','Co-Work','Office','HQ'][gs.office_level]}",
                                            curses.color_pair(PAIR_TOPBAR)),
    ]
    cx = len(logo) + 2
    for text, attr in stats:
        safe_addstr(win, 0, cx, text, attr)
        cx += len(text)

    # Right: player name
    pname = f" 👤 {gs.player_name}  "
    safe_addstr(win, 0, w - len(pname) - 1, pname,
                curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD)

# ─────────────────────── TAB BAR ───────────────────────────────

def draw_tabs(win, active_tab: int):
    h, w = win.getmaxyx()
    # Second row
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(1, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))

    cx = 2
    for i, tab in enumerate(TABS):
        label = f"  {tab}  "
        if i == active_tab:
            safe_addstr(win, 1, cx, label,
                        curses.color_pair(PAIR_TAB_ACTIVE) | curses.A_BOLD)
        else:
            safe_addstr(win, 1, cx, label,
                        curses.color_pair(PAIR_TAB_INACTIVE))
        cx += len(label)

    # Key hints on right
    hints = " Tab:Switch  Q:Quit  Enter:Select  Arrow:Nav "
    safe_addstr(win, 1, w - len(hints) - 1, hints,
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── DASHBOARD TAB ────────────────────────

def draw_dashboard(win, gs: GameState):
    h, w = win.getmaxyx()
    y_start = 3
    mid = w // 2

    # ── Left column ──────────────────────────────────────────
    lw = mid - 2

    # Overview panel
    safe_addstr(win, y_start,   2, "┌" + "─"*(lw-2) + "┐", curses.color_pair(PAIR_BORDER))
    t = " COMPANY OVERVIEW "
    safe_addstr(win, y_start, 2+(lw-len(t))//2, t,
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)

    rows = [
        ("Active Projects",  str(len([p for p in gs.projects if p.status not in ("Failed","Sunset")]))),
        ("Total Employees",  str(len(gs.employees))),
        ("Monthly Revenue",  f"${gs.monthly_revenue:,}"),
        ("Monthly Expenses", f"${gs.monthly_expenses:,}"),
        ("Net Profit/Loss",  f"${gs.monthly_revenue - gs.monthly_expenses:+,}"),
        ("Cash on Hand",     f"${gs.cash:,}"),
        ("Active AI Sub",    gs.active_ai_sub),
        ("Compute Credits",  f"{gs.compute_credits:,} cr"),
        ("Reputation",       f"{gs.reputation}/100"),
        ("Mental Health",    f"{gs.mental_health}/100"),
    ]
    for i, (label, val) in enumerate(rows):
        ry = y_start + 1 + i
        safe_addstr(win, ry, 2, "│", curses.color_pair(PAIR_BORDER))
        safe_addstr(win, ry, 4, label, curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ry, 4+24, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        safe_addstr(win, ry, 2+lw-1, "│", curses.color_pair(PAIR_BORDER))
    bot = y_start + 1 + len(rows)
    safe_addstr(win, bot, 2, "└" + "─"*(lw-2) + "┘", curses.color_pair(PAIR_BORDER))

    # Stat bars
    bar_y = bot + 2
    for label, val, maxval, fill_pair in [
        ("Reputation  ", gs.reputation,    100, PAIR_ACCENT),
        ("Mental Health", gs.mental_health, 100, PAIR_BADGE_BLUE),
        ("Cash Flow   ", min(100, int((gs.monthly_revenue / max(1, gs.monthly_expenses))*50)),
                                            100, PAIR_BADGE_GREEN),
    ]:
        safe_addstr(win, bar_y, 2, f" {label} ", curses.color_pair(PAIR_MUTED))
        bx = 2 + 15
        bw = lw - 20
        progress_bar(win, bar_y, bx, bw, val, fill_pair, PAIR_MUTED)
        safe_addstr(win, bar_y, bx + bw + 1, f"{val:3d}%", curses.color_pair(PAIR_MUTED))
        bar_y += 1

    # Loans panel
    bar_y += 1
    loan_h = len(gs.loans) + 2
    safe_addstr(win, bar_y, 2, "┌" + "─"*(lw-2) + "┐", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, bar_y, 2+(lw-12)//2, " ACTIVE LOANS ",
                curses.color_pair(PAIR_WARN) | curses.A_BOLD)
    for i, loan in enumerate(gs.loans):
        ry = bar_y + 1 + i
        safe_addstr(win, ry, 2, "│", curses.color_pair(PAIR_BORDER))
        info = (f"  {loan['lender']:<14} "
                f"${loan['remaining']:,} remaining  "
                f"{loan['rate']}% APR  "
                f"${loan['monthly']}/mo")
        safe_addstr(win, ry, 4, info, curses.color_pair(PAIR_WARN))
        safe_addstr(win, ry, 2+lw-1, "│", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, bar_y+loan_h-1, 2, "└" + "─"*(lw-2) + "┘",
                curses.color_pair(PAIR_BORDER))

    # ── Right column ─────────────────────────────────────────
    rx = mid + 1
    rw = w - mid - 3

    # Event feed
    safe_addstr(win, y_start, rx, "┌" + "─"*(rw-2) + "┐", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, y_start, rx+(rw-14)//2, " EVENT FEED ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)

    event_pairs = {"good": PAIR_ACCENT, "warn": PAIR_WARN, "bad": PAIR_DANGER, "neutral": PAIR_MUTED}
    for i, (icon, msg, kind, date) in enumerate(gs.events[:min(10, h-y_start-4)]):
        ry = y_start + 1 + i
        safe_addstr(win, ry, rx, "│", curses.color_pair(PAIR_BORDER))
        epair = event_pairs.get(kind, PAIR_MUTED)
        safe_addstr(win, ry, rx+2, f"{icon} ", curses.color_pair(epair))
        max_msg = rw - 16
        safe_addstr(win, ry, rx+5, msg[:max_msg], curses.color_pair(epair))
        safe_addstr(win, ry, rx+rw-10, date[:8], curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ry, rx+rw-1, "│", curses.color_pair(PAIR_BORDER))

    ef_bot = y_start + 1 + min(10, h-y_start-4)
    safe_addstr(win, ef_bot, rx, "└" + "─"*(rw-2) + "┘", curses.color_pair(PAIR_BORDER))

    # Next-tick hint
    nt_y = ef_bot + 2
    safe_addstr(win, nt_y, rx+2,
                "[ Press N to advance one month ]",
                curses.color_pair(PAIR_BADGE_AMBER) | curses.A_BOLD)

# ─────────────────────── PROJECTS TAB ─────────────────────────

def draw_projects(win, gs: GameState, selected_row: int):
    h, w = win.getmaxyx()
    y = 3

    # Header
    header = (f"  {'PROJECT NAME':<18} {'TYPE':<18} {'MODEL':<20} "
              f"{'STATUS':<10} {'PROG':>4} {'MRR':>7} {'USERS':>7}  ")
    hline(win, y, 1, w-2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    for i, p in enumerate(gs.projects):
        is_sel = (i == selected_row)
        row_pair = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL

        mrr = f"${p.revenue:,}" if p.revenue else "—"
        users = f"{p.users:,}" if p.users else "—"
        prog = f"{p.progress}%" if p.status == "In Dev" else ("✓" if p.progress==100 else "—")

        row = (f"  {p.name:<18} {p.ptype:<18} {p.model:<20} "
               f"{'':10} {prog:>4} {mrr:>7} {users:>7}  ")
        safe_addstr(win, y, 1, " " * (w-2), curses.color_pair(row_pair))
        safe_addstr(win, y, 2, row, curses.color_pair(row_pair))

        # Inline status badge
        bx = 2 + 18 + 18 + 20 + 2 + 3
        badge(win, y, bx, p.status, status_pair(p.status))

        # Progress bar for in-dev
        if p.status == "In Dev":
            pbx = bx + len(p.status) + 4
            progress_bar(win, y, pbx, 12, p.progress,
                         PAIR_BADGE_BLUE, PAIR_MUTED)
        y += 1

    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    # Detail panel for selected project
    if 0 <= selected_row < len(gs.projects):
        p = gs.projects[selected_row]
        safe_addstr(win, y, 2, f" Detail: {p.name} ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        y += 1
        details = [
            ("Stack",     p.stack),
            ("Niche",     p.niche),
            ("AI Model",  p.model),
            ("MRR",       f"${p.revenue:,}"),
            ("Users",     f"{p.users:,}"),
            ("Tokens Used", f"{p.tokens_used:,}K"),
            ("Team Morale", f"{p.moral}%"),
        ]
        col_w = (w-4) // 3
        for j, (k, v) in enumerate(details):
            col = j % 3
            row_off = j // 3
            dx = 4 + col * col_w
            safe_addstr(win, y+row_off, dx, f"{k}: ", curses.color_pair(PAIR_MUTED))
            safe_addstr(win, y+row_off, dx+len(k)+2, v, curses.color_pair(PAIR_ACCENT))

        y += (len(details)-1)//3 + 2
        actions = ["[ Launch ]", "[ Sunset ]", "[ Boost (200cr) ]", "[ View Analytics ]"]
        ax = 4
        for act in actions:
            safe_addstr(win, y, ax, act, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ax += len(act) + 2

    y += 2
    safe_addstr(win, y, 2, "Up/Down: select project  |  Enter: action",
                curses.color_pair(PAIR_MUTED))

# ──────────────── NEW PROJECT FORM TAB ────────────────────────

@dataclass
class NewProjectForm:
    fields: list = field(default_factory=lambda: [
        {"label": "Project Name",  "value": "",        "max": 30,
         "hint": "e.g. FormFlux, NicheNest, CronBot"},
        {"label": "Project Type",  "value": "",        "max": 0,
         "options": PROJECT_TYPES,  "selected": 0},
        {"label": "AI Model",      "value": "",        "max": 0,
         "options": AI_MODELS,      "selected": 0},
        {"label": "Tech Stack",    "value": "",        "max": 0,
         "options": TECH_STACKS,    "selected": 0},
        {"label": "Niche",         "value": "",        "max": 0,
         "options": NICHES,         "selected": 0},
        {"label": "Budget (USD)",  "value": "500",     "max": 10,
         "hint": "tokens / initial compute budget"},
        {"label": "Timeline (weeks)", "value": "4",    "max": 3,
         "hint": "estimated dev weeks"},
    ])
    focused: int = 0
    submitted: bool = False
    message: str = ""

def draw_new_project(win, gs: GameState, form: NewProjectForm):
    h, w = win.getmaxyx()
    y = 3

    safe_addstr(win, y, 2, " NEW PROJECT SETUP ", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 2,
                "Configure your next vibe-coded masterpiece below.",
                curses.color_pair(PAIR_MUTED))
    y += 2

    fw = min(70, w-6)
    fx = (w - fw) // 2

    # Box
    safe_addstr(win, y, fx, "┌" + "─"*(fw-2) + "┐", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, y, fx+(fw-16)//2, " PROJECT CREATOR ",
                curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1

    for i, field_def in enumerate(form.fields):
        is_focus = (i == form.focused)
        label = field_def["label"]
        inner_y = y + i*3

        # Left bar
        safe_addstr(win, inner_y,   fx, "│", curses.color_pair(PAIR_BORDER))
        safe_addstr(win, inner_y+1, fx, "│", curses.color_pair(PAIR_BORDER))
        # Right bar
        safe_addstr(win, inner_y,   fx+fw-1, "│", curses.color_pair(PAIR_BORDER))
        safe_addstr(win, inner_y+1, fx+fw-1, "│", curses.color_pair(PAIR_BORDER))

        # Label
        label_attr = (curses.color_pair(PAIR_ACCENT)|curses.A_BOLD if is_focus
                      else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_focus else "  "
        safe_addstr(win, inner_y, fx+2, f"{prefix}{label}", label_attr)

        # Input / selector
        if "options" in field_def:
            opts = field_def["options"]
            sel  = field_def["selected"]
            # Show prev / current / next
            prev_s = f"‹ {opts[(sel-1) % len(opts)][:18]}"
            curr_s = f"  [{opts[sel][:22]}]  "
            next_s = f"{opts[(sel+1) % len(opts)][:18]} ›"

            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            safe_addstr(win, inner_y+1, fx+4, prev_s[:15],
                        curses.color_pair(PAIR_MUTED))
            safe_addstr(win, inner_y+1, fx+20, curr_s,
                        curses.color_pair(ip)|(curses.A_BOLD if is_focus else 0))
            safe_addstr(win, inner_y+1, fx+46, next_s[:15],
                        curses.color_pair(PAIR_MUTED))
            if is_focus:
                safe_addstr(win, inner_y, fx+fw-24,
                            "◄/► to change",
                            curses.color_pair(PAIR_MUTED))
        else:
            ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
            val = field_def["value"]
            hint = field_def.get("hint","")
            disp = val if val else hint
            is_hint = not val
            vattr = curses.color_pair(PAIR_MUTED) if is_hint else curses.color_pair(ip)
            box = f" {disp:<{fw-8}} "
            safe_addstr(win, inner_y+1, fx+2, box[:fw-4], vattr)
            if is_focus:
                # Cursor
                cx2 = fx + 3 + len(val)
                safe_addstr(win, inner_y+1, cx2, "█",
                            curses.color_pair(PAIR_INPUT_FOCUS)|curses.A_BLINK)

    bot_y = y + len(form.fields)*3
    safe_addstr(win, bot_y, fx, "└" + "─"*(fw-2) + "┘", curses.color_pair(PAIR_BORDER))
    bot_y += 2

    # Cost preview
    model_idx  = form.fields[2]["selected"] if "options" in form.fields[2] else 0
    stack_idx  = form.fields[3]["selected"] if "options" in form.fields[3] else 0
    try:    budget = int(form.fields[5]["value"])
    except: budget = 500
    try:    weeks  = int(form.fields[6]["value"])
    except: weeks  = 4

    base_cost = budget + weeks * 200 + model_idx * 50
    token_est = weeks * 800 + model_idx * 300

    safe_addstr(win, bot_y, fx+2, "Project Estimates:", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    safe_addstr(win, bot_y, fx+22,
                f"  Cost ≈ ${base_cost:,}   Tokens ≈ {token_est:,}K   "
                f"Launch risk: {'HIGH' if weeks < 3 else 'MED' if weeks < 8 else 'LOW'}",
                curses.color_pair(PAIR_WARN))
    bot_y += 2

    # Buttons
    btns = ["[ ▶ Start Project ]", "[ Reset ]", "[ Cancel ]"]
    bx = fx + 4
    for bi, btn in enumerate(btns):
        bp = PAIR_BUTTON_FOCUS if bi==0 else PAIR_BUTTON
        safe_addstr(win, bot_y, bx, btn, curses.color_pair(bp)|curses.A_BOLD)
        bx += len(btn) + 3
    bot_y += 2

    if form.message:
        safe_addstr(win, bot_y, fx+2, form.message, curses.color_pair(PAIR_ACCENT)|curses.A_BOLD)

    # Navigation hint
    safe_addstr(win, h-2, 2,
                "Up/Down: move field   ◄/►: cycle options   Type: enter text   Enter: start project",
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── EMPLOYEES TAB ────────────────────────

def draw_employees(win, gs: GameState, emp_sel: int):
    h, w = win.getmaxyx()
    y = 3

    header = f"  {'NAME':<16} {'ROLE':<18} {'LVL':>3} {'SALARY':>8} {'MOOD':>5} {'SKILL':>6}  "
    hline(win, y, 1, w-2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    for i, emp in enumerate(gs.employees):
        is_sel = (i == emp_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        row = (f"  {emp.name:<16} {emp.role:<18} "
               f"{'★'*emp.level:<3} ${emp.salary:>7,} "
               f" {'😊' if emp.mood>75 else '😐' if emp.mood>45 else '😞'}"
               f" {emp.mood:>2}%  {emp.skill:>3}%  ")
        safe_addstr(win, y, 1, " "*(w-2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))

        # Mini mood bar
        bx = w - 22
        progress_bar(win, y, bx, 10, emp.mood,
                     PAIR_ACCENT if emp.mood>60 else PAIR_WARN if emp.mood>30 else PAIR_DANGER,
                     PAIR_MUTED)
        safe_addstr(win, y, bx+11, f" {emp.hired_year}", curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1
    hline(win, y, 1, w-2, PAIR_BORDER)
    y += 1

    # Employee actions
    safe_addstr(win, y, 2, " ACTIONS ", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    for lbl in ["[ ＋ Hire Employee ]", "[ ▲ Train Selected ]",
                "[ 💬 Boost Morale ]", "[ ✕ Lay Off ]"]:
        safe_addstr(win, y, 2, lbl, curses.color_pair(PAIR_BUTTON)|curses.A_BOLD)
        y += 2

    # Monthly salary summary
    total_sal = sum(e.salary for e in gs.employees)
    sx = w // 2 + 2
    safe_addstr(win, 3+2, sx, "PAYROLL SUMMARY", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    for i, emp in enumerate(gs.employees):
        safe_addstr(win, 3+3+i, sx, f"  {emp.name:<16} ${emp.salary:,}/mo",
                    curses.color_pair(PAIR_MUTED))
    safe_addstr(win, 3+3+len(gs.employees)+1, sx,
                f"  {'TOTAL':<16} ${total_sal:,}/mo",
                curses.color_pair(PAIR_WARN)|curses.A_BOLD)

# ─────────────────────── FINANCE TAB ──────────────────────────

def draw_finance(win, gs: GameState):
    h, w = win.getmaxyx()
    y = 3
    mid = w // 2

    # Income breakdown (left)
    income_rows = [
        ("FormFlux MRR",       1_850),
        ("CronBot Pro MRR",    440),
        ("Template Sales",     290),
        ("Consulting Retainer",620),
    ]
    expense_rows = [
        ("Employee Salaries",  sum(e.salary for e in gs.employees)),
        ("Compute / API Fees", 340),
        ("Office Rent",        480),
        ("Loan Repayments",    sum(l["monthly"] for l in gs.loans)),
        ("Tooling & SaaS",     185),
    ]

    lw = mid - 2
    safe_addstr(win, y, 2, "┌"+"─"*(lw-2)+"┐", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, y, 2+(lw-10)//2, " INCOME ", curses.color_pair(PAIR_ACCENT)|curses.A_BOLD)
    for i,(label,amt) in enumerate(income_rows):
        ry=y+1+i
        safe_addstr(win,ry,2,"│",curses.color_pair(PAIR_BORDER))
        safe_addstr(win,ry,4,f"  {label:<28}",curses.color_pair(PAIR_MUTED))
        safe_addstr(win,ry,36,f"${amt:>7,}",curses.color_pair(PAIR_ACCENT)|curses.A_BOLD)
        safe_addstr(win,ry,2+lw-1,"│",curses.color_pair(PAIR_BORDER))
    tot_y=y+1+len(income_rows)
    safe_addstr(win,tot_y,2,"├"+"─"*(lw-2)+"┤",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,tot_y+1,4,"  TOTAL",curses.color_pair(PAIR_MUTED))
    safe_addstr(win,tot_y+1,36,f"${gs.monthly_revenue:>7,}",
                curses.color_pair(PAIR_ACCENT)|curses.A_BOLD)
    safe_addstr(win,tot_y+1,2,"│",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,tot_y+1,2+lw-1,"│",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,tot_y+2,2,"└"+"─"*(lw-2)+"┘",curses.color_pair(PAIR_BORDER))

    ey = tot_y + 4
    safe_addstr(win, ey, 2, "┌"+"─"*(lw-2)+"┐", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, ey, 2+(lw-12)//2, " EXPENSES ", curses.color_pair(PAIR_DANGER)|curses.A_BOLD)
    for i,(label,amt) in enumerate(expense_rows):
        ry=ey+1+i
        safe_addstr(win,ry,2,"│",curses.color_pair(PAIR_BORDER))
        safe_addstr(win,ry,4,f"  {label:<28}",curses.color_pair(PAIR_MUTED))
        safe_addstr(win,ry,36,f"${amt:>7,}",curses.color_pair(PAIR_DANGER)|curses.A_BOLD)
        safe_addstr(win,ry,2+lw-1,"│",curses.color_pair(PAIR_BORDER))
    et=ey+1+len(expense_rows)
    safe_addstr(win,et,2,"├"+"─"*(lw-2)+"┤",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,et+1,4,"  TOTAL",curses.color_pair(PAIR_MUTED))
    safe_addstr(win,et+1,36,f"${gs.monthly_expenses:>7,}",
                curses.color_pair(PAIR_DANGER)|curses.A_BOLD)
    safe_addstr(win,et+1,2,"│",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,et+1,2+lw-1,"│",curses.color_pair(PAIR_BORDER))
    safe_addstr(win,et+2,2,"└"+"─"*(lw-2)+"┘",curses.color_pair(PAIR_BORDER))

    profit = gs.monthly_revenue - gs.monthly_expenses
    pp = PAIR_ACCENT if profit >= 0 else PAIR_DANGER
    safe_addstr(win, et+4, 2,
                f"  Net Monthly: ${profit:+,}",
                curses.color_pair(pp)|curses.A_BOLD)

    # Right: Runway + Bank actions
    rx = mid + 1
    rw = w - mid - 3
    runway_months = gs.cash // max(1, abs(profit)) if profit < 0 else 999
    runway_txt = f"{runway_months} mo" if runway_months < 999 else "∞"

    ry = 3
    safe_addstr(win, ry, rx+2, "FINANCIAL HEALTH", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    ry += 2
    for label, val, pair in [
        ("Cash on Hand",  f"${gs.cash:,}",      PAIR_ACCENT),
        ("Runway",        runway_txt,             PAIR_BADGE_GREEN if runway_months>6 else PAIR_DANGER),
        ("Total Debt",    f"${sum(l['remaining'] for l in gs.loans):,}", PAIR_WARN),
        ("Credit Score",  "712  (Good)",          PAIR_BADGE_BLUE),
    ]:
        safe_addstr(win, ry, rx+2, f"  {label:<16}", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ry, rx+20, val, curses.color_pair(pair)|curses.A_BOLD)
        ry += 2

    ry += 1
    safe_addstr(win, ry, rx+2, "BANKING ACTIONS", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    ry += 2
    for action in ["[ Request Loan ]", "[ Repay Early ]", "[ Transfer Cash ]", "[ View History ]"]:
        safe_addstr(win, ry, rx+4, action, curses.color_pair(PAIR_BUTTON)|curses.A_BOLD)
        ry += 2

    # Lenders list
    ry += 1
    safe_addstr(win, ry, rx+2, "LENDERS", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    ry += 1
    lenders = [
        ("StartupBank",    "9%",   "$5K max",  "Fast approval"),
        ("MicroVenture",   "14.5%","$3K max",  "No credit check"),
        ("AngelBridge",    "6%",   "$20K max", "Requires 60+ rep"),
        ("CedarCredit",    "11%",  "$10K max", "Lebanon-based"),
    ]
    for l in lenders:
        safe_addstr(win, ry, rx+4,
                    f"{l[0]:<14} {l[1]:<6} {l[2]:<10} {l[3]}",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

# ─────────────────────── MARKET TAB ───────────────────────────

def draw_market(win, gs: GameState):
    h, w = win.getmaxyx()
    y = 3

    safe_addstr(win, y, 2, " MARKET & TRENDS ", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    safe_addstr(win, y+1, 2, f"  March 2024 — AI bubble confidence index: 78/100",
                curses.color_pair(PAIR_MUTED))
    y += 3

    # Trending niches
    mid = w // 2
    lw = mid - 2

    trends = [
        ("AI Wrapper Tools",    "+42%", "🔥🔥🔥", "Extremely hot"),
        ("B2B Automation",      "+28%", "🔥🔥",   "Growing"),
        ("EdTech",              "+11%", "🔥",     "Stable uptick"),
        ("Fintech Consumer",    "+7%",  "📈",     "Steady"),
        ("Social Networking",   "-3%",  "📉",     "Declining"),
        ("No-Code Platforms",   "-12%", "🧊",     "Cooling off"),
    ]

    safe_addstr(win, y, 2, "NICHE TREND REPORT", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 2, "─"*(lw-2), curses.color_pair(PAIR_BORDER))
    y += 1
    for niche, pct, heat, label in trends:
        pp = PAIR_ACCENT if pct.startswith("+") else PAIR_DANGER
        safe_addstr(win, y, 4, f"  {heat}  {niche:<22} {pct:<6}  {label}",
                    curses.color_pair(pp))
        y += 1

    y += 1
    # Model costs
    safe_addstr(win, y, 2, "AI MODEL COSTS (per 1M tokens)", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 2, "─"*(lw-2), curses.color_pair(PAIR_BORDER))
    y += 1
    model_costs = [
        ("GPT-4o",          "$5.00",  "$15.00", "Best quality, pricey"),
        ("Claude 3.5 Sonnet","$3.00", "$15.00", "Balanced — your current sub"),
        ("Gemini 1.5 Pro",  "$3.50",  "$10.50", "Strong long context"),
        ("Llama 3.1 70B",   "$0.60",  "$0.60",  "Cheap, self-hostable"),
        ("Mistral Large",   "$2.00",  "$6.00",  "EU-based, GDPR friendly"),
    ]
    safe_addstr(win, y, 4, f"  {'MODEL':<22} {'IN':>7} {'OUT':>7}  NOTE",
                curses.color_pair(PAIR_MUTED)|curses.A_BOLD)
    y += 1
    for m, inp, out, note in model_costs:
        is_current = (m == gs.active_ai_sub)
        cp = PAIR_BADGE_GREEN if is_current else PAIR_MUTED
        cur = "← ACTIVE" if is_current else ""
        safe_addstr(win, y, 4, f"  {m:<22} {inp:>7} {out:>7}  {note}  {cur}",
                    curses.color_pair(cp))
        y += 1

    # Right column: Rival activity
    ry = 3
    rx = mid + 2
    rw = w - mid - 3
    safe_addstr(win, ry, rx, "RIVAL ACTIVITY", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    ry += 1
    safe_addstr(win, ry, rx, "─"*rw, curses.color_pair(PAIR_BORDER))
    ry += 1
    rivals = [
        ("PixelShift LLC",  "AI Wrapper",  "$12K MRR", "↑ Fast"),
        ("NovaTech",        "EdTech SaaS", "$8K MRR",  "→ Stable"),
        ("QuickDeploy Co.", "CLI Tools",   "$3K MRR",  "↓ Slowing"),
    ]
    for rname, rtype, rmrr, rtrend in rivals:
        safe_addstr(win, ry, rx+2, f"{rname:<18} {rtype:<15} {rmrr:<10} {rtrend}",
                    curses.color_pair(PAIR_MUTED))
        ry += 2

    ry += 1
    safe_addstr(win, ry, rx, "INFRASTRUCTURE", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    ry += 1
    safe_addstr(win, ry, rx, "─"*rw, curses.color_pair(PAIR_BORDER))
    ry += 1
    infra = [
        ("Vercel (Hobby)",      "Free",     "Active"),
        ("Supabase (Pro)",      "$25/mo",   "Active"),
        ("Cloudflare Workers",  "$5/mo",    "Active"),
        ("AWS Fargate",         "Unsubbed", "—"),
    ]
    for name, cost, status in infra:
        sp = PAIR_ACCENT if status == "Active" else PAIR_MUTED
        safe_addstr(win, ry, rx+2, f"{name:<22} {cost:<12} ",
                    curses.color_pair(PAIR_MUTED))
        safe_addstr(win, ry, rx+38, status, curses.color_pair(sp))
        ry += 1

# ─────────────────────── EVENTS TAB ───────────────────────────

def draw_events(win, gs: GameState):
    h, w = win.getmaxyx()
    y = 3

    safe_addstr(win, y, 2, " RANDOM EVENTS & WORLD TIMELINE ", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 2

    # Upcoming random events
    upcoming = [
        ("❓", "UPCOMING",  "Product Hunt submission window opens next week.",       "Apr 2024"),
        ("❓", "UPCOMING",  "GPT-5 rumoured launch may disrupt the AI market.",       "May 2024"),
        ("❓", "UPCOMING",  "Potential co-working space rental discount (-20%).",    "Apr 2024"),
    ]
    safe_addstr(win, y, 2, "UPCOMING EVENTS", curses.color_pair(PAIR_WARN)|curses.A_BOLD)
    y += 1
    hline(win, y, 2, w-4, PAIR_BORDER)
    y += 1
    for icon, kind, msg, date in upcoming:
        safe_addstr(win, y, 4, f"  {icon}  [{date}]  {msg}",
                    curses.color_pair(PAIR_WARN))
        y += 1

    y += 2
    # Historical events
    safe_addstr(win, y, 2, "HISTORICAL LOG", curses.color_pair(PAIR_TITLE)|curses.A_BOLD)
    y += 1
    hline(win, y, 2, w-4, PAIR_BORDER)
    y += 1
    event_pairs = {"good": PAIR_ACCENT, "warn": PAIR_WARN, "bad": PAIR_DANGER, "neutral": PAIR_MUTED}
    for icon, msg, kind, date in gs.events:
        ep = event_pairs.get(kind, PAIR_MUTED)
        safe_addstr(win, y, 4, f"  {icon}  [{date}]  {msg}", curses.color_pair(ep))
        y += 1
        if y >= h - 3:
            break

    # World timeline hint
    safe_addstr(win, h-3, 2,
                "  The historical timeline (2022-2042+) drives market events, "
                "AI model releases, and economic shocks.",
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── STATUS BAR ───────────────────────────

def draw_statusbar(win, msg: str):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(h-1, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))
    safe_addstr(win, h-1, 2, msg, curses.color_pair(PAIR_TOPBAR))

# ─────────────────────── MAIN LOOP ────────────────────────────

def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(100)    # 100ms input poll

    gs        = make_dummy_state()
    form      = NewProjectForm()
    active_tab     = 0
    proj_sel       = 0
    emp_sel        = 0
    status_msg     = "Welcome to Vibe Coder Tycoon!  Press Tab to switch tabs."
    tick_counter   = 0
    input_mode     = False   # True when typing in a text field

    # Ticker messages cycling at bottom
    tickers = [
        "📡 AI Index up 3.4% — investors bullish on LLM tooling",
        "💬 Community post: 'I shipped a SaaS in 6 hours with GPT-4o'",
        "⚠️  Vercel announces new compute pricing — costs may rise",
        "📣 Product Hunt top #3 today: 'ResumeAI' by a solo dev",
        "🌍 Lebanon co-working scene growing — CedarTech nodes expand",
        "🤖 Llama 3.1 released: open-source devs rejoice",
        "🏦 AngelBridge seed round: $500K in 48 hours via cold emails",
    ]
    ticker_idx = 0
    ticker_tick = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Background fill
        stdscr.attron(curses.color_pair(PAIR_PANEL))
        for row in range(h):
            stdscr.hline(row, 0, " ", w)
        stdscr.attroff(curses.color_pair(PAIR_PANEL))

        # Draw chrome
        draw_topbar(stdscr, gs)
        draw_tabs(stdscr, active_tab)

        # Draw active tab content
        tab_name = TABS[active_tab]
        if tab_name == "Dashboard":
            draw_dashboard(stdscr, gs)
        elif tab_name == "Projects":
            draw_projects(stdscr, gs, proj_sel)
        elif tab_name == "New Project":
            draw_new_project(stdscr, gs, form)
        elif tab_name == "Employees":
            draw_employees(stdscr, gs, emp_sel)
        elif tab_name == "Finance":
            draw_finance(stdscr, gs)
        elif tab_name == "Market":
            draw_market(stdscr, gs)
        elif tab_name == "Events":
            draw_events(stdscr, gs)

        # Ticker at bottom-1
        ticker_tick += 1
        if ticker_tick >= 50:
            ticker_tick = 0
            ticker_idx = (ticker_idx + 1) % len(tickers)
        ticker_msg = tickers[ticker_idx]
        safe_addstr(stdscr, h-2, 2, f" ▶ {ticker_msg} ",
                    curses.color_pair(PAIR_TICKER))

        draw_statusbar(stdscr, status_msg)
        stdscr.refresh()

        # Input
        key = stdscr.getch()
        tab_name = TABS[active_tab]

        if key == ord('q') or key == ord('Q'):
            break

        elif key == ord('\t'):   # Tab: next tab
            active_tab = (active_tab + 1) % len(TABS)
            status_msg = f"Switched to: {TABS[active_tab]}"

        elif key == curses.KEY_BTAB:   # Shift-Tab: prev tab
            active_tab = (active_tab - 1) % len(TABS)
            status_msg = f"Switched to: {TABS[active_tab]}"

        elif key == ord('n') or key == ord('N'):
            # Advance month (Dashboard only)
            if tab_name == "Dashboard":
                gs.month += 1
                if gs.month > 12:
                    gs.month = 1
                    gs.year += 1
                # Simulate a tick
                gs.cash += gs.monthly_revenue - gs.monthly_expenses
                gs.cash = max(0, gs.cash)
                gs.mental_health = max(0, min(100, gs.mental_health + random.randint(-5, 8)))
                gs.reputation    = max(0, min(100, gs.reputation + random.randint(-2, 4)))
                status_msg = (f"Month advanced to "
                              f"{'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[gs.month-1]}"
                              f" {gs.year}. Cash: ${gs.cash:,}")

        elif tab_name == "Projects":
            if key == curses.KEY_UP:
                proj_sel = max(0, proj_sel - 1)
            elif key == curses.KEY_DOWN:
                proj_sel = min(len(gs.projects)-1, proj_sel + 1)
                status_msg = f"Selected: {gs.projects[proj_sel].name}"

        elif tab_name == "Employees":
            if key == curses.KEY_UP:
                emp_sel = max(0, emp_sel - 1)
            elif key == curses.KEY_DOWN:
                emp_sel = min(len(gs.employees)-1, emp_sel + 1)
                status_msg = f"Selected: {gs.employees[emp_sel].name}"

        elif tab_name == "New Project":
            f_idx = form.focused
            cur_field = form.fields[f_idx]

            if key == curses.KEY_UP:
                form.focused = max(0, form.focused - 1)
            elif key == curses.KEY_DOWN:
                form.focused = min(len(form.fields)-1, form.focused + 1)

            elif "options" in cur_field:
                if key == curses.KEY_LEFT:
                    cur_field["selected"] = (cur_field["selected"]-1) % len(cur_field["options"])
                elif key == curses.KEY_RIGHT:
                    cur_field["selected"] = (cur_field["selected"]+1) % len(cur_field["options"])

            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if "max" in cur_field and cur_field["max"] > 0:
                    cur_field["value"] = cur_field["value"][:-1]

            elif key == 10 or key == curses.KEY_ENTER:
                # Submit
                name = form.fields[0]["value"] or "Unnamed Project"
                ptype = PROJECT_TYPES[form.fields[1]["selected"]]
                model = AI_MODELS[form.fields[2]["selected"]]
                stack = TECH_STACKS[form.fields[3]["selected"]]
                niche = NICHES[form.fields[4]["selected"]]
                new_p = Project(name, ptype, model, stack, niche,
                                "In Dev", 0, 0, 0, 85, 0)
                gs.projects.append(new_p)
                gs.events.insert(0, ("🚀", f"Project '{name}' kicked off!", "good",
                                     f"{'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[gs.month-1]} {gs.year}"))
                form.message = f"  ✅ '{name}' added to your project queue!"
                status_msg = f"New project '{name}' started!"

            elif 32 <= key < 127:
                if "max" in cur_field and cur_field["max"] > 0:
                    if len(cur_field["value"]) < cur_field["max"]:
                        cur_field["value"] += chr(key)

# ───────────────────────── ENTRY POINT ────────────────────────

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n  Thanks for playing Vibe Coder Tycoon (Terminal Demo)\n")
    print("  Next step: Defold mobile build with pixel-art sprites.\n")
