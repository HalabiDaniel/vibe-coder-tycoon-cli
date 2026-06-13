#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              VIBE CODER TYCOON  —  Terminal Game             ║
║       A founder sim for the AI-powered builder era           ║
╚══════════════════════════════════════════════════════════════╝
  Run:  python3 vibe_coder_tycoon.py
  Quit: Q  |  Navigate: Arrow Keys / Tab / Enter
"""

import curses
import random
import time
import json
import os
import hashlib
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────── COLOUR PALETTE ───────────────────────

PAIR_TOPBAR       = 1
PAIR_TAB_ACTIVE   = 2
PAIR_TAB_INACTIVE = 3
PAIR_PANEL        = 4
PAIR_HIGHLIGHT    = 5
PAIR_ACCENT       = 6
PAIR_DANGER       = 7
PAIR_WARN         = 8
PAIR_TITLE        = 9
PAIR_BORDER       = 10
PAIR_MUTED        = 11
PAIR_INPUT_FOCUS  = 12
PAIR_INPUT_IDLE   = 13
PAIR_BUTTON       = 14
PAIR_BUTTON_FOCUS = 15
PAIR_BADGE_BLUE   = 16
PAIR_BADGE_GREEN  = 17
PAIR_BADGE_AMBER  = 18
PAIR_BADGE_RED    = 19
PAIR_TICKER       = 20
PAIR_LOGO         = 21
PAIR_OVERLAY      = 22
PAIR_TITLE_SCREEN = 23
PAIR_MENU_SEL     = 24
PAIR_MENU_IDLE    = 25
PAIR_FOUNDER      = 26

def init_colors():
    curses.start_color()
    curses.use_default_colors()

    def p(pair, fg, bg): curses.init_pair(pair, fg, bg)

    BG       = 17
    BG2      = 18
    BG_TAB   = 234
    FG       = 252
    FG_DIM   = 245
    GREEN    = 82
    RED      = 196
    AMBER    = 214
    CYAN     = 51
    BLUE     = 33
    PURPLE   = 141
    PINK     = 205
    LOGO_FG  = 214
    NAVY     = 17
    NEARBLK  = 232

    p(PAIR_TOPBAR,       FG,      NAVY)
    p(PAIR_TAB_ACTIVE,   NEARBLK, GREEN)
    p(PAIR_TAB_INACTIVE, FG_DIM,  BG_TAB)
    p(PAIR_PANEL,        FG,      NEARBLK)
    p(PAIR_HIGHLIGHT,    NEARBLK, CYAN)
    p(PAIR_ACCENT,       GREEN,   NEARBLK)
    p(PAIR_DANGER,       RED,     NEARBLK)
    p(PAIR_WARN,         AMBER,   NEARBLK)
    p(PAIR_TITLE,        CYAN,    NEARBLK)
    p(PAIR_BORDER,       BLUE,    NEARBLK)
    p(PAIR_MUTED,        FG_DIM,  NEARBLK)
    p(PAIR_INPUT_FOCUS,  NEARBLK, CYAN)
    p(PAIR_INPUT_IDLE,   FG,      235)
    p(PAIR_BUTTON,       NEARBLK, BLUE)
    p(PAIR_BUTTON_FOCUS, NEARBLK, GREEN)
    p(PAIR_BADGE_BLUE,   NEARBLK, BLUE)
    p(PAIR_BADGE_GREEN,  NEARBLK, GREEN)
    p(PAIR_BADGE_AMBER,  NEARBLK, AMBER)
    p(PAIR_BADGE_RED,    NEARBLK, RED)
    p(PAIR_TICKER,       AMBER,   NEARBLK)
    p(PAIR_LOGO,         LOGO_FG, NAVY)
    p(PAIR_OVERLAY,      FG,      NAVY)
    p(PAIR_TITLE_SCREEN, CYAN,    NAVY)
    p(PAIR_MENU_SEL,     NEARBLK, AMBER)
    p(PAIR_MENU_IDLE,    FG_DIM,  NAVY)
    p(PAIR_FOUNDER,      PURPLE,  NEARBLK)
    p(PAIR_MUTED,        FG_DIM,  NEARBLK)

# ─────────────────────── CONSTANTS ────────────────────────────

GAME_VERSION = "v0.9.0-alpha"
DEMO_MONTH_LIMIT = 12

SAVE_FILE = os.path.expanduser("~/.vibe_coder_save.json")

TABS = [
    "Dashboard", "Founder", "Companies", "Projects",
    "Employees", "Market", "Research", "News", "Settings", "Help"
]

# Parody AI subscription names
AI_SUBS = [
    {"name": "ChatNPC Basic",   "cost": 0,   "speed": 2, "quality": 2, "bug_risk": 4,
     "tokens": 1, "chaos": 3, "desc": "Free tier. Slow, unreliable, chaotic."},
    {"name": "Clodex Lite",     "cost": 10,  "speed": 3, "quality": 4, "bug_risk": 3,
     "tokens": 2, "chaos": 2, "desc": "Budget model. Balanced but limited context."},
    {"name": "Gemino Mini",     "cost": 15,  "speed": 4, "quality": 3, "bug_risk": 3,
     "tokens": 2, "chaos": 2, "desc": "Fast and cheap. Weak at complex logic."},
    {"name": "Llamurai 70B",    "cost": 5,   "speed": 3, "quality": 3, "bug_risk": 3,
     "tokens": 1, "chaos": 1, "desc": "Open-source warrior. Self-hostable. GDPR-safe."},
    {"name": "Clodex Pro",      "cost": 40,  "speed": 4, "quality": 5, "bug_risk": 2,
     "tokens": 4, "chaos": 1, "desc": "Premium reasoning. Low bug risk. Expensive."},
    {"name": "ChatNPC Turbo",   "cost": 30,  "speed": 5, "quality": 4, "bug_risk": 2,
     "tokens": 3, "chaos": 2, "desc": "Fast and capable. Token-hungry."},
    {"name": "Mistralix Large", "cost": 25,  "speed": 4, "quality": 4, "bug_risk": 2,
     "tokens": 3, "chaos": 1, "desc": "EU-based. GDPR-friendly. Solid coder."},
    {"name": "DeepVault Coder", "cost": 20,  "speed": 3, "quality": 5, "bug_risk": 1,
     "tokens": 2, "chaos": 1, "desc": "Specialist coding model. Low chaos, high craft."},
]

BACKGROUNDS = [
    {"name": "Solo Hacker",
     "desc": "You work alone, move fast, and break things. Sometimes on purpose.",
     "bonuses": {"prototyping": +15, "burnout_resist": -5, "sales": 0,  "tech_skill": +10}},
    {"name": "Student Builder",
     "desc": "Broke but resourceful. You have time, no money, and strong opinions.",
     "bonuses": {"prototyping": +10, "burnout_resist": +10, "sales": -5, "tech_skill": +5}},
    {"name": "Agency Freelancer",
     "desc": "You know how to sell, scope, and deliver. Slightly burned out already.",
     "bonuses": {"prototyping": 0,  "burnout_resist": -10, "sales": +20, "tech_skill": 0}},
    {"name": "Corporate Escapee",
     "desc": "You left the salary. Now you hustle. You understand processes and politics.",
     "bonuses": {"prototyping": -5, "burnout_resist": +5,  "sales": +10, "tech_skill": +5}},
    {"name": "Indie Game Dev",
     "desc": "You shipped a game once. It made $47. You will not stop trying.",
     "bonuses": {"prototyping": +10, "burnout_resist": +5, "sales": +5, "tech_skill": +5}},
    {"name": "Open-Source Tinkerer",
     "desc": "You contribute to everything and own nothing. Community loves you.",
     "bonuses": {"prototyping": +5, "burnout_resist": +10, "sales": -10, "tech_skill": +20}},
]

PROJECT_TYPES = [
    "SaaS Web App", "Mobile App", "Browser Extension", "CLI Tool",
    "API / Backend", "AI Wrapper", "Discord Bot", "No-Code Template",
    "Developer Tool", "Content Platform",
]

TECH_STACKS = [
    "Next.js + Vercel", "React Native + Expo", "Python + FastAPI",
    "Node.js + Express", "Svelte + Cloudflare", "Electron Desktop",
    "Bubble.io", "Replit + Nix", "T3 Stack", "Django + Railway",
]

NICHES = [
    "Productivity", "Fintech", "Healthcare", "EdTech", "E-Commerce",
    "Social / Community", "Gaming Tools", "Developer Tools",
    "Content Creation", "B2B Automation",
]

COMPANY_LEGAL_STYLES = [
    "Solo Hustle", "Tiny Studio", "Indie Lab",
    "Garage Startup", "Growth Startup", "Holding Company", "Mega Corp",
]

COMPANY_FOCUS_AREAS = [
    "AI Tools", "SaaS", "Mobile Apps", "Games", "Developer Tools",
    "Automation", "Education", "Content Tools", "Weird Internet Products",
]

FUNDING_STYLES = [
    "Bootstrapped", "Friends & Family", "Angel Round",
    "Seed Round", "Revenue-Based", "VC-Backed",
]

RISK_APPETITES = ["Cautious", "Balanced", "Aggressive", "Reckless"]

EMPLOYEE_ROLES = [
    "Vibe Coder", "Prompt Engineer", "Frontend Dev", "Backend Dev",
    "Pixel Artist", "Growth Goblin", "Bug Hunter", "Community Wizard",
    "Finance Gremlin", "Operations Goblin",
]

EMPLOYEE_TRAITS = [
    "Night Owl", "Burnout Resistant", "Token Efficient", "Bug Magnet",
    "Viral Touch", "Revenue Focused", "Community Legend", "Deep Focus",
    "Chaos Agent", "Silent Genius",
]

RESEARCH_CATEGORIES = [
    ("Infrastructure",  ["Faster Deployment", "Auto-Scaling", "CDN Mastery", "Zero-Downtime Deploys"]),
    ("AI / Prompting",  ["Better System Prompts", "Token Compression", "Multi-Agent Chains", "Fine-Tuning Basics"]),
    ("Marketing",       ["Viral Launch Tactics", "SEO Foundations", "Cold Email Engine", "Community Flywheel"]),
    ("Hiring",          ["Better Job Posts", "Culture Fit Screening", "Async Team Setup", "Contractor Network"]),
    ("Automation",      ["Auto Customer Support", "Revenue Reconciliation", "CI/CD Pipeline", "A/B Testing Rig"]),
    ("Funding",         ["Pitch Deck Template", "Angel Network Access", "Revenue Forecasting", "Cap Table Basics"]),
    ("Management",      ["Async Stand-Ups", "OKR Framework", "1-on-1 Cadence", "Team Rituals"]),
    ("Founder Health",  ["Burnout Shield", "Deep Work Blocks", "Boundary Setting", "Sleep Optimization"]),
]

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ─────────────────────── DATA MODELS ──────────────────────────

@dataclass
class Project:
    name: str
    ptype: str
    model: str
    stack: str
    niche: str
    company_id: int
    status: str
    progress: int
    revenue: int
    users: int
    morale: int
    tokens_used: int
    bug_count: int = 0
    hype: int = 50
    tech_debt: int = 0
    launch_date: str = ""
    lifetime_revenue: int = 0

@dataclass
class Employee:
    name: str
    role: str
    level: int
    salary: int
    mood: int
    skill: int
    hired_year: int
    company_id: int
    trait: str = ""
    loyalty: int = 75
    productivity: int = 75

@dataclass
class Company:
    id: int
    name: str
    legal_style: str
    focus_area: str
    funding_style: str
    risk_appetite: str
    cash: int
    monthly_revenue: int
    monthly_expenses: int
    debt: int
    reputation: int
    valuation: int
    office_level: int
    mood: int
    founded_month: int
    founded_year: int
    active: bool = True
    loans: list = field(default_factory=list)

@dataclass
class Founder:
    username: str
    background_idx: int
    reputation: int
    burnout: int
    skill_prototyping: int
    skill_sales: int
    skill_tech: int
    skill_management: int
    total_tokens_used: int
    achievements: list = field(default_factory=list)
    career_history: list = field(default_factory=list)
    unlocked_research: list = field(default_factory=list)

@dataclass
class GameState:
    founder: Optional[Founder]
    year: int
    month: int
    months_elapsed: int
    active_ai_sub_idx: int
    companies: list
    projects: list
    employees: list
    news_feed: list
    events: list
    research_progress: dict
    settings: dict
    demo_ended: bool = False

    def total_cash(self):
        return sum(c.cash for c in self.companies if c.active)

    def active_companies(self):
        return [c for c in self.companies if c.active]

    def company_by_id(self, cid):
        for c in self.companies:
            if c.id == cid:
                return c
        return None

    def projects_for_company(self, cid):
        return [p for p in self.projects if p.company_id == cid]

    def employees_for_company(self, cid):
        return [e for e in self.employees if e.company_id == cid]

# ─────────────────────── SAVE / LOAD ──────────────────────────

ACCOUNTS_FILE = os.path.expanduser("~/.vibe_coder_accounts.json")

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_accounts(accounts):
    try:
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)
    except Exception:
        pass

def accounts_sign_in(username_or_email, password):
    accounts = load_accounts()
    ph = hash_password(password)
    for uname, data in accounts.items():
        if (uname == username_or_email or data.get("email") == username_or_email):
            if data.get("password_hash") == ph:
                return uname, data
    return None, None

def accounts_create(username, email, password):
    accounts = load_accounts()
    if username in accounts:
        return False, "Username already exists."
    for data in accounts.values():
        if data.get("email") == email:
            return False, "Email already registered."
    accounts[username] = {
        "email": email,
        "password_hash": hash_password(password),
        "last_played": f"{MONTH_NAMES[0]} 2025",
        "founder_status": "Rookie Founder",
    }
    save_accounts(accounts)
    return True, "Account created."

def save_game(gs: GameState, username: str):
    try:
        data = {
            "username": username,
            "year": gs.year,
            "month": gs.month,
            "months_elapsed": gs.months_elapsed,
            "active_ai_sub_idx": gs.active_ai_sub_idx,
            "founder": gs.founder.__dict__ if gs.founder else None,
            "companies": [c.__dict__ for c in gs.companies],
            "projects": [p.__dict__ for p in gs.projects],
            "employees": [e.__dict__ for e in gs.employees],
            "news_feed": gs.news_feed,
            "events": gs.events,
            "research_progress": gs.research_progress,
            "settings": gs.settings,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_game(username: str) -> Optional[GameState]:
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
        if data.get("username") != username:
            return None
        fd = data.get("founder")
        founder = Founder(**fd) if fd else None
        companies = [Company(**c) for c in data.get("companies", [])]
        projects  = [Project(**p) for p in data.get("projects", [])]
        employees = [Employee(**e) for e in data.get("employees", [])]
        return GameState(
            founder=founder,
            year=data["year"],
            month=data["month"],
            months_elapsed=data.get("months_elapsed", 0),
            active_ai_sub_idx=data.get("active_ai_sub_idx", 0),
            companies=companies,
            projects=projects,
            employees=employees,
            news_feed=data.get("news_feed", []),
            events=data.get("events", []),
            research_progress=data.get("research_progress", {}),
            settings=data.get("settings", default_settings()),
        )
    except Exception:
        return None

def default_settings():
    return {
        "theme": "Dark Terminal",
        "reduced_animations": False,
        "high_contrast": False,
        "ticker_speed": "normal",
        "audio": "off",
    }

def make_new_game(founder: Founder, ai_sub_idx: int) -> GameState:
    bg = BACKGROUNDS[founder.background_idx]
    starting_cash = 5000
    c = Company(
        id=0,
        name=f"{founder.username}'s First Venture",
        legal_style="Solo Hustle",
        focus_area="AI Tools",
        funding_style="Bootstrapped",
        risk_appetite="Balanced",
        cash=starting_cash,
        monthly_revenue=0,
        monthly_expenses=200,
        debt=0,
        reputation=20,
        valuation=starting_cash,
        office_level=1,
        mood=80,
        founded_month=1,
        founded_year=2025,
        loans=[],
    )
    gs = GameState(
        founder=founder,
        year=2025,
        month=1,
        months_elapsed=0,
        active_ai_sub_idx=ai_sub_idx,
        companies=[c],
        projects=[],
        employees=[],
        news_feed=make_initial_news(),
        events=[("🚀", f"Welcome, {founder.username}! Your journey begins.", "good", "Jan 2025")],
        research_progress={},
        settings=default_settings(),
    )
    return gs

def make_initial_news():
    return [
        {"icon": "📡", "headline": "AI funding hits record high — $40B deployed in Q4 2024",
         "category": "Market", "date": "Jan 2025", "effect": None},
        {"icon": "🔥", "headline": "ChatNPC announces major pricing restructure — check your subs",
         "category": "Tools", "date": "Jan 2025", "effect": None},
        {"icon": "📣", "headline": "IndieScroll trending: solo devs shipping faster than ever",
         "category": "Community", "date": "Jan 2025", "effect": None},
        {"icon": "⚠️",  "headline": "SnapStack suffers 6-hour outage — Vercel alternatives spike",
         "category": "Drama", "date": "Jan 2025", "effect": None},
        {"icon": "💡", "headline": "New open-source LLM from DeepVault matches frontier quality",
         "category": "Research", "date": "Dec 2024", "effect": None},
    ]

# ─────────────────────── DRAWING HELPERS ──────────────────────

def safe_addstr(win, y, x, text, attr=0):
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

def progress_bar(win, y, x, width, pct, pair_fill, pair_empty):
    filled = max(0, min(width, int(width * pct / 100)))
    safe_addstr(win, y, x, "█" * filled,            curses.color_pair(pair_fill))
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
        "Archived": PAIR_MUTED,
        "Sold":     PAIR_BADGE_AMBER,
    }.get(status, PAIR_BADGE_BLUE)

def fill_background(win, pair):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(pair))
    for row in range(h):
        win.hline(row, 0, " ", w)
    win.attroff(curses.color_pair(pair))

def draw_box(win, y, x, h, w, pair_border, title="", pair_title=None):
    if pair_title is None:
        pair_title = PAIR_TITLE
    safe_addstr(win, y, x, "┌" + "─"*(w-2) + "┐", curses.color_pair(pair_border))
    for r in range(1, h-1):
        safe_addstr(win, y+r, x,     "│", curses.color_pair(pair_border))
        safe_addstr(win, y+r, x+w-1, "│", curses.color_pair(pair_border))
    safe_addstr(win, y+h-1, x, "└" + "─"*(w-2) + "┘", curses.color_pair(pair_border))
    if title:
        t = f" {title} "
        tx = x + max(1, (w - len(t)) // 2)
        safe_addstr(win, y, tx, t, curses.color_pair(pair_title) | curses.A_BOLD)

def center_text(win, y, text, attr):
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(win, y, x, text, attr)

def draw_topbar(win, gs: GameState):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(0, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))

    logo = " ⚡ VIBE CODER TYCOON "
    safe_addstr(win, 0, 1, logo, curses.color_pair(PAIR_LOGO) | curses.A_BOLD)

    total_cash = gs.total_cash()
    sub = AI_SUBS[gs.active_ai_sub_idx]["name"]
    date_str = f"{MONTH_NAMES[gs.month-1]} {gs.year}"

    stats = [
        (f"   📅 {date_str}",              curses.color_pair(PAIR_TOPBAR)),
        (f"   💰 ${total_cash:,}",          curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD),
        (f"   🤖 {sub}",                    curses.color_pair(PAIR_TOPBAR)),
        (f"   🔥 Burnout:{gs.founder.burnout}%", curses.color_pair(PAIR_TOPBAR)),
        (f"   ⭐ Rep:{gs.founder.reputation}", curses.color_pair(PAIR_TOPBAR)),
        (f"   🏢 {len(gs.active_companies())} cos", curses.color_pair(PAIR_TOPBAR)),
    ]
    cx = len(logo) + 2
    for text, attr in stats:
        safe_addstr(win, 0, cx, text, attr)
        cx += len(text)

    pname = f" 👤 {gs.founder.username}  "
    safe_addstr(win, 0, w - len(pname) - 1, pname,
                curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD)

def draw_tabs(win, active_tab: int):
    h, w = win.getmaxyx()
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

    hints = " Tab:Switch  Q:Quit  N:Next Month  Enter:Select "
    safe_addstr(win, 1, w - len(hints) - 1, hints, curses.color_pair(PAIR_MUTED))

def draw_statusbar(win, msg: str):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(h-1, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))
    safe_addstr(win, h-1, 2, msg, curses.color_pair(PAIR_TOPBAR))

# ─────────────────────── TITLE SCREEN ─────────────────────────

LOGO_ART = [
    r"  ██╗   ██╗██╗██████╗ ███████╗     ██████╗ ██████╗ ██████╗ ███████╗██████╗  ",
    r"  ██║   ██║██║██╔══██╗██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗ ",
    r"  ██║   ██║██║██████╔╝█████╗      ██║     ██║   ██║██║  ██║█████╗  ██████╔╝ ",
    r"  ╚██╗ ██╔╝██║██╔══██╗██╔══╝      ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗ ",
    r"   ╚████╔╝ ██║██████╔╝███████╗    ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║ ",
    r"    ╚═══╝  ╚═╝╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ",
    r"",
    r"  ████████╗██╗   ██╗ ██████╗ ██████╗  ██████╗ ███╗   ██╗",
    r"  ╚══██╔══╝╚██╗ ██╔╝██╔════╝██╔═══██╗██╔═══██╗████╗  ██║",
    r"     ██║    ╚████╔╝ ██║     ██║   ██║██║   ██║██╔██╗ ██║",
    r"     ██║     ╚██╔╝  ██║     ██║   ██║██║   ██║██║╚██╗██║",
    r"     ██║      ██║   ╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║",
    r"     ╚═╝      ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝",
]

LOGO_SMALL = [
    "  ██╗   ██╗ ██████╗████████╗  |  TYCOON",
    "  ██║   ██║██╔════╝╚══██╔══╝  | Founder Sim",
    "  ╚██╗ ██╔╝██║        ██║     | for the AI era",
    "   ╚████╔╝ ██║        ██║     |",
    "    ╚═══╝  ╚██████╗   ██║     | " + GAME_VERSION,
]

TITLE_MENU = [
    ("S", "Sign In"),
    ("C", "Create Account"),
    ("O", "Play Offline"),
    ("T", "Settings"),
    ("R", "Credits"),
    ("Q", "Exit"),
]

def draw_title_screen(win, sel: int, blink: bool):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)

    # Decorative border
    safe_addstr(win, 0,   0, "╔" + "═"*(w-2) + "╗", curses.color_pair(PAIR_BORDER))
    safe_addstr(win, h-1, 0, "╚" + "═"*(w-2) + "╝", curses.color_pair(PAIR_BORDER))
    for r in range(1, h-1):
        safe_addstr(win, r, 0,   "║", curses.color_pair(PAIR_BORDER))
        safe_addstr(win, r, w-1, "║", curses.color_pair(PAIR_BORDER))

    # Logo (small version if terminal is narrow)
    logo_y = 2
    if w >= 80:
        for i, line in enumerate(LOGO_SMALL):
            center_text(win, logo_y + i, line, curses.color_pair(PAIR_LOGO) | curses.A_BOLD)
        logo_y += len(LOGO_SMALL) + 1
    else:
        title = "VIBE CODER TYCOON"
        center_text(win, logo_y, title, curses.color_pair(PAIR_LOGO) | curses.A_BOLD)
        logo_y += 2

    # Tagline
    tagline = "Ship fast. Break things. Build an empire."
    center_text(win, logo_y, tagline, curses.color_pair(PAIR_TITLE_SCREEN))
    logo_y += 1

    sub_tag = "A terminal-native founder sim for the AI-powered builder era."
    center_text(win, logo_y, sub_tag, curses.color_pair(PAIR_MUTED))
    logo_y += 2

    # Version + decorative line
    ver_line = f"─── {GAME_VERSION} ─── Alpha Release ───"
    center_text(win, logo_y, ver_line, curses.color_pair(PAIR_BORDER))
    logo_y += 2

    # Menu
    menu_w = 30
    menu_x = max(1, (w - menu_w) // 2)
    for i, (key, label) in enumerate(TITLE_MENU):
        is_sel = (i == sel)
        if is_sel:
            bg = curses.color_pair(PAIR_MENU_SEL) | curses.A_BOLD
            text = f"  [ {key} ]  {label}  "
        else:
            bg = curses.color_pair(PAIR_MENU_IDLE)
            text = f"    {key}    {label}  "
        center_text(win, logo_y + i*2, text, bg)
    logo_y += len(TITLE_MENU) * 2 + 1

    # Blink hint
    if blink:
        hint = "Arrow keys to navigate  |  Enter to select"
        center_text(win, logo_y, hint, curses.color_pair(PAIR_MUTED))
    logo_y += 2

    # Ticker band
    tickers_title = ["⚡ AI is the IDE now  ", "📦 Ship before you sleep  ",
                     "💸 MRR or nothing  ", "🌍 Build global, start local  "]
    tick_idx = int(time.time() * 0.5) % len(tickers_title)
    center_text(win, h-3, "  ".join(tickers_title), curses.color_pair(PAIR_TICKER))

# ─────────────────────── SIGN IN FLOW ─────────────────────────

@dataclass
class SignInState:
    fields: list = field(default_factory=lambda: [
        {"label": "Username or Email", "value": "", "secret": False},
        {"label": "Password",          "value": "", "secret": True},
    ])
    focused: int = 0
    message: str = ""
    success_name: str = ""
    success_date: str = ""
    success_status: str = ""
    step: str = "form"  # "form" | "welcome"

def draw_sign_in(win, state: SignInState, blink: bool):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)

    if state.step == "welcome":
        draw_welcome_back(win, state)
        return

    title = "SIGN IN TO YOUR ACCOUNT"
    center_text(win, 2, title, curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 3, "Enter your credentials to continue.", curses.color_pair(PAIR_MUTED))

    bw = min(50, w - 4)
    bx = (w - bw) // 2
    by = 5

    draw_box(win, by, bx, len(state.fields)*3 + 4, bw, PAIR_BORDER, "CREDENTIALS", PAIR_TITLE)

    for i, f in enumerate(state.fields):
        is_focus = (i == state.focused)
        fy = by + 1 + i * 3
        label_attr = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
                      else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_focus else "  "
        safe_addstr(win, fy, bx+2, f"{prefix}{f['label']}", label_attr)
        val = f["value"]
        display = ("*" * len(val)) if f["secret"] else val
        ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
        inp_text = f" {display:<{bw-8}} "
        safe_addstr(win, fy+1, bx+2, inp_text[:bw-4], curses.color_pair(ip))
        if is_focus and blink:
            cx = bx + 3 + len(display)
            safe_addstr(win, fy+1, cx, "█", curses.color_pair(PAIR_INPUT_FOCUS) | curses.A_BLINK)

    # Buttons
    btn_y = by + len(state.fields)*3 + 3
    btns = [("Enter", "[ Sign In ]"), ("Esc", "[ Back ]")]
    bxb = bx + 4
    for key, label in btns:
        safe_addstr(win, btn_y, bxb, label, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
        bxb += len(label) + 4

    if state.message:
        msg_pair = PAIR_DANGER if "Invalid" in state.message or "failed" in state.message.lower() else PAIR_ACCENT
        center_text(win, btn_y + 2, state.message, curses.color_pair(msg_pair) | curses.A_BOLD)

    center_text(win, h-3, "Up/Down: move field  |  Type: enter text  |  Enter: sign in  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

def draw_welcome_back(win, state: SignInState):
    h, w = win.getmaxyx()
    bw = min(52, w - 4)
    bx = (w - bw) // 2
    by = (h - 14) // 2

    draw_box(win, by, bx, 14, bw, PAIR_BORDER, "WELCOME BACK", PAIR_ACCENT)

    center_text(win, by+2, f"👤  {state.success_name}", curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    center_text(win, by+4, f"Last played:  {state.success_date}", curses.color_pair(PAIR_MUTED))
    center_text(win, by+5, f"Founder rank: {state.success_status}", curses.color_pair(PAIR_TITLE))
    center_text(win, by+7, "Your save data has been loaded.", curses.color_pair(PAIR_MUTED))

    center_text(win, by+9, "[ Continue → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
    center_text(win, by+11, "Press Enter to continue", curses.color_pair(PAIR_MUTED))

# ─────────────────────── SIGN UP FLOW ─────────────────────────

@dataclass
class SignUpState:
    step: str = "form"  # "form" | "founder" | "ai_sub"
    fields: list = field(default_factory=lambda: [
        {"label": "Choose a Username",     "value": "", "secret": False, "max": 20},
        {"label": "Email Address",         "value": "", "secret": False, "max": 60},
        {"label": "Password",              "value": "", "secret": True,  "max": 50},
        {"label": "Confirm Password",      "value": "", "secret": True,  "max": 50},
    ])
    focused: int = 0
    message: str = ""
    founder_bg_sel: int = 0
    ai_sub_sel: int = 0

def draw_sign_up(win, state: SignUpState, blink: bool):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)

    if state.step == "founder":
        draw_founder_creation(win, state)
        return
    if state.step == "ai_sub":
        draw_ai_sub_selection(win, state)
        return

    title = "CREATE YOUR ACCOUNT"
    center_text(win, 2, title, curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 3, "Set up your founder profile to start building.", curses.color_pair(PAIR_MUTED))

    bw = min(54, w - 4)
    bx = (w - bw) // 2
    by = 5

    draw_box(win, by, bx, len(state.fields)*3 + 4, bw, PAIR_BORDER, "ACCOUNT DETAILS", PAIR_TITLE)

    for i, f in enumerate(state.fields):
        is_focus = (i == state.focused)
        fy = by + 1 + i * 3
        label_attr = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
                      else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_focus else "  "
        safe_addstr(win, fy, bx+2, f"{prefix}{f['label']}", label_attr)
        val = f["value"]
        display = ("*" * len(val)) if f["secret"] else val
        ip = PAIR_INPUT_FOCUS if is_focus else PAIR_INPUT_IDLE
        safe_addstr(win, fy+1, bx+2, f" {display:<{bw-8}} "[:bw-4], curses.color_pair(ip))
        if is_focus and blink:
            cx = bx + 3 + len(display)
            safe_addstr(win, fy+1, cx, "█", curses.color_pair(PAIR_INPUT_FOCUS) | curses.A_BLINK)

    btn_y = by + len(state.fields)*3 + 3
    safe_addstr(win, btn_y, bx+4, "[ Create Account → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
    safe_addstr(win, btn_y, bx+26, "[ Back ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)

    if state.message:
        mp = PAIR_DANGER if "already" in state.message or "match" in state.message else PAIR_ACCENT
        center_text(win, btn_y + 2, state.message, curses.color_pair(mp) | curses.A_BOLD)

    center_text(win, h-3, "Up/Down: field  |  Type: enter text  |  Enter: next  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

def draw_founder_creation(win, state: SignUpState):
    h, w = win.getmaxyx()
    title = "CHOOSE YOUR BACKGROUND"
    center_text(win, 2, title, curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 3, "Your background shapes your starting skills and bonuses.",
                curses.color_pair(PAIR_MUTED))

    bw = min(68, w - 4)
    bx = (w - bw) // 2
    by = 5

    for i, bg in enumerate(BACKGROUNDS):
        is_sel = (i == state.founder_bg_sel)
        row_y = by + i * 4
        pair = PAIR_MENU_SEL if is_sel else PAIR_PANEL

        prefix = "▶ " if is_sel else "  "
        name_attr = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_sel
                     else curses.color_pair(PAIR_TITLE))
        safe_addstr(win, row_y, bx + 2, f"{prefix}{bg['name']}", name_attr)
        safe_addstr(win, row_y+1, bx + 6, bg["desc"][:bw-8], curses.color_pair(PAIR_MUTED))

        # Bonus display
        bonuses = bg["bonuses"]
        bstr = (f"  Prototype {bonuses['prototyping']:+d}  "
                f"Sales {bonuses['sales']:+d}  "
                f"Tech {bonuses['tech_skill']:+d}  "
                f"Burnout Resist {bonuses['burnout_resist']:+d}")
        safe_addstr(win, row_y+2, bx + 6, bstr[:bw-8],
                    curses.color_pair(PAIR_ACCENT if is_sel else PAIR_MUTED))

        if i < len(BACKGROUNDS) - 1:
            safe_addstr(win, row_y+3, bx, "─" * bw, curses.color_pair(PAIR_BORDER))

    btn_y = by + len(BACKGROUNDS) * 4 + 1
    safe_addstr(win, btn_y, bx + 4, "[ Confirm Background → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    center_text(win, h-3, "Up/Down: choose background  |  Enter: confirm  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

def draw_ai_sub_selection(win, state: SignUpState):
    h, w = win.getmaxyx()
    title = "CHOOSE YOUR AI SUBSCRIPTION"
    center_text(win, 2, title, curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 3, "Your AI tool affects speed, quality, bugs, and token burn.",
                curses.color_pair(PAIR_MUTED))

    bw = min(72, w - 4)
    bx = (w - bw) // 2
    by = 5

    col_header = f"  {'NAME':<18} {'$/mo':>5}  {'SPEED':>5}  {'QUALITY':>7}  {'BUG RISK':>8}  {'CHAOS':>5}"
    safe_addstr(win, by, bx, col_header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, by+1, bx, "─"*bw, curses.color_pair(PAIR_BORDER))

    for i, sub in enumerate(AI_SUBS):
        is_sel = (i == state.ai_sub_sel)
        row_y = by + 2 + i * 3
        name_attr = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_sel
                     else curses.color_pair(PAIR_MUTED))
        prefix = "▶ " if is_sel else "  "

        cost = f"${sub['cost']}" if sub["cost"] > 0 else "Free"
        spd   = "█" * sub["speed"]   + "░" * (5 - sub["speed"])
        qual  = "█" * sub["quality"] + "░" * (5 - sub["quality"])
        bugs  = "█" * sub["bug_risk"] + "░" * (5 - sub["bug_risk"])
        chaos = "█" * sub["chaos"]   + "░" * (5 - sub["chaos"])

        row = f"  {prefix}{sub['name']:<18} {cost:>5}  {spd}  {qual}     {bugs}      {chaos}"
        safe_addstr(win, row_y, bx, row, name_attr)
        safe_addstr(win, row_y+1, bx + 6, sub["desc"][:bw-8], curses.color_pair(PAIR_MUTED))

    btn_y = by + 2 + len(AI_SUBS) * 3 + 1
    safe_addstr(win, btn_y, bx + 4, "[ Start Game → ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    center_text(win, h-3, "Up/Down: choose AI sub  |  Enter: start your journey  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── CREDITS SCREEN ───────────────────────

def draw_credits(win):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)
    center_text(win, 2, "CREDITS", curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    lines = [
        "",
        "Vibe Coder Tycoon — Terminal Edition",
        f"Version {GAME_VERSION}",
        "",
        "Design & Development",
        "A solo founder project. Built with Python + curses.",
        "",
        "Inspiration",
        "Every indie dev who shipped at 3am with no users yet.",
        "",
        "Special Thanks",
        "The open-source community. The AI builders.",
        "Everyone who ever clicked Deploy and held their breath.",
        "",
        "⚡  Ship it. Even if it breaks.",
        "",
    ]
    for i, line in enumerate(lines):
        attr = curses.color_pair(PAIR_ACCENT) if line.startswith("⚡") else curses.color_pair(PAIR_MUTED)
        if line in ("Design & Development", "Inspiration", "Special Thanks"):
            attr = curses.color_pair(PAIR_TITLE) | curses.A_BOLD
        center_text(win, 4 + i, line, attr)
    center_text(win, h-3, "Press Esc or Enter to return", curses.color_pair(PAIR_MUTED))

# ─────────────────────── SETTINGS SCREEN ──────────────────────

SETTINGS_OPTIONS = {
    "theme": ["Dark Terminal", "Matrix Green", "Amber CRT", "Soft Hacker", "Retro DOS", "Clean Monochrome"],
    "ticker_speed": ["slow", "normal", "fast"],
    "audio": ["off", "on"],
}

@dataclass
class SettingsUIState:
    focused: int = 0
    keys: list = field(default_factory=lambda: [
        "theme", "reduced_animations", "high_contrast", "ticker_speed", "audio"
    ])
    labels: list = field(default_factory=lambda: [
        "Visual Theme",
        "Reduced Animations",
        "High Contrast Mode",
        "Ticker Speed",
        "Audio",
    ])

def draw_settings_screen(win, gs: Optional[GameState], state: SettingsUIState,
                         standalone_settings=None):
    h, w = win.getmaxyx()
    settings = gs.settings if gs else (standalone_settings or default_settings())

    fill_background(win, PAIR_PANEL if gs else PAIR_OVERLAY)

    title_y = 3 if not gs else 3
    safe_addstr(win, title_y, 2, " SETTINGS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y = title_y + 2

    for i, (key, label) in enumerate(zip(state.keys, state.labels)):
        is_focus = (i == state.focused)
        prefix = "▶ " if is_focus else "  "
        la = (curses.color_pair(PAIR_ACCENT) | curses.A_BOLD if is_focus
              else curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 4, f"{prefix}{label:<26}", la)

        val = settings.get(key, "")
        if isinstance(val, bool):
            vstr = "ON" if val else "OFF"
            vp = PAIR_BADGE_GREEN if val else PAIR_BADGE_RED
        elif key in SETTINGS_OPTIONS:
            vstr = str(val).upper()
            vp = PAIR_BADGE_BLUE
        else:
            vstr = str(val)
            vp = PAIR_MUTED

        badge(win, y, 34, vstr, vp)

        if is_focus:
            if key in SETTINGS_OPTIONS:
                safe_addstr(win, y, 50, "◄/► to cycle", curses.color_pair(PAIR_MUTED))
            else:
                safe_addstr(win, y, 50, "Enter to toggle", curses.color_pair(PAIR_MUTED))
        y += 2

    y += 1
    safe_addstr(win, y, 4, "[ Save & Return ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    if not gs:
        center_text(win, h-3, "Up/Down: field  |  ◄/►: change  |  Esc: back",
                    curses.color_pair(PAIR_MUTED))

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

# ─────────────────────── FOUNDER TAB ──────────────────────────

def draw_founder(win, gs: GameState):
    h, w = win.getmaxyx()
    f = gs.founder
    bg = BACKGROUNDS[f.background_idx]
    y = 3
    mid = w // 2

    # Left: Identity
    safe_addstr(win, y, 2, " FOUNDER PROFILE ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2
    rows = [
        ("Name",          f.username),
        ("Background",    bg["name"]),
        ("Reputation",    f"{f.reputation}/100"),
        ("Burnout",       f"{f.burnout}%"),
        ("Tokens Used",   f"{f.total_tokens_used:,}K"),
        ("Companies",     str(len(gs.active_companies()))),
        ("Projects",      str(len(gs.projects))),
        ("AI Sub",        AI_SUBS[gs.active_ai_sub_idx]["name"]),
    ]
    lw = mid - 4
    for label, val in rows:
        safe_addstr(win, y, 4, f"{label:<22}", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 26, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        y += 1

    y += 1
    # Skill bars
    safe_addstr(win, y, 4, "SKILLS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    skills = [
        ("Prototyping", f.skill_prototyping),
        ("Sales",       f.skill_sales),
        ("Tech Depth",  f.skill_tech),
        ("Management",  f.skill_management),
    ]
    for name, val in skills:
        safe_addstr(win, y, 4, f"  {name:<14}", curses.color_pair(PAIR_MUTED))
        bw = lw - 22
        progress_bar(win, y, 20, bw, val, PAIR_ACCENT, PAIR_MUTED)
        safe_addstr(win, y, 20 + bw + 1, f"{val:3d}", curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1
    # Burnout bar (danger colour)
    safe_addstr(win, y, 4, "  Burnout        ", curses.color_pair(PAIR_MUTED))
    bw = lw - 22
    burn_pair = PAIR_DANGER if f.burnout > 70 else PAIR_WARN if f.burnout > 40 else PAIR_ACCENT
    progress_bar(win, y, 20, bw, f.burnout, burn_pair, PAIR_MUTED)
    safe_addstr(win, y, 20 + bw + 1, f"{f.burnout:3d}%",
                curses.color_pair(PAIR_DANGER if f.burnout > 70 else PAIR_MUTED))
    y += 2

    # Background bonus reminder
    safe_addstr(win, y, 4, f"Background: {bg['name']}", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 6, bg["desc"][:mid-8], curses.color_pair(PAIR_MUTED))
    y += 1
    bonuses = bg["bonuses"]
    bstr = (f"  Proto {bonuses['prototyping']:+d}  Sales {bonuses['sales']:+d}  "
            f"Tech {bonuses['tech_skill']:+d}  Burnout Resist {bonuses['burnout_resist']:+d}")
    safe_addstr(win, y, 6, bstr[:mid-8], curses.color_pair(PAIR_ACCENT))

    # Right: Achievements + career
    rx = mid + 2
    rw = w - mid - 4
    ry = 3
    safe_addstr(win, ry, rx, " ACHIEVEMENTS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.achievements:
        for ach in f.achievements[:8]:
            safe_addstr(win, ry, rx+2, f"🏆 {ach}", curses.color_pair(PAIR_WARN))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "No achievements yet. Go ship something.",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, " CAREER HISTORY ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.career_history:
        for entry in f.career_history[:8]:
            safe_addstr(win, ry, rx+2, f"  {entry}"[:rw-4], curses.color_pair(PAIR_MUTED))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "Your story is just beginning.",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 2
    safe_addstr(win, ry, rx, " UNLOCKED RESEARCH ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.unlocked_research:
        for res in f.unlocked_research[:6]:
            safe_addstr(win, ry, rx+2, f"✓ {res}", curses.color_pair(PAIR_ACCENT))
            ry += 1
    else:
        safe_addstr(win, ry, rx+2, "Nothing unlocked yet. Visit Research.",
                    curses.color_pair(PAIR_MUTED))

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

# ─────────────────────── PROJECTS TAB ─────────────────────────

@dataclass
class ProjectsUIState:
    view: str = "list"      # "list" | "detail" | "new_step1" | "new_step2" | "new_step3" | "new_review"
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

def draw_projects(win, gs: GameState, ui: ProjectsUIState):
    h, w = win.getmaxyx()

    if ui.view.startswith("new"):
        _draw_new_project_wizard(win, gs, ui)
        return

    y = 3
    filters = ["All", "In Dev", "Launched", "Growing", "Failed", "Archived", "Sold"]
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
               if ui.filter_status == "All" or p.status == ui.filter_status]

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
        actions = ["[ Launch ]", "[ Sunset ]", "[ Boost (200cr) ]", "[ View Analytics ]", "[ Archive ]"]
        ax = 4
        for act in actions:
            safe_addstr(win, min(act_y, h-5), ax, act, curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ax += len(act) + 2

    safe_addstr(win, h-4, 2,
                "Up/Down: select  |  ◄/►: filter  |  N: new project  |  Enter: action",
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

# ─────────────────────── MARKET TAB ───────────────────────────

def draw_market(win, gs: GameState):
    h, w = win.getmaxyx()
    y = 3
    mid = w // 2
    lw = mid - 3

    safe_addstr(win, y, 2, " MARKET & TRENDS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    month = MONTH_NAMES[gs.month-1]
    safe_addstr(win, y+1, 2, f"  {month} {gs.year}  —  AI Builder Confidence Index: 78/100",
                curses.color_pair(PAIR_MUTED))
    y += 3

    # Trending niches
    trends = [
        ("AI Wrapper Tools",   "+42%", "🔥🔥🔥", "Extremely hot"),
        ("B2B Automation",     "+28%", "🔥🔥",   "Growing"),
        ("EdTech",             "+11%", "🔥",     "Stable uptick"),
        ("Fintech Consumer",   "+7%",  "📈",     "Steady"),
        ("Social Networking",  "-3%",  "📉",     "Declining"),
        ("No-Code Platforms",  "-12%", "🧊",     "Cooling off"),
    ]

    safe_addstr(win, y, 2, "NICHE TREND REPORT", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER)
    y += 1
    for niche, pct, heat, label in trends:
        pp = PAIR_ACCENT if pct.startswith("+") else PAIR_DANGER
        safe_addstr(win, y, 4, f"  {heat}  {niche:<22} {pct:<7} {label}", curses.color_pair(pp))
        y += 1

    y += 1
    # AI sub pricing
    safe_addstr(win, y, 2, "AI SUBSCRIPTION MARKET", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER)
    y += 1
    safe_addstr(win, y, 4, f"  {'NAME':<20} {'$/mo':>6}  {'QUALITY':<9}  NOTE",
                curses.color_pair(PAIR_MUTED) | curses.A_BOLD)
    y += 1
    current_sub = AI_SUBS[gs.active_ai_sub_idx]["name"]
    for sub in AI_SUBS:
        is_cur = (sub["name"] == current_sub)
        cp = PAIR_BADGE_GREEN if is_cur else PAIR_MUTED
        cur = "← ACTIVE" if is_cur else ""
        cost = f"${sub['cost']}" if sub["cost"] else "Free"
        qual = "█" * sub["quality"] + "░" * (5 - sub["quality"])
        safe_addstr(win, y, 4, f"  {sub['name']:<20} {cost:>6}  {qual}  {sub['desc'][:24]}  {cur}",
                    curses.color_pair(cp))
        y += 1

    # Right column: Rivals + infrastructure
    rx = mid + 2
    rw = w - mid - 4
    ry = 3 + 3

    safe_addstr(win, ry, rx, "COMPETITOR ACTIVITY", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    rivals = [
        ("SnapStack LLC",    "AI Wrapper",     "$14K MRR", "↑ Fast"),
        ("CloudCastle",      "SaaS Infra",     "$9K MRR",  "→ Stable"),
        ("DeployGoblin Co.", "CLI Tools",      "$3.5K MRR","↓ Slowing"),
        ("BirdBoard Inc.",   "Social Tool",    "$1K MRR",  "↓ Dying"),
        ("HuntProductive",   "Productivity",   "$22K MRR", "↑ Surging"),
    ]
    for rname, rtype, rmrr, rtrend in rivals:
        safe_addstr(win, ry, rx+2, f"{rname:<20} {rtype:<16} {rmrr:<10} {rtrend}",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, "INVESTOR MOOD", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    safe_addstr(win, ry, rx+2, "Angel Market:   Bullish on AI tooling", curses.color_pair(PAIR_ACCENT))
    ry += 1
    safe_addstr(win, ry, rx+2, "VC Market:      Cautious — focused on B2B", curses.color_pair(PAIR_WARN))
    ry += 1
    safe_addstr(win, ry, rx+2, "Platform Mood:  RepoRealm star count rising", curses.color_pair(PAIR_MUTED))
    ry += 1
    safe_addstr(win, ry, rx+2, "IndieScroll:    Solo devs trending", curses.color_pair(PAIR_ACCENT))

    ry += 2
    safe_addstr(win, ry, rx, "PLATFORM NEWS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw-1, PAIR_BORDER)
    ry += 1
    platform_news = [
        "⚠️  SnapStack pricing up 30% next quarter",
        "📉 CloudCastle outage caused 6hr downtime",
        "🔥 IndieScroll launch day record: 8K visitors",
        "💸 DeployGoblin acquired for $2M (rumoured)",
    ]
    for pn in platform_news:
        safe_addstr(win, ry, rx+2, pn[:rw-4], curses.color_pair(PAIR_MUTED))
        ry += 1

# ─────────────────────── RESEARCH TAB ─────────────────────────

@dataclass
class ResearchUIState:
    cat_sel: int = 0
    item_sel: int = 0

def draw_research(win, gs: GameState, ui: ResearchUIState):
    h, w = win.getmaxyx()
    y = 3
    mid = w // 3

    safe_addstr(win, y, 2, " RESEARCH TREE ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 20, "Unlock new capabilities across 8 domains.",
                curses.color_pair(PAIR_MUTED))
    y += 2

    # Left: Category list
    safe_addstr(win, y, 2, "CATEGORIES", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    for i, (cat, _) in enumerate(RESEARCH_CATEGORIES):
        is_sel = (i == ui.cat_sel)
        cp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        unlocked = sum(1 for item in RESEARCH_CATEGORIES[i][1]
                       if item in gs.founder.unlocked_research)
        total = len(RESEARCH_CATEGORIES[i][1])
        safe_addstr(win, y + i*2, 2, " "*(mid-4), curses.color_pair(cp))
        safe_addstr(win, y + i*2, 2, f" {prefix}{cat:<18} {unlocked}/{total}",
                    curses.color_pair(cp))

    # Right: Items in selected category
    rx = mid + 4
    rw = w - rx - 2
    ry = 5

    cat_name, cat_items = RESEARCH_CATEGORIES[ui.cat_sel]
    safe_addstr(win, ry, rx, f" {cat_name.upper()} UNLOCKS ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 2

    for j, item in enumerate(cat_items):
        is_sel = (j == ui.item_sel)
        is_unlocked = (item in gs.founder.unlocked_research)
        prefix = "▶ " if is_sel else "  "
        icon = "✓ " if is_unlocked else "○ "
        cp = (PAIR_BADGE_GREEN if is_unlocked else
              PAIR_HIGHLIGHT if is_sel else PAIR_PANEL)
        safe_addstr(win, ry, rx, " "*(rw-2), curses.color_pair(cp))
        safe_addstr(win, ry, rx, f" {prefix}{icon}{item}",
                    curses.color_pair(cp) | (curses.A_BOLD if is_sel else 0))

        if is_sel and not is_unlocked:
            safe_addstr(win, ry+1, rx+4, "Cost: 500 tokens + $200",
                        curses.color_pair(PAIR_WARN))
            safe_addstr(win, ry+1, rx+30, "[ Enter: Unlock ]",
                        curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)
        elif is_sel and is_unlocked:
            safe_addstr(win, ry+1, rx+4, "Already unlocked. Effect: active.",
                        curses.color_pair(PAIR_ACCENT))
        ry += 3

    safe_addstr(win, h-4, 2,
                "Up/Down: category  |  ◄/►: items  |  Enter: unlock",
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── NEWS TAB ─────────────────────────────

@dataclass
class NewsUIState:
    selected: int = 0

def draw_news(win, gs: GameState, ui: NewsUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " TECH NEWS FEED ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 20, "Fictional market intelligence for your decision-making.",
                curses.color_pair(PAIR_MUTED))
    y += 2

    categories = list(set(n["category"] for n in gs.news_feed))
    cat_x = 2
    safe_addstr(win, y, 2, "All  ", curses.color_pair(PAIR_TAB_ACTIVE))
    cat_x += 6
    for cat in categories:
        safe_addstr(win, y, cat_x, f"{cat}  ", curses.color_pair(PAIR_TAB_INACTIVE))
        cat_x += len(cat) + 3
    y += 2

    mid = w // 2
    lw = mid - 2

    # News list
    for i, item in enumerate(gs.news_feed[:min(len(gs.news_feed), h - y - 8)]):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        icon = item.get("icon", "📰")
        headline = item["headline"]
        category = item["category"]
        date = item["date"]
        safe_addstr(win, y + i*2, 1, " "*(lw), curses.color_pair(rp))
        safe_addstr(win, y + i*2, 2, f" {icon} {headline[:lw-12]}",
                    curses.color_pair(rp))
        safe_addstr(win, y + i*2 + 1, 4, f"  [{category}]  {date}",
                    curses.color_pair(PAIR_MUTED))

    # Detail panel
    rx = mid + 2
    rw = w - mid - 4
    if gs.news_feed and 0 <= ui.selected < len(gs.news_feed):
        item = gs.news_feed[ui.selected]
        ry = y
        safe_addstr(win, ry, rx, " STORY DETAIL ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        ry += 2
        safe_addstr(win, ry, rx+2, item["icon"] + " " + item["headline"][:rw-6],
                    curses.color_pair(PAIR_WARN) | curses.A_BOLD)
        ry += 2
        safe_addstr(win, ry, rx+2, f"Category: {item['category']}   Date: {item['date']}",
                    curses.color_pair(PAIR_MUTED))
        ry += 2
        effect_text = item.get("effect") or "No immediate gameplay effect."
        safe_addstr(win, ry, rx+2, "Effect:", curses.color_pair(PAIR_TITLE))
        safe_addstr(win, ry+1, rx+4, str(effect_text)[:rw-6], curses.color_pair(PAIR_MUTED))

    safe_addstr(win, h-4, 2, "Up/Down: select story  |  Enter: read full story",
                curses.color_pair(PAIR_MUTED))

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

# ─────────────────────── END DEMO SCREEN ──────────────────────

def draw_demo_end(win, gs: GameState):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_OVERLAY)

    center_text(win, 2, "╔═════════════════════════════════════════╗",
                curses.color_pair(PAIR_BORDER))
    center_text(win, 3, "║        FOUNDER REPORT — DEMO COMPLETE        ║",
                curses.color_pair(PAIR_TITLE_SCREEN) | curses.A_BOLD)
    center_text(win, 4, "╚═════════════════════════════════════════╝",
                curses.color_pair(PAIR_BORDER))

    total_rev  = sum(p.lifetime_revenue for p in gs.projects)
    total_users = sum(p.users for p in gs.projects)
    launched   = len([p for p in gs.projects if p.status not in ("In Dev",)])
    failed     = len([p for p in gs.projects if p.status == "Failed"])
    companies  = len(gs.companies)

    # Rank calculation
    score = total_rev // 100 + total_users // 10 + gs.founder.reputation
    if score > 500:    rank = "🏆 Tech Visionary"
    elif score > 200:  rank = "🚀 Serial Founder"
    elif score > 80:   rank = "⚡ Vibe Coder"
    elif score > 20:   rank = "🌱 Early Builder"
    else:              rank = "🐣 Rookie Founder"

    best_project = max(gs.projects, key=lambda p: p.lifetime_revenue, default=None)
    worst_project = max(gs.projects, key=lambda p: p.bug_count, default=None)

    rows = [
        ("Companies Created",   str(companies)),
        ("Projects Launched",   str(launched)),
        ("Projects Failed",     str(failed)),
        ("Total Revenue",       f"${total_rev:,}"),
        ("Total Users",         f"{total_users:,}"),
        ("Founder Reputation",  f"{gs.founder.reputation}/100"),
        ("Final Burnout",       f"{gs.founder.burnout}%"),
        ("Biggest Win",         best_project.name if best_project else "—"),
        ("Biggest Disaster",    worst_project.name if worst_project else "—"),
        ("Final Founder Rank",  rank),
    ]
    bw = 52
    bx = (w - bw) // 2
    by = 6
    draw_box(win, by, bx, len(rows)+4, bw, PAIR_BORDER, "FINAL STATS", PAIR_TITLE)
    for i, (label, val) in enumerate(rows):
        ry = by + 2 + i
        safe_addstr(win, ry, bx+4, f"{label:<28}", curses.color_pair(PAIR_MUTED))
        vp = PAIR_ACCENT if "Revenue" in label or "Win" in label else PAIR_WARN
        safe_addstr(win, ry, bx+32, val, curses.color_pair(vp) | curses.A_BOLD)

    center_text(win, by + len(rows) + 5,
                "Thanks for playing Vibe Coder Tycoon.",
                curses.color_pair(PAIR_MUTED))
    center_text(win, by + len(rows) + 6,
                "Press Q to exit or R to start a new game.",
                curses.color_pair(PAIR_MUTED))

# ─────────────────────── MONTH ADVANCE ────────────────────────

def advance_month(gs: GameState) -> str:
    gs.month += 1
    if gs.month > 12:
        gs.month = 1
        gs.year += 1
    gs.months_elapsed += 1

    sub = AI_SUBS[gs.active_ai_sub_idx]
    events_this_month = []

    # Apply company financials
    for c in gs.active_companies():
        c.cash += c.monthly_revenue - c.monthly_expenses
        c.cash = max(0, c.cash)
        c.valuation = c.cash + c.monthly_revenue * 12
        if c.cash == 0:
            events_this_month.append(
                ("💸", f"{c.name} ran out of cash!", "bad",
                 f"{MONTH_NAMES[gs.month-1]} {gs.year}"))

    # Progress in-dev projects
    for p in gs.projects:
        if p.status == "In Dev":
            speed = sub["speed"]
            p.progress = min(100, p.progress + random.randint(8, 12) + speed * 2)
            p.tokens_used += sub["tokens"] * random.randint(100, 300)
            gs.founder.total_tokens_used += sub["tokens"] * random.randint(1, 3)
            if p.progress >= 100:
                p.status = "Launched"
                p.launch_date = f"{MONTH_NAMES[gs.month-1]} {gs.year}"
                events_this_month.append(
                    ("🚀", f"{p.name} launched!", "good",
                     f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
        elif p.status in ("Launched", "Growing"):
            growth = random.randint(2, 8)
            p.revenue = max(0, p.revenue + growth * 10)
            p.users   = max(0, p.users + random.randint(10, 80))
            p.lifetime_revenue += p.revenue
            c = gs.company_by_id(p.company_id)
            if c:
                c.monthly_revenue = sum(proj.revenue for proj in gs.projects
                                        if proj.company_id == c.id)
            if p.revenue > 1000 and p.status == "Launched":
                p.status = "Growing"

    # Founder burnout
    burnout_delta = random.randint(-2, 5) - gs.founder.skill_management // 20
    gs.founder.burnout = max(0, min(100, gs.founder.burnout + burnout_delta))
    if gs.founder.burnout > 80:
        events_this_month.append(
            ("⚠️", "Founder burnout critical! Take a rest.", "bad",
             f"{MONTH_NAMES[gs.month-1]} {gs.year}"))

    # Reputation drift
    gs.founder.reputation = max(0, min(100, gs.founder.reputation + random.randint(-1, 3)))

    # Employee mood drift
    for emp in gs.employees:
        emp.mood = max(0, min(100, emp.mood + random.randint(-4, 4)))
        emp.productivity = max(0, min(100, emp.productivity + random.randint(-3, 3)))

    # Random news event
    random_news = [
        {"icon": "📰", "headline": "AI token costs drop 15% — good time to prototype",
         "category": "Market", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "⚠️",  "headline": "Market sentiment sours on consumer AI tools",
         "category": "Market", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "🔥",  "headline": "IndieScroll trending: solo builders hit 10K MRR",
         "category": "Community", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "💡",  "headline": "New open-source stack released — consider switching",
         "category": "Tools", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "💸",  "headline": "Angel round closed: $500K into micro-SaaS",
         "category": "Funding", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
    ]
    gs.news_feed.insert(0, random.choice(random_news))
    gs.news_feed = gs.news_feed[:20]

    gs.events = events_this_month + gs.events
    gs.events = gs.events[:20]

    date_str = f"{MONTH_NAMES[gs.month-1]} {gs.year}"
    return f"Month advanced to {date_str}. Cash: ${gs.total_cash():,}  Burnout: {gs.founder.burnout}%"

# ─────────────────────── MAIN LOOP ────────────────────────────

TICKERS = [
    "⚡ AI Index up 3.4% — investors bullish on LLM tooling",
    "💬 'I shipped a SaaS in 6 hours' — IndieScroll trending",
    "⚠️  SnapStack announces new pricing — devs panicking",
    "📣 BirdBoard top launch today: 8K users day one",
    "🌍 Beirut co-working scene expanding — builders arriving",
    "🤖 Llamurai 70B drops: open-source devs celebrate",
    "🏦 AngelBridge seed: $500K in 48h via cold emails",
    "📉 ChatNPC Turbo token costs rise 22% next quarter",
    "🔥 HuntProductive hits $50K MRR — solo founder",
    "💡 DeployGoblin acquired for $2M — rumours confirmed",
]

def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(100)

    # ── State ──
    screen = "title"    # title | sign_in | sign_up | credits | settings_pre | game
    title_sel = 0
    blink = True
    blink_tick = 0
    ticker_idx = 0
    ticker_tick = 0
    status_msg = ""

    sign_in_state = SignInState()
    sign_up_state = SignUpState()
    settings_ui   = SettingsUIState()
    standalone_settings = default_settings()

    gs: Optional[GameState] = None
    current_user: Optional[str] = None

    active_tab = 0
    dash_company_sel = 0
    companies_ui = CompaniesUIState()
    projects_ui  = ProjectsUIState()
    employees_ui = EmployeesUIState()
    research_ui  = ResearchUIState()
    news_ui      = NewsUIState()

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        blink_tick += 1
        if blink_tick >= 5:
            blink_tick = 0
            blink = not blink

        ticker_tick += 1
        if ticker_tick >= 60:
            ticker_tick = 0
            ticker_idx = (ticker_idx + 1) % len(TICKERS)

        # ── DRAW ──
        if screen == "title":
            draw_title_screen(stdscr, title_sel, blink)

        elif screen == "sign_in":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_in(stdscr, sign_in_state, blink)

        elif screen == "sign_up":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_up(stdscr, sign_up_state, blink)

        elif screen == "credits":
            draw_credits(stdscr)

        elif screen == "settings_pre":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_settings_screen(stdscr, None, settings_ui, standalone_settings)

        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            if gs.demo_ended:
                draw_demo_end(stdscr, gs)
            else:
                fill_background(stdscr, PAIR_PANEL)
                draw_topbar(stdscr, gs)
                draw_tabs(stdscr, active_tab)

                tab = TABS[active_tab]
                if tab == "Dashboard":
                    draw_dashboard(stdscr, gs, dash_company_sel)
                elif tab == "Founder":
                    draw_founder(stdscr, gs)
                elif tab == "Companies":
                    draw_companies(stdscr, gs, companies_ui)
                elif tab == "Projects":
                    draw_projects(stdscr, gs, projects_ui)
                elif tab == "Employees":
                    draw_employees(stdscr, gs, employees_ui)
                elif tab == "Market":
                    draw_market(stdscr, gs)
                elif tab == "Research":
                    draw_research(stdscr, gs, research_ui)
                elif tab == "News":
                    draw_news(stdscr, gs, news_ui)
                elif tab == "Settings":
                    draw_settings_screen(stdscr, gs, settings_ui)
                elif tab == "Help":
                    draw_help(stdscr)

                # Ticker
                ticker_msg = TICKERS[ticker_idx]
                safe_addstr(stdscr, h-2, 2, f" ▶ {ticker_msg} ",
                            curses.color_pair(PAIR_TICKER))
                draw_statusbar(stdscr, status_msg)

        stdscr.refresh()

        # ── INPUT ──
        key = stdscr.getch()
        if key == -1:
            continue

        # ── TITLE SCREEN ──
        if screen == "title":
            if key == curses.KEY_UP:
                title_sel = (title_sel - 1) % len(TITLE_MENU)
            elif key == curses.KEY_DOWN:
                title_sel = (title_sel + 1) % len(TITLE_MENU)
            elif key in (10, curses.KEY_ENTER, ord(' ')):
                sel_key, sel_label = TITLE_MENU[title_sel]
                if sel_key == "Q":
                    break
                elif sel_key == "S":
                    sign_in_state = SignInState()
                    screen = "sign_in"
                elif sel_key == "C":
                    sign_up_state = SignUpState()
                    screen = "sign_up"
                elif sel_key == "O":
                    # Play offline — create a quick offline founder
                    founder = Founder(
                        username="OfflineFounder",
                        background_idx=0,
                        reputation=20, burnout=0,
                        skill_prototyping=40, skill_sales=20,
                        skill_tech=35, skill_management=20,
                        total_tokens_used=0,
                    )
                    gs = make_new_game(founder, 0)
                    current_user = None
                    screen = "game"
                    active_tab = 0
                    status_msg = "Playing offline. Progress will not be saved."
                elif sel_key == "T":
                    screen = "settings_pre"
                elif sel_key == "R":
                    screen = "credits"
            # Keyboard shortcuts on title
            elif key == ord('q') or key == ord('Q'):
                break
            elif key == ord('s') or key == ord('S'):
                sign_in_state = SignInState()
                screen = "sign_in"
            elif key == ord('c') or key == ord('C'):
                sign_up_state = SignUpState()
                screen = "sign_up"
            elif key == ord('o') or key == ord('O'):
                founder = Founder(
                    username="OfflineFounder",
                    background_idx=0,
                    reputation=20, burnout=0,
                    skill_prototyping=40, skill_sales=20,
                    skill_tech=35, skill_management=20,
                    total_tokens_used=0,
                )
                gs = make_new_game(founder, 0)
                current_user = None
                screen = "game"
                status_msg = "Playing offline."
            elif key == ord('r') or key == ord('R'):
                screen = "credits"
            elif key == ord('t') or key == ord('T'):
                screen = "settings_pre"

        # ── SIGN IN ──
        elif screen == "sign_in":
            if sign_in_state.step == "welcome":
                if key in (10, curses.KEY_ENTER, 27):
                    # Load or create game for this user
                    loaded = load_game(current_user)
                    if loaded:
                        gs = loaded
                    else:
                        founder = Founder(
                            username=current_user,
                            background_idx=0,
                            reputation=20, burnout=0,
                            skill_prototyping=40, skill_sales=20,
                            skill_tech=35, skill_management=20,
                            total_tokens_used=0,
                        )
                        gs = make_new_game(founder, 0)
                    screen = "game"
                    status_msg = f"Welcome back, {current_user}!"
            else:
                if key == 27:  # Esc
                    screen = "title"
                elif key == curses.KEY_UP:
                    sign_in_state.focused = max(0, sign_in_state.focused - 1)
                elif key == curses.KEY_DOWN:
                    sign_in_state.focused = min(len(sign_in_state.fields)-1,
                                                sign_in_state.focused + 1)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    f = sign_in_state.fields[sign_in_state.focused]
                    f["value"] = f["value"][:-1]
                elif key in (10, curses.KEY_ENTER):
                    uname = sign_in_state.fields[0]["value"].strip()
                    pw    = sign_in_state.fields[1]["value"]
                    if not uname or not pw:
                        sign_in_state.message = "Please fill in both fields."
                    else:
                        name, data = accounts_sign_in(uname, pw)
                        if name:
                            current_user = name
                            sign_in_state.success_name   = name
                            sign_in_state.success_date   = data.get("last_played", "—")
                            sign_in_state.success_status = data.get("founder_status", "Rookie Founder")
                            sign_in_state.step = "welcome"
                        else:
                            sign_in_state.message = "Invalid username or password."
                elif 32 <= key < 127:
                    f = sign_in_state.fields[sign_in_state.focused]
                    if len(f["value"]) < 80:
                        f["value"] += chr(key)

        # ── SIGN UP ──
        elif screen == "sign_up":
            if sign_up_state.step == "form":
                if key == 27:
                    screen = "title"
                elif key == curses.KEY_UP:
                    sign_up_state.focused = max(0, sign_up_state.focused - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.focused = min(len(sign_up_state.fields)-1,
                                                sign_up_state.focused + 1)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    f = sign_up_state.fields[sign_up_state.focused]
                    f["value"] = f["value"][:-1]
                elif key in (10, curses.KEY_ENTER):
                    uname = sign_up_state.fields[0]["value"].strip()
                    email = sign_up_state.fields[1]["value"].strip()
                    pw1   = sign_up_state.fields[2]["value"]
                    pw2   = sign_up_state.fields[3]["value"]
                    if not uname or not email or not pw1:
                        sign_up_state.message = "All fields are required."
                    elif pw1 != pw2:
                        sign_up_state.message = "Passwords do not match."
                    elif len(uname) < 3:
                        sign_up_state.message = "Username must be at least 3 characters."
                    else:
                        ok, msg = accounts_create(uname, email, pw1)
                        if ok:
                            current_user = uname
                            sign_up_state.step = "founder"
                        else:
                            sign_up_state.message = msg
                elif 32 <= key < 127:
                    f = sign_up_state.fields[sign_up_state.focused]
                    mx = f.get("max", 80)
                    if len(f["value"]) < mx:
                        f["value"] += chr(key)

            elif sign_up_state.step == "founder":
                if key == 27:
                    sign_up_state.step = "form"
                elif key == curses.KEY_UP:
                    sign_up_state.founder_bg_sel = max(0, sign_up_state.founder_bg_sel - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.founder_bg_sel = min(len(BACKGROUNDS)-1,
                                                       sign_up_state.founder_bg_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    sign_up_state.step = "ai_sub"

            elif sign_up_state.step == "ai_sub":
                if key == 27:
                    sign_up_state.step = "founder"
                elif key == curses.KEY_UP:
                    sign_up_state.ai_sub_sel = max(0, sign_up_state.ai_sub_sel - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.ai_sub_sel = min(len(AI_SUBS)-1,
                                                   sign_up_state.ai_sub_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    bg_idx = sign_up_state.founder_bg_sel
                    bg     = BACKGROUNDS[bg_idx]
                    founder = Founder(
                        username=current_user,
                        background_idx=bg_idx,
                        reputation=20,
                        burnout=0,
                        skill_prototyping=40 + bg["bonuses"]["prototyping"],
                        skill_sales=20      + bg["bonuses"]["sales"],
                        skill_tech=35       + bg["bonuses"]["tech_skill"],
                        skill_management=20 + bg["bonuses"]["burnout_resist"],
                        total_tokens_used=0,
                    )
                    gs = make_new_game(founder, sign_up_state.ai_sub_sel)
                    screen = "game"
                    status_msg = f"Welcome, {current_user}! Your journey begins."

        # ── CREDITS ──
        elif screen == "credits":
            if key in (27, 10, curses.KEY_ENTER, ord('q'), ord('Q')):
                screen = "title"

        # ── SETTINGS (pre-game) ──
        elif screen == "settings_pre":
            if key == 27 or key in (10, curses.KEY_ENTER):
                screen = "title"
            elif key == curses.KEY_UP:
                settings_ui.focused = max(0, settings_ui.focused - 1)
            elif key == curses.KEY_DOWN:
                settings_ui.focused = min(len(settings_ui.keys)-1,
                                          settings_ui.focused + 1)
            else:
                _handle_settings_key(key, settings_ui, standalone_settings)

        # ── IN GAME ──
        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            if gs.demo_ended:
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('r') or key == ord('R'):
                    screen = "title"
                    gs = None
                continue

            # Global quit
            if key == ord('q') or key == ord('Q'):
                if current_user:
                    save_game(gs, current_user)
                break

            # Tab navigation
            if key == ord('\t'):
                active_tab = (active_tab + 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"
            elif key == curses.KEY_BTAB:
                active_tab = (active_tab - 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"

            tab = TABS[active_tab]

            # N: advance month (any tab)
            if key in (ord('n'), ord('N')):
                status_msg = advance_month(gs)
                if current_user:
                    save_game(gs, current_user)
                if gs.months_elapsed >= DEMO_MONTH_LIMIT:
                    gs.demo_ended = True
                continue

            # Tab-specific keys
            if tab == "Dashboard":
                if key == curses.KEY_UP:
                    dash_company_sel = max(0, dash_company_sel - 1)
                elif key == curses.KEY_DOWN:
                    dash_company_sel = min(len(gs.active_companies())-1,
                                           dash_company_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    active_tab = TABS.index("Companies")

            elif tab == "Companies":
                if companies_ui.view == "list":
                    if key == curses.KEY_UP:
                        companies_ui.selected = max(0, companies_ui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        companies_ui.selected = min(len(gs.companies)-1,
                                                    companies_ui.selected + 1)
                    elif key in (ord('n'), ord('N')):
                        companies_ui.view = "new"
                        companies_ui.message = ""
                    elif key in (10, curses.KEY_ENTER):
                        companies_ui.view = "detail"
                elif companies_ui.view in ("detail", "new"):
                    if key == 27:
                        companies_ui.view = "list"
                    elif companies_ui.view == "new":
                        _handle_new_company_keys(key, companies_ui, gs)

            elif tab == "Projects":
                if projects_ui.view == "list":
                    if key == curses.KEY_UP:
                        projects_ui.selected = max(0, projects_ui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        projects_ui.selected = min(len(gs.projects)-1,
                                                   projects_ui.selected + 1)
                    elif key == curses.KEY_LEFT:
                        filters = ["All", "In Dev", "Launched", "Growing", "Failed", "Archived", "Sold"]
                        idx = filters.index(projects_ui.filter_status)
                        projects_ui.filter_status = filters[(idx-1) % len(filters)]
                    elif key == curses.KEY_RIGHT:
                        filters = ["All", "In Dev", "Launched", "Growing", "Failed", "Archived", "Sold"]
                        idx = filters.index(projects_ui.filter_status)
                        projects_ui.filter_status = filters[(idx+1) % len(filters)]
                    elif key in (ord('n'), ord('N')):
                        if gs.active_companies():
                            projects_ui.view = "new"
                            projects_ui.new_step = 0
                            projects_ui.message = ""
                        else:
                            status_msg = "Create a company first before adding a project."
                elif projects_ui.view == "new":
                    if key == 27:
                        if projects_ui.new_step > 0:
                            projects_ui.new_step -= 1
                        else:
                            projects_ui.view = "list"
                    else:
                        _handle_new_project_keys(key, projects_ui, gs, status_msg)
                        # Check if we just confirmed and should go back
                        if projects_ui.view == "list":
                            status_msg = projects_ui.message

            elif tab == "Employees":
                if key == curses.KEY_UP:
                    employees_ui.selected = max(0, employees_ui.selected - 1)
                elif key == curses.KEY_DOWN:
                    employees_ui.selected = min(len(gs.employees)-1,
                                                employees_ui.selected + 1)
                elif key in (ord('h'), ord('H')):
                    # Hire a random employee
                    names = ["Ama Kwei", "Taro Naka", "Zara Malik", "Ivan Petrov",
                             "Lena Chen", "Rafi Hassan", "Suki Park", "Omar Ali"]
                    if gs.active_companies():
                        cid = gs.active_companies()[0].id
                        emp = Employee(
                            name=random.choice(names),
                            role=random.choice(EMPLOYEE_ROLES),
                            level=1,
                            salary=random.randint(1500, 3500),
                            mood=random.randint(70, 90),
                            skill=random.randint(40, 65),
                            hired_year=gs.year,
                            company_id=cid,
                            trait=random.choice(EMPLOYEE_TRAITS),
                        )
                        gs.employees.append(emp)
                        c = gs.company_by_id(cid)
                        if c:
                            c.monthly_expenses += emp.salary
                        status_msg = f"Hired {emp.name} as {emp.role}!"

            elif tab == "Research":
                if key == curses.KEY_UP:
                    research_ui.cat_sel = max(0, research_ui.cat_sel - 1)
                    research_ui.item_sel = 0
                elif key == curses.KEY_DOWN:
                    research_ui.cat_sel = min(len(RESEARCH_CATEGORIES)-1,
                                              research_ui.cat_sel + 1)
                    research_ui.item_sel = 0
                elif key == curses.KEY_LEFT:
                    research_ui.item_sel = max(0, research_ui.item_sel - 1)
                elif key == curses.KEY_RIGHT:
                    _, items = RESEARCH_CATEGORIES[research_ui.cat_sel]
                    research_ui.item_sel = min(len(items)-1, research_ui.item_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    _, items = RESEARCH_CATEGORIES[research_ui.cat_sel]
                    item = items[research_ui.item_sel]
                    if item not in gs.founder.unlocked_research:
                        gs.founder.unlocked_research.append(item)
                        gs.founder.total_tokens_used += 500
                        status_msg = f"Unlocked: {item}!"
                    else:
                        status_msg = f"{item} is already unlocked."

            elif tab == "News":
                if key == curses.KEY_UP:
                    news_ui.selected = max(0, news_ui.selected - 1)
                elif key == curses.KEY_DOWN:
                    news_ui.selected = min(len(gs.news_feed)-1, news_ui.selected + 1)

            elif tab == "Settings":
                if key == curses.KEY_UP:
                    settings_ui.focused = max(0, settings_ui.focused - 1)
                elif key == curses.KEY_DOWN:
                    settings_ui.focused = min(len(settings_ui.keys)-1,
                                              settings_ui.focused + 1)
                else:
                    _handle_settings_key(key, settings_ui, gs.settings)

def _handle_settings_key(key, ui: SettingsUIState, settings: dict):
    k = ui.keys[ui.focused]
    if k in SETTINGS_OPTIONS:
        opts = SETTINGS_OPTIONS[k]
        cur = settings.get(k, opts[0])
        try:    idx = opts.index(cur)
        except: idx = 0
        if key == curses.KEY_LEFT:
            settings[k] = opts[(idx-1) % len(opts)]
        elif key == curses.KEY_RIGHT:
            settings[k] = opts[(idx+1) % len(opts)]
        elif key in (10, curses.KEY_ENTER):
            settings[k] = opts[(idx+1) % len(opts)]
    elif isinstance(settings.get(k), bool):
        if key in (10, curses.KEY_ENTER, curses.KEY_LEFT, curses.KEY_RIGHT):
            settings[k] = not settings[k]

def _handle_new_company_keys(key, ui: CompaniesUIState, gs: GameState):
    idx = ui.new_focused
    f = ui.new_fields[idx]
    if key == curses.KEY_UP:
        ui.new_focused = max(0, ui.new_focused - 1)
    elif key == curses.KEY_DOWN:
        ui.new_focused = min(len(ui.new_fields)-1, ui.new_focused + 1)
    elif f["type"] == "options":
        opts = f["options"]
        if key == curses.KEY_LEFT:
            f["selected"] = (f["selected"] - 1) % len(opts)
        elif key == curses.KEY_RIGHT:
            f["selected"] = (f["selected"] + 1) % len(opts)
    elif f["type"] == "text":
        if key in (curses.KEY_BACKSPACE, 127, 8):
            f["value"] = f["value"][:-1]
        elif 32 <= key < 127 and len(f["value"]) < f.get("max", 30):
            f["value"] += chr(key)
    if key in (10, curses.KEY_ENTER) and ui.new_focused == len(ui.new_fields) - 1:
        name = ui.new_fields[0]["value"].strip() or "New Venture"
        legal = COMPANY_LEGAL_STYLES[ui.new_fields[1]["selected"]]
        focus = COMPANY_FOCUS_AREAS[ui.new_fields[2]["selected"]]
        funding = FUNDING_STYLES[ui.new_fields[3]["selected"]]
        risk = RISK_APPETITES[ui.new_fields[4]["selected"]]
        try:    cash = int(ui.new_fields[5]["value"])
        except: cash = 2000
        cid = len(gs.companies)
        c = Company(
            id=cid, name=name, legal_style=legal, focus_area=focus,
            funding_style=funding, risk_appetite=risk,
            cash=cash, monthly_revenue=0, monthly_expenses=300,
            debt=0, reputation=10, valuation=cash,
            office_level=1, mood=80,
            founded_month=gs.month, founded_year=gs.year,
            loans=[],
        )
        gs.companies.append(c)
        gs.events.insert(0, ("🏢", f"New company '{name}' founded!", "good",
                              f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
        ui.message = f"'{name}' created successfully!"
        ui.view = "list"

def _handle_new_project_keys(key, ui: ProjectsUIState, gs: GameState, status_msg: str):
    if ui.new_step == 0:
        active = gs.active_companies()
        if key == curses.KEY_UP:
            ui.new_company_idx = max(0, ui.new_company_idx - 1)
        elif key == curses.KEY_DOWN:
            ui.new_company_idx = min(len(active)-1, ui.new_company_idx + 1)
        elif key in (10, curses.KEY_ENTER):
            ui.new_step = 1

    elif ui.new_step == 1:
        idx = ui.new_focused
        f = ui.new_fields[idx]
        if key == curses.KEY_UP:
            ui.new_focused = max(0, ui.new_focused - 1)
        elif key == curses.KEY_DOWN:
            ui.new_focused = min(len(ui.new_fields)-1, ui.new_focused + 1)
        elif f.get("type") == "options":
            opts = f["options"]
            if key == curses.KEY_LEFT:
                f["selected"] = (f["selected"] - 1) % len(opts)
            elif key == curses.KEY_RIGHT:
                f["selected"] = (f["selected"] + 1) % len(opts)
        elif f.get("type") == "text":
            if key in (curses.KEY_BACKSPACE, 127, 8):
                f["value"] = f["value"][:-1]
            elif 32 <= key < 127 and len(f["value"]) < f.get("max", 30):
                f["value"] += chr(key)
        if key in (10, curses.KEY_ENTER) and ui.new_focused == len(ui.new_fields) - 1:
            ui.new_step = 2

    elif ui.new_step == 2:
        if key in (10, curses.KEY_ENTER):
            name     = ui.new_fields[0]["value"].strip() or "Unnamed Project"
            ptype    = PROJECT_TYPES[ui.new_fields[1]["selected"]]
            sub_name = [s["name"] for s in AI_SUBS][ui.new_fields[2]["selected"]]
            stack    = TECH_STACKS[ui.new_fields[3]["selected"]]
            niche    = NICHES[ui.new_fields[4]["selected"]]
            active   = gs.active_companies()
            cid      = active[ui.new_company_idx].id if active else 0
            p = Project(
                name=name, ptype=ptype, model=sub_name, stack=stack, niche=niche,
                company_id=cid, status="In Dev", progress=0,
                revenue=0, users=0, morale=80, tokens_used=0,
            )
            gs.projects.append(p)
            gs.events.insert(0, ("🚀", f"Project '{name}' started!", "good",
                                  f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
            ui.message = f"'{name}' added to your queue!"
            ui.view = "list"
            ui.new_step = 0

# ───────────────────────── ENTRY POINT ────────────────────────

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n  Thanks for playing Vibe Coder Tycoon\n")
    print("  Build fast. Ship often. Don't burn out.\n")