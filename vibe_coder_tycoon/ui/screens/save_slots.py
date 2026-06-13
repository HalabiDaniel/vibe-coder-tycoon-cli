import curses
from dataclasses import dataclass

from ..colors import *
from ..helpers import *


# ─────────────────────── SAVE SLOTS SCREEN ────────────────────

@dataclass
class SaveSlotsUIState:
    selected: int = 0
    message: str = ""


def draw_save_slots(win, slots: list, state: SaveSlotsUIState):
    """
    slots: list of dicts from cloud.list_save_slots(), each has:
      id, slot_name, game_version, updated_at,
      plus flattened save_data fields if available
    An extra synthetic entry "Start New Game" is always appended.
    """
    h, w = win.getmaxyx()
    fill_background(win, PAIR_MENU_OVERLAY)

    center_text(win, 2, "CLOUD SAVE SLOTS", curses.color_pair(PAIR_MENU_TITLE) | curses.A_BOLD)
    center_text(win, 3, "Choose a cloud save to continue, or start a new game.",
                curses.color_pair(PAIR_MENU_DIM))

    bw = min(62, w - 4)
    bx = (w - bw) // 2
    by = 5

    all_entries = list(slots) + [{"_new": True}]
    box_h = len(all_entries) * 4 + 2
    draw_box(win, by, bx, box_h, bw, PAIR_MENU_BORDER, "AVAILABLE SAVES", PAIR_MENU_TITLE)

    for i, slot in enumerate(all_entries):
        is_sel = (i == state.selected)
        row_y = by + 1 + i * 4
        prefix = "▶ " if is_sel else "  "
        name_attr = curses.color_pair(PAIR_MENU_ACCENT) | curses.A_BOLD if is_sel else curses.color_pair(PAIR_MENU_TITLE)

        if slot.get("_new"):
            safe_addstr(win, row_y, bx + 2, f"{prefix}Start New Game", name_attr)
            safe_addstr(win, row_y + 1, bx + 6, "Begin a fresh founder journey.",
                        curses.color_pair(PAIR_MENU_DIM))
        else:
            name = slot.get("slot_name", "save")
            version = slot.get("game_version", "")
            updated = _fmt_date(slot.get("updated_at", ""))
            safe_addstr(win, row_y, bx + 2, f"{prefix}{name}  [{version}]", name_attr)
            safe_addstr(win, row_y + 1, bx + 6, f"Last played: {updated}",
                        curses.color_pair(PAIR_MENU_DIM))

        if i < len(all_entries) - 1:
            safe_addstr(win, row_y + 3, bx, "─" * bw, curses.color_pair(PAIR_MENU_BORDER))

    if state.message:
        mp = PAIR_DANGER if "error" in state.message.lower() else PAIR_MENU_ACCENT
        center_text(win, by + box_h + 1, state.message, curses.color_pair(mp) | curses.A_BOLD)

    center_text(win, h - 3, "Up/Down: choose  |  Enter: load  |  Esc: cancel",
                curses.color_pair(PAIR_MENU_DIM))


def _fmt_date(iso: str) -> str:
    if not iso:
        return "Unknown"
    # "2025-03-14T12:34:56..." → "2025-03-14"
    return iso[:10] if len(iso) >= 10 else iso
