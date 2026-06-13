import curses

from .colors import *
from ..constants import TABS, AI_SUBS, MONTH_NAMES
from ..models import GameState


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

