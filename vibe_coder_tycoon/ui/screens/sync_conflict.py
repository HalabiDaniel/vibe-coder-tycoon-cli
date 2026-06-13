import curses
from dataclasses import dataclass

from ..colors import *
from ..helpers import *


# ─────────────────────── SYNC CONFLICT SCREEN ─────────────────

CONFLICT_OPTIONS = [
    ("Upload local",    "Keep local save. Upload it and overwrite the cloud."),
    ("Download cloud",  "Download cloud save. Replace your local save."),
    ("Keep both",       "Keep both. Local save becomes 'local-backup' slot in cloud."),
    ("Stay offline",    "Continue offline. No changes to cloud or local saves."),
]


def draw_sync_conflict(win, local_info: dict, cloud_info: dict, sel: int):
    """
    local_info / cloud_info keys: last_played, cash, projects, months_elapsed
    sel: 0-3 (currently highlighted choice)
    """
    h, w = win.getmaxyx()
    fill_background(win, PAIR_MENU_OVERLAY)

    center_text(win, 1, "SAVE CONFLICT DETECTED", curses.color_pair(PAIR_DANGER) | curses.A_BOLD)
    center_text(win, 2, "Both your local and cloud saves have changed since last sync.",
                curses.color_pair(PAIR_MENU_DIM))

    bw = min(30, (w - 6) // 2)
    gap = 4
    total = bw * 2 + gap
    lx = (w - total) // 2
    rx = lx + bw + gap
    by = 4

    # ── Local save panel ──
    draw_box(win, by, lx, 7, bw, PAIR_MENU_BORDER, "LOCAL SAVE", PAIR_MENU_TITLE)
    _draw_save_info(win, by + 1, lx + 2, local_info, bw - 4)

    # ── Cloud save panel ──
    draw_box(win, by, rx, 7, bw, PAIR_MENU_BORDER, "CLOUD SAVE", PAIR_BADGE_BLUE)
    _draw_save_info(win, by + 1, rx + 2, cloud_info, bw - 4)

    # ── Options ──
    opt_y = by + 8
    center_text(win, opt_y - 1, "Choose what to do:", curses.color_pair(PAIR_MENU_TITLE) | curses.A_BOLD)
    opt_bw = min(58, w - 4)
    opt_bx = (w - opt_bw) // 2

    for i, (label, desc) in enumerate(CONFLICT_OPTIONS):
        is_sel = (i == sel)
        ry = opt_y + i * 3
        prefix = "▶ " if is_sel else "  "
        name_attr = curses.color_pair(PAIR_MENU_ACCENT) | curses.A_BOLD if is_sel else curses.color_pair(PAIR_MENU_TITLE)
        safe_addstr(win, ry, opt_bx, f"{prefix}{i+1}. {label}", name_attr)
        safe_addstr(win, ry + 1, opt_bx + 5, desc[:opt_bw - 6], curses.color_pair(PAIR_MENU_DIM))

    center_text(win, h - 3, "Up/Down: choose  |  Enter: confirm",
                curses.color_pair(PAIR_MENU_DIM))


def _draw_save_info(win, y: int, x: int, info: dict, width: int):
    lines = [
        ("Last played", info.get("last_played", "—")),
        ("Cash",        f"${info.get('cash', 0):,}"),
        ("Projects",    str(info.get("projects", 0))),
        ("Month",       str(info.get("months_elapsed", 0))),
        ("Companies",   str(info.get("companies", 0))),
    ]
    for i, (label, value) in enumerate(lines):
        safe_addstr(win, y + i, x, f"{label}: ", curses.color_pair(PAIR_MENU_DIM))
        safe_addstr(win, y + i, x + len(label) + 2, str(value)[:width - len(label) - 3],
                    curses.color_pair(PAIR_MENU_TITLE))
