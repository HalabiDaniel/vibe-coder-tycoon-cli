import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee


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

