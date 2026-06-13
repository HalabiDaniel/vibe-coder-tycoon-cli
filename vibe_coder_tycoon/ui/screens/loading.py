import curses
import time

from ..colors import *
from ..helpers import (
    safe_addstr, fill_background, center_text, draw_box, progress_bar,
)
from ...constants import GAME_VERSION
from .title import LOGO_ART


# ─────────────────────── LOADING SCREEN ───────────────────────

LOADING_LOGO = [
    "  ██╗   ██╗ ██████╗████████╗",
    "  ██║   ██║██╔════╝╚══██╔══╝",
    "  ╚██╗ ██╔╝██║        ██║   ",
    "   ╚████╔╝ ██║        ██║   ",
    "    ╚═══╝  ╚██████╗   ██║   ",
    "           ╚═════╝   ╚═╝    ",
]

# Flavour messages shown as the bar fills. Each is roughly a slice of the load.
LOADING_STEPS = [
    "Booting dev environment...",
    "Spinning up AI subscriptions...",
    "Brewing coffee ☕...",
    "Fetching the latest hot takes...",
    "Compiling your empire...",
    "Negotiating with investors...",
    "Deploying to production 🚀...",
    "Almost there, holding our breath...",
]

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def draw_loading_screen(win, pct: float, step_msg: str, spin_char: str):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_MENU_OVERLAY)

    # Decorative border
    safe_addstr(win, 0,   0, "╔" + "═" * (w - 2) + "╗", curses.color_pair(PAIR_MENU_BORDER))
    safe_addstr(win, h-1, 0, "╚" + "═" * (w - 2) + "╝", curses.color_pair(PAIR_MENU_BORDER))
    for r in range(1, h - 1):
        safe_addstr(win, r, 0,   "║", curses.color_pair(PAIR_MENU_BORDER))
        safe_addstr(win, r, w-1, "║", curses.color_pair(PAIR_MENU_BORDER))

    # Logo block, vertically centred-ish. Use the full illustrated
    # "VIBE CODER TYCOON" art when the terminal is large enough, otherwise
    # fall back to the compact VCT block so it still fits.
    use_full = (w >= 80 and h >= 28)
    logo = LOGO_ART if use_full else LOADING_LOGO

    logo_y = max(2, (h // 2) - (len(logo) // 2) - 3)
    for i, line in enumerate(logo):
        center_text(win, logo_y + i, line, curses.color_pair(PAIR_MENU_LOGO) | curses.A_BOLD)

    title_y = logo_y + len(logo) + 1
    if not use_full:
        center_text(win, title_y, "VIBE CODER TYCOON",
                    curses.color_pair(PAIR_MENU_TITLE) | curses.A_BOLD)
        title_y += 1
    center_text(win, title_y, f"─── {GAME_VERSION} ───",
                curses.color_pair(PAIR_MENU_DIM))

    # Progress bar
    bar_w = min(50, w - 10)
    bar_x = max(1, (w - bar_w) // 2)
    bar_y = title_y + 3
    progress_bar(win, bar_y, bar_x, bar_w, pct, PAIR_BADGE_GREEN, PAIR_MENU_BORDER)

    pct_txt = f"{int(pct)}%"
    center_text(win, bar_y + 1, pct_txt, curses.color_pair(PAIR_MENU_ACCENT) | curses.A_BOLD)

    # Spinner + current step message
    msg = f"{spin_char}  {step_msg}"
    center_text(win, bar_y + 3, msg, curses.color_pair(PAIR_MENU_TITLE))


def run_loading_screen(stdscr, duration: float = 3.0):
    """Blocks for ~`duration` seconds while animating a loading screen."""
    start = time.time()
    spin_idx = 0
    n_steps = len(LOADING_STEPS)

    stdscr.nodelay(True)  # non-blocking getch so timing stays accurate
    try:
        while True:
            elapsed = time.time() - start
            pct = min(100.0, (elapsed / duration) * 100.0)

            step_idx = min(n_steps - 1, int((pct / 100.0) * n_steps))
            step_msg = LOADING_STEPS[step_idx]
            spin_char = SPINNER[spin_idx % len(SPINNER)]
            spin_idx += 1

            stdscr.erase()
            draw_loading_screen(stdscr, pct, step_msg, spin_char)
            stdscr.refresh()

            if elapsed >= duration:
                break

            # ~12 fps animation; a keypress skips the rest of the wait
            time.sleep(0.08)
            if stdscr.getch() != -1:
                break
    finally:
        stdscr.nodelay(False)
        stdscr.timeout(100)
