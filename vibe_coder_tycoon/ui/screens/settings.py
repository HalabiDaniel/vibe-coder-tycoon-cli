import curses
import time
import random
from typing import Optional
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import *
from ...models import GameState, Founder, Company, Project, Employee
from ...persistence import default_settings


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

    # In-game settings live inside the game panel theme; the standalone
    # version (reached from the main menu) uses the warm menu theme.
    if gs:
        bg_pair, title_pair = PAIR_PANEL, PAIR_TITLE
        focus_pair, muted_pair = PAIR_ACCENT, PAIR_MUTED
        option_badge = PAIR_BADGE_BLUE
    else:
        bg_pair, title_pair = PAIR_MENU_OVERLAY, PAIR_MENU_TITLE
        focus_pair, muted_pair = PAIR_MENU_ACCENT, PAIR_MENU_DIM
        option_badge = PAIR_BADGE_AMBER

    # In-game, the topbar (row 0) and tabs (row 1) are already drawn by the
    # main loop, so only fill the content area beneath them. Standalone fills
    # the whole screen.
    if gs:
        for row in range(2, h):
            win.attron(curses.color_pair(bg_pair))
            win.hline(row, 0, " ", w)
            win.attroff(curses.color_pair(bg_pair))
        title_y = 3
    else:
        fill_background(win, bg_pair)
        title_y = 3

    safe_addstr(win, title_y, 2, " SETTINGS ", curses.color_pair(title_pair) | curses.A_BOLD)
    y = title_y + 2

    for i, (key, label) in enumerate(zip(state.keys, state.labels)):
        is_focus = (i == state.focused)
        prefix = "▶ " if is_focus else "  "
        la = (curses.color_pair(focus_pair) | curses.A_BOLD if is_focus
              else curses.color_pair(muted_pair))
        safe_addstr(win, y, 4, f"{prefix}{label:<26}", la)

        val = settings.get(key, "")
        if isinstance(val, bool):
            vstr = "ON" if val else "OFF"
            vp = PAIR_BADGE_GREEN if val else PAIR_BADGE_RED
        elif key in SETTINGS_OPTIONS:
            vstr = str(val).upper()
            vp = option_badge
        else:
            vstr = str(val)
            vp = muted_pair

        badge(win, y, 34, vstr, vp)

        if is_focus:
            if key in SETTINGS_OPTIONS:
                safe_addstr(win, y, 50, "◄/► to cycle", curses.color_pair(muted_pair))
            else:
                safe_addstr(win, y, 50, "Enter to toggle", curses.color_pair(muted_pair))
        y += 2

    y += 1
    safe_addstr(win, y, 4, "[ Save & Return ]",
                curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    if not gs:
        center_text(win, h-3, "Up/Down: field  |  ◄/►: change  |  Esc: back",
                    curses.color_pair(muted_pair))

