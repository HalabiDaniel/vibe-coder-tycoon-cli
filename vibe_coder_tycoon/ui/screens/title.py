import curses
import time

from ..colors import *
from ..helpers import *
from ...constants import GAME_VERSION


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

    # Menu — framed panel with full-width selection bars
    item_w  = 32                 # inner width of each menu row
    box_w   = item_w + 4         # padding + borders
    box_x   = max(1, (w - box_w) // 2)
    box_y   = logo_y
    box_h   = len(TITLE_MENU) + 2

    draw_box(win, box_y, box_x, box_h, box_w, PAIR_BORDER,
             "MAIN MENU", PAIR_TITLE_SCREEN)

    bar_x = box_x + 2
    for i, (key, label) in enumerate(TITLE_MENU):
        row_y  = box_y + 1 + i
        is_sel = (i == sel)
        if is_sel:
            bar = f" ▶  [{key}]  {label}".ljust(item_w)
            safe_addstr(win, row_y, bar_x, bar,
                        curses.color_pair(PAIR_MENU_SEL) | curses.A_BOLD)
        else:
            safe_addstr(win, row_y, bar_x, " " * item_w,
                        curses.color_pair(PAIR_MENU_IDLE))
            key_txt = f"[{key}]"
            safe_addstr(win, row_y, bar_x + 4, key_txt,
                        curses.color_pair(PAIR_LOGO) | curses.A_BOLD)
            safe_addstr(win, row_y, bar_x + 4 + len(key_txt) + 2, label,
                        curses.color_pair(PAIR_MENU_IDLE))
    logo_y = box_y + box_h + 1

    # Blink hint
    if blink:
        hint = "↑↓ navigate   •   Enter select   •   hotkeys jump"
        center_text(win, logo_y, hint, curses.color_pair(PAIR_MUTED))
    logo_y += 2

    # Ticker band
    tickers_title = ["⚡ AI is the IDE now  ", "📦 Ship before you sleep  ",
                     "💸 MRR or nothing  ", "🌍 Build global, start local  "]
    tick_idx = int(time.time() * 0.5) % len(tickers_title)
    center_text(win, h-3, "  ".join(tickers_title), curses.color_pair(PAIR_TICKER))


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

