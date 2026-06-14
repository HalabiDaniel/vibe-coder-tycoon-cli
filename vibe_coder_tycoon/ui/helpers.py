import curses
import unicodedata

from .colors import *
from ..constants import TABS, AI_SUBS, MONTH_NAMES
from ..models import GameState


# ─────────────────────── DRAWING HELPERS ──────────────────────

def char_width(ch):
    """Return the number of terminal cells a character occupies.

    Most emoji and symbols render two cells wide even though ``len`` counts
    them as a single character. Getting this right keeps column positions in
    the top bar aligned instead of overlapping/cutting each other off.
    """
    if ch == "\uFE0F" or unicodedata.combining(ch):
        return 0
    o = ord(ch)
    if (0x1F000 <= o <= 0x1FAFF or   # emoji & pictographs
            0x2600 <= o <= 0x27BF or  # misc symbols & dingbats (⚡ ⭐-ish)
            0x2B00 <= o <= 0x2BFF or  # ⭐ and friends
            0x1F900 <= o <= 0x1F9FF or
            unicodedata.east_asian_width(ch) in ("W", "F")):
        return 2
    return 1

def disp_width(text):
    """Display width of a string in terminal cells (emoji-aware)."""
    return sum(char_width(c) for c in text)

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
        "In Dev":       PAIR_BADGE_BLUE,
        "Dev Complete": PAIR_BADGE_AMBER,
        "Launched":     PAIR_BADGE_AMBER,
        "Growing":      PAIR_BADGE_GREEN,
        "Failed":       PAIR_BADGE_RED,
        "Sunset":       PAIR_BADGE_RED,
        "Archived":     PAIR_MUTED,
        "Sold":         PAIR_BADGE_AMBER,
        "Template":     PAIR_BADGE_GREEN,
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

def input_field(win, y, x, width, value, *, focus=False, secret=False, blink=False):
    """Draw a single-line text input with a visible border.

    Occupies 3 rows (top border, text row, bottom border) starting at row `y`
    and spanning `width` columns. A focused field gets a bright amber border;
    idle fields use a dim border so they stay visible but recede.
    """
    width = max(4, width)
    border_pair = PAIR_MENU_LOGO if focus else PAIR_MENU_DIM
    bp = curses.color_pair(border_pair) | (curses.A_BOLD if focus else 0)

    safe_addstr(win, y,     x, "┌" + "─" * (width - 2) + "┐", bp)
    safe_addstr(win, y + 1, x,             "│", bp)
    safe_addstr(win, y + 1, x + width - 1, "│", bp)
    safe_addstr(win, y + 2, x, "└" + "─" * (width - 2) + "┘", bp)

    display = ("•" * len(value)) if secret else value
    inner_w = width - 4                      # one space padding each side
    shown = display[-inner_w:] if len(display) > inner_w else display
    txt_attr = curses.color_pair(PAIR_MENU_OVERLAY) | (curses.A_BOLD if focus else 0)
    safe_addstr(win, y + 1, x + 2, shown.ljust(inner_w), txt_attr)

    if focus and blink:
        cx = x + 2 + min(len(shown), inner_w - 1)
        safe_addstr(win, y + 1, cx, "█", curses.color_pair(PAIR_MENU_LOGO) | curses.A_BLINK)

def _vibe_gauge(vibe: float, width: int = 5) -> str:
    """Render a fixed-width vibe bar using block chars."""
    filled = max(0, min(width, round(vibe / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def draw_topbar(win, gs: GameState):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(0, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))

    logo = " ⚡ VIBE CODER TYCOON "
    safe_addstr(win, 0, 1, logo, curses.color_pair(PAIR_LOGO) | curses.A_BOLD)

    f = gs.founder
    date_str = f"{MONTH_NAMES[gs.month-1]} {gs.year}"
    personal = f.personal_cash
    tokens   = f.total_tokens_used
    rep      = f.reputation
    vibe     = f.vibe
    gauge    = _vibe_gauge(vibe)

    # Choose vibe colour: calm (muted) → flowing (accent) → chaotic (warn)
    if vibe >= 70:
        vibe_pair = PAIR_WARN
    elif vibe >= 30:
        vibe_pair = PAIR_ACCENT
    else:
        vibe_pair = PAIR_MUTED

    # Player name right-aligned; reserve space so stats never collide.
    pname = f" 👤 {f.username}  "
    name_x = w - disp_width(pname) - 1
    safe_addstr(win, 0, name_x, pname,
                curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD)

    cx = disp_width(logo) + 2

    def _stat(text, attr):
        nonlocal cx
        tw = disp_width(text)
        if cx + tw > name_x:
            return False
        safe_addstr(win, 0, cx, text, attr)
        cx += tw
        return True

    _stat(f"  📅 {date_str}", curses.color_pair(PAIR_TOPBAR))
    _stat(f"  💰 ${personal:,.0f}", curses.color_pair(PAIR_TOPBAR) | curses.A_BOLD)
    _stat(f"  🪙 {tokens:,}K", curses.color_pair(PAIR_TOPBAR))
    _stat(f"  ⭐ Rep:{rep}", curses.color_pair(PAIR_TOPBAR))

    # Vibe gauge rendered with colour inline
    vibe_label = "  ✨ V:["
    if cx + disp_width(vibe_label) + 7 <= name_x:
        safe_addstr(win, 0, cx, vibe_label, curses.color_pair(PAIR_TOPBAR))
        cx += disp_width(vibe_label)
        safe_addstr(win, 0, cx, gauge, curses.color_pair(vibe_pair) | curses.A_BOLD)
        cx += len(gauge)
        safe_addstr(win, 0, cx, "]", curses.color_pair(PAIR_TOPBAR))
        cx += 1

    _stat(f"  🏢 {len(gs.active_companies())} cos", curses.color_pair(PAIR_TOPBAR))

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

    hints = " Tab→  Shift+Tab←  Q:Save & Menu  N:Next Month  Enter:Select "
    safe_addstr(win, 1, w - len(hints) - 1, hints, curses.color_pair(PAIR_MUTED))

def draw_statusbar(win, msg: str):
    h, w = win.getmaxyx()
    win.attron(curses.color_pair(PAIR_TOPBAR))
    win.hline(h-1, 0, " ", w)
    win.attroff(curses.color_pair(PAIR_TOPBAR))
    safe_addstr(win, h-1, 2, msg, curses.color_pair(PAIR_TOPBAR))

