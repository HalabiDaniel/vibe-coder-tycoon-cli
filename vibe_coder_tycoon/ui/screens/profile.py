import curses

from ..colors import *
from ..helpers import *


# ─────────────────────── PROFILE SCREEN ───────────────────────

def draw_profile(win, current_user: str, cloud_email: str, cloud_slots: list):
    h, w = win.getmaxyx()
    fill_background(win, PAIR_MENU_OVERLAY)

    center_text(win, 2, "PROFILE", curses.color_pair(PAIR_MENU_TITLE) | curses.A_BOLD)

    bw = min(60, w - 4)
    bx = (w - bw) // 2

    # ── Player info panel ──
    by = 4
    info_rows = [
        ("Username",     current_user or "—"),
        ("Email",        cloud_email or "—"),
        ("Status",       "Signed In" if cloud_email else "Offline"),
    ]
    panel_h = len(info_rows) + 2
    draw_box(win, by, bx, panel_h, bw, PAIR_MENU_BORDER, "PLAYER INFO", PAIR_MENU_TITLE)
    for i, (label, value) in enumerate(info_rows):
        ry = by + 1 + i
        safe_addstr(win, ry, bx + 2, f"{label:<14}", curses.color_pair(PAIR_MENU_DIM))
        is_signed_in = label == "Status" and value == "Signed In"
        attr = curses.color_pair(PAIR_MENU_ACCENT) if is_signed_in else curses.color_pair(PAIR_MENU_TITLE)
        safe_addstr(win, ry, bx + 16, str(value)[:bw - 18], attr)

    # ── Cloud saves panel ──
    saves_y = by + panel_h + 1
    saves_inner_h = max(3, len(cloud_slots)) if cloud_slots else 3
    saves_h = saves_inner_h + 2
    draw_box(win, saves_y, bx, saves_h, bw, PAIR_MENU_BORDER, "CLOUD SAVES", PAIR_MENU_TITLE)

    if not cloud_slots:
        center_text(win, saves_y + 1, "No cloud saves found.",
                    curses.color_pair(PAIR_MENU_DIM))
        center_text(win, saves_y + 2, "Start a game to create your first save.",
                    curses.color_pair(PAIR_MENU_DIM))
    else:
        for i, slot in enumerate(cloud_slots[:saves_inner_h]):
            ry = saves_y + 1 + i
            slot_name = slot.get("slot_name", "autosave")
            updated   = (slot.get("updated_at") or "")[:10] or "Unknown"
            meta      = slot.get("metadata") or {}
            months    = meta.get("months_elapsed", "?")
            row = f"  {slot_name:<16}  Updated: {updated:<12}  Month {months}"
            safe_addstr(win, ry, bx + 1, row[:bw - 2], curses.color_pair(PAIR_MENU_IDLE))

    center_text(win, h - 3, "Esc / Enter: back to menu",
                curses.color_pair(PAIR_MENU_DIM))
