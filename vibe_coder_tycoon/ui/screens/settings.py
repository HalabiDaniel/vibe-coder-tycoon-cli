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

