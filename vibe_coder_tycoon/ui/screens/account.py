import curses
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *


# ─────────────────────── ACCOUNT SCREEN ───────────────────────

@dataclass
class AccountUIState:
    selected: int = 0  # focused button index
    message: str = ""

_BUTTONS = ["Sync Now", "Log Out", "Delete Local Session", "Back"]

def draw_account(win, gs, state: AccountUIState, cloud_info: dict):
    """
    cloud_info keys (all optional):
      username, email, founder_name, background, login_status,
      last_sync, slot_name, is_configured
    """
    h, w = win.getmaxyx()
    fill_background(win, PAIR_MENU_OVERLAY)

    center_text(win, 2, "ACCOUNT", curses.color_pair(PAIR_MENU_TITLE) | curses.A_BOLD)

    bw = min(58, w - 4)
    bx = (w - bw) // 2

    # ── Info panel ──
    by = 4
    rows = [
        ("Username",       cloud_info.get("username", "—")),
        ("Email",          cloud_info.get("email", "—")),
        ("Founder",        cloud_info.get("founder_name", "—")),
        ("Background",     cloud_info.get("background", "—")),
        ("Login status",   cloud_info.get("login_status", "Offline")),
        ("Last cloud sync",cloud_info.get("last_sync", "Never")),
        ("Save slot",      cloud_info.get("slot_name", "autosave")),
    ]
    draw_box(win, by, bx, len(rows) + 2, bw, PAIR_MENU_BORDER, "PROFILE", PAIR_MENU_TITLE)
    for i, (label, value) in enumerate(rows):
        ry = by + 1 + i
        safe_addstr(win, ry, bx + 2, f"{label:<16}", curses.color_pair(PAIR_MENU_DIM))
        val_pair = PAIR_MENU_ACCENT if label == "Login status" and value == "Signed In" else PAIR_MENU_TITLE
        safe_addstr(win, ry, bx + 18, str(value)[:bw - 20], curses.color_pair(val_pair))

    if not cloud_info.get("is_configured"):
        center_text(win, by + len(rows) + 3,
                    "Cloud not configured. Set SUPABASE_URL and SUPABASE_KEY in .env",
                    curses.color_pair(PAIR_WARN))

    # ── Buttons ──
    btn_y = by + len(rows) + 5
    for i, label in enumerate(_BUTTONS):
        is_sel = (i == state.selected)
        attr = curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD if is_sel else curses.color_pair(PAIR_MENU_BUTTON)
        btext = f"[ {label} ]"
        bx_btn = bx + 2 + i * 18
        safe_addstr(win, btn_y, bx_btn, btext, attr)

    if state.message:
        mp = PAIR_DANGER if "failed" in state.message.lower() or "error" in state.message.lower() else PAIR_MENU_ACCENT
        center_text(win, btn_y + 2, state.message, curses.color_pair(mp) | curses.A_BOLD)

    center_text(win, h - 3, "Left/Right: choose action  |  Enter: confirm  |  Esc: back",
                curses.color_pair(PAIR_MENU_DIM))


def account_button_label(idx: int) -> str:
    return _BUTTONS[idx] if 0 <= idx < len(_BUTTONS) else ""


ACCOUNT_BUTTON_COUNT = len(_BUTTONS)
