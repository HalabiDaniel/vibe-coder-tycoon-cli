"""
Phase 2 — Development Dashboard UI
Shows Design/Tech/Bug bars, terminal log, action panel, and interruption overlays.
"""

import curses
from dataclasses import dataclass, field

from ..colors import (
    PAIR_TITLE, PAIR_PANEL, PAIR_BORDER, PAIR_ACCENT, PAIR_MUTED, PAIR_BUTTON,
    PAIR_BUTTON_FOCUS, PAIR_HIGHLIGHT, PAIR_DANGER, PAIR_WARN, PAIR_BADGE_GREEN,
    PAIR_BADGE_RED, PAIR_BADGE_BLUE, PAIR_OVERLAY,
)
from ..helpers import safe_addstr, draw_box, hline, progress_bar, badge
from ...constants import DEV_ACTIONS, QA_OPTIONS, AI_SUBS, FEATURE_SCOPES
from ...models import GameState


@dataclass
class DevUIState:
    action_sel: int = 0       # 0-4: which action button is highlighted
    qa_sel: int = 0           # index into QA_OPTIONS
    log_scroll: int = 0       # future: scroll terminal log


# ─────────────────────── MAIN DRAW ────────────────────────────


def draw_development(win, gs: GameState, project_idx: int, dev_ui: DevUIState):
    """Draw the full development dashboard for the given project."""
    h, w = win.getmaxyx()

    if project_idx < 0 or project_idx >= len(gs.projects):
        safe_addstr(win, 5, 4, "No project selected.", curses.color_pair(PAIR_DANGER))
        return

    p = gs.projects[project_idx]
    ds = p.dev_session

    # ── Header ────────────────────────────────────────────────
    c = gs.company_by_id(p.company_id)
    cname = c.name[:22] if c else "—"
    paused_tag = "  [PAUSED]" if p.paused_dev else ""
    sub = AI_SUBS[gs.active_ai_sub_idx]

    header = f" DEV: {p.name:<22}{paused_tag}   Day {p.dev_day}/{p.dev_total_days}   {cname} "
    safe_addstr(win, 3, 2, header[:w - 4], curses.color_pair(PAIR_TITLE) | curses.A_BOLD)

    prog_pct = int(100 * p.dev_day / max(1, p.dev_total_days))
    progress_bar(win, 3, 2 + len(header), min(20, w - len(header) - 6), prog_pct,
                 PAIR_BADGE_GREEN, PAIR_MUTED)
    safe_addstr(win, 3, 2 + len(header) + min(20, w - len(header) - 6) + 1,
                f" {prog_pct}%", curses.color_pair(PAIR_ACCENT))

    hline(win, 4, 1, w - 2, PAIR_BORDER)

    # ── Left column: bars ─────────────────────────────────────
    mid = w // 2
    bar_w = max(10, mid - 20)
    y = 5

    safe_addstr(win, y, 4, "DEVELOPMENT BARS", curses.color_pair(PAIR_MUTED) | curses.A_BOLD)
    y += 2

    _draw_stat_bar(win, y,     4, "Design", int(p.design_score), bar_w, PAIR_BADGE_BLUE)
    _draw_stat_bar(win, y + 2, 4, "Tech  ", int(p.tech_score),   bar_w, PAIR_BADGE_GREEN)

    bug_pair = PAIR_BADGE_RED if p.bug_count > 15 else (PAIR_WARN if p.bug_count > 7 else PAIR_BADGE_GREEN)
    safe_addstr(win, y + 4, 4, f"{'Bugs  ':<7}", curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y + 4, 11, f"{p.bug_count:>3} bugs", curses.color_pair(bug_pair) | curses.A_BOLD)

    safe_addstr(win, y + 6, 4, "Hype  ", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y + 6, 11, bar_w, p.hype, PAIR_ACCENT, PAIR_MUTED)
    safe_addstr(win, y + 6, 12 + bar_w, f" {p.hype}", curses.color_pair(PAIR_ACCENT))

    # QA selector
    safe_addstr(win, y + 8, 4, "QA Level  ", curses.color_pair(PAIR_MUTED))
    qa_name = p.qa_level
    qa_pair = PAIR_DANGER if qa_name == "Skip QA" else (PAIR_WARN if qa_name == "Light QA" else PAIR_BADGE_GREEN)
    safe_addstr(win, y + 8, 14, f"◄ {qa_name} ►", curses.color_pair(qa_pair) | curses.A_BOLD)

    # AI info
    safe_addstr(win, y + 10, 4,
                f"AI: {sub['name']}  (quality {sub['quality']}  bug_risk {sub['bug_risk']})",
                curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y + 11, 4,
                f"Scope: {p.scope}  Faked features: {len(p.faked_features)}",
                curses.color_pair(PAIR_MUTED))

    if p.status == "Dev Complete":
        safe_addstr(win, y + 13, 4,
                    f"Quality Score: {p.quality_score}/100",
                    curses.color_pair(PAIR_BADGE_GREEN) | curses.A_BOLD)
        safe_addstr(win, y + 14, 4,
                    "[ L ] Launch Project",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    # Vertical divider
    for row in range(4, h - 6):
        safe_addstr(win, row, mid, "│", curses.color_pair(PAIR_BORDER))

    # ── Right column: terminal log ────────────────────────────
    safe_addstr(win, 5, mid + 2, "TERMINAL LOG", curses.color_pair(PAIR_MUTED) | curses.A_BOLD)

    log_area_h = h - 6 - 5 - 1  # rows available for log
    log_lines = ds.terminal_log if ds else ["No dev session active."]
    visible_lines = log_lines[-log_area_h:] if len(log_lines) > log_area_h else log_lines

    for i, line in enumerate(visible_lines):
        ry = 7 + i
        if ry >= h - 7:
            break
        # Color-code by prefix
        if line.startswith("⚠️") or line.startswith("⏸"):
            lp = PAIR_DANGER
        elif line.startswith(">"):
            lp = PAIR_ACCENT
        elif line.startswith("[") or line.startswith("Resolved"):
            lp = PAIR_BADGE_GREEN
        else:
            lp = PAIR_MUTED
        safe_addstr(win, ry, mid + 2, line[: w - mid - 4], curses.color_pair(lp))

    # ── Action panel ──────────────────────────────────────────
    sep_y = h - 7
    hline(win, sep_y, 1, w - 2, PAIR_BORDER)
    safe_addstr(win, sep_y, 3, " ACTIONS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)

    actions_row1 = DEV_ACTIONS[:3]
    actions_row2 = DEV_ACTIONS[3:]
    ax = 2
    for i, act in enumerate(actions_row1):
        is_sel = (i == dev_ui.action_sel)
        ap = PAIR_BUTTON_FOCUS if is_sel else PAIR_BUTTON
        label = f"[{act['key']}] {act['name']}"
        cost = f" (${act['cost']})" if act["cost"] > 0 else ""
        safe_addstr(win, sep_y + 1, ax, label + cost, curses.color_pair(ap) | curses.A_BOLD)
        ax += len(label + cost) + 3

    ax = 2
    for i, act in enumerate(actions_row2, start=3):
        is_sel = (i == dev_ui.action_sel)
        ap = PAIR_BUTTON_FOCUS if is_sel else PAIR_BUTTON
        label = f"[{act['key']}] {act['name']}"
        cost = f" (${act['cost']})" if act["cost"] > 0 else ""
        safe_addstr(win, sep_y + 2, ax, label + cost, curses.color_pair(ap) | curses.A_BOLD)
        ax += len(label + cost) + 3

    # Last action result
    if ds and ds.action_result:
        safe_addstr(win, sep_y + 3, 2, ds.action_result[:w - 4], curses.color_pair(PAIR_ACCENT))

    # Controls hint
    safe_addstr(win, h - 3, 2,
                "◄/►: select action  |  Enter: do action  |  Q: cycle QA  |  P: pause  |  L: launch  |  Esc: back",
                curses.color_pair(PAIR_MUTED))

    # ── Interruption overlay ──────────────────────────────────
    if ds and ds.pending_interruption:
        _draw_interruption_overlay(win, ds)


# ─────────────────────── HELPERS ──────────────────────────────


def _draw_stat_bar(win, y, x, label: str, value: int, bar_w: int, pair: int):
    safe_addstr(win, y,     x, f"{label:<7}", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y, x + 7, bar_w, value, pair, PAIR_MUTED)
    safe_addstr(win, y, x + 7 + bar_w + 1, f"{value:>3}", curses.color_pair(PAIR_ACCENT))


def _draw_interruption_overlay(win, ds):
    h, w = win.getmaxyx()
    evt = ds.pending_interruption
    choices = evt.get("choices", [])

    bw = min(54, w - 8)
    bh = 7 + len(choices)
    bx = (w - bw) // 2
    by = (h - bh) // 2

    # Fill background
    for row in range(by, by + bh):
        safe_addstr(win, row, bx, " " * bw, curses.color_pair(PAIR_OVERLAY))

    draw_box(win, by, bx, bh, bw, PAIR_DANGER, f"⚠️  {evt['title']}", PAIR_DANGER)

    body = evt.get("body", "")
    # Word-wrap body into bw-4 wide lines
    words = body.split()
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= bw - 4:
            line = (line + " " + word).strip()
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    for i, ln in enumerate(lines[:2]):
        safe_addstr(win, by + 2 + i, bx + 2, ln, curses.color_pair(PAIR_OVERLAY))

    for i, choice in enumerate(choices):
        is_sel = (i == ds.interruption_choice_idx)
        prefix = "▶ " if is_sel else "  "
        cp = PAIR_BUTTON_FOCUS if is_sel else PAIR_OVERLAY
        safe_addstr(win, by + 4 + i, bx + 2, f"{prefix}{choice['label']}"[:bw - 4],
                    curses.color_pair(cp) | (curses.A_BOLD if is_sel else 0))

    hint = "Up/Down: choose  |  Enter: confirm"
    safe_addstr(win, by + bh - 2, bx + 2, hint[:bw - 4], curses.color_pair(PAIR_MUTED))
