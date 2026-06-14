"""
Phase 13 — Event-card overlay.

Renders the top pending event choice-card (gs.pending_event_cards[0]) as a modal
over the current game screen. Input routing lives in app.py.
"""

import curses
import textwrap

from ..colors import (
    PAIR_OVERLAY, PAIR_DANGER, PAIR_WARN, PAIR_ACCENT, PAIR_MUTED,
    PAIR_BUTTON_FOCUS, PAIR_TITLE,
)
from ..helpers import safe_addstr, draw_box


_CATEGORY_PAIR = {
    "positive": PAIR_ACCENT,
    "negative": PAIR_DANGER,
    "meme": PAIR_WARN,
    "founder": PAIR_WARN,
}


def draw_event_card(win, card: dict, sel: int):
    h, w = win.getmaxyx()
    choices = card.get("choices", [])
    body = card.get("body", "")

    bw = min(72, w - 6)
    bx = (w - bw) // 2
    wrapped = textwrap.wrap(body, bw - 6) if body else []
    bh = 6 + len(wrapped) + len(choices)
    by = max(2, (h - bh) // 2)

    border_pair = _CATEGORY_PAIR.get(card.get("category"), PAIR_WARN)

    # Dim/fill the card area
    for row in range(by, min(h - 1, by + bh)):
        safe_addstr(win, row, bx, " " * bw, curses.color_pair(PAIR_OVERLAY))

    title = f"{card.get('icon', '🃏')}  {card.get('title', 'Event')}"
    draw_box(win, by, bx, bh, bw, border_pair, title[:bw - 4], border_pair)

    y = by + 2
    for ln in wrapped:
        safe_addstr(win, y, bx + 3, ln, curses.color_pair(PAIR_OVERLAY))
        y += 1

    y += 1
    for i, ch in enumerate(choices):
        is_sel = (i == sel)
        prefix = "▶ " if is_sel else "  "
        cp = PAIR_BUTTON_FOCUS if is_sel else PAIR_OVERLAY
        attr = curses.color_pair(cp) | (curses.A_BOLD if is_sel else 0)
        safe_addstr(win, y, bx + 3, f"{prefix}{ch['label']}"[:bw - 6], attr)
        y += 1

    safe_addstr(win, by + bh - 1, bx + 3,
                " ↑/↓ choose   Enter confirm ",
                curses.color_pair(PAIR_MUTED))
