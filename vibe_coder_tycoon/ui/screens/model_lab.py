"""
Phase 10 — Model Lab UI

Two views:
  "list"  — browse player models, toggle licensing, retire
  "train" — axis sliders, name input, cost preview, confirm training
"""

import curses
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import (
    AI_MODEL_AXES, AXIS_POINT_BUDGET,
    AI_MODEL_TRAINING_COST_PER_POINT, AI_MODEL_TRAINING_DAYS_PER_POINT,
    AI_MODEL_TOKEN_COST_PER_POINT, MONTH_NAMES,
)
from ...models import GameState
from ...engine.systems.player_models import check_unlock, compute_capability


# ─────────────────────── STATE ─────────────────────────────────


@dataclass
class ModelLabUIState:
    view: str = "list"          # "list" | "train"
    selected: int = 0           # index into gs.player_models
    # train view
    axis_sel: int = 0           # which axis is highlighted (0–5)
    axis_points: list = field(default_factory=lambda: [0] * 6)
    model_name: str = ""
    name_input: bool = False    # True = typing name
    message: str = ""


# ─────────────────────── MAIN DRAW ────────────────────────────


def draw_model_lab(win, gs: GameState, ui: "ModelLabUIState"):
    if ui.view == "train":
        _draw_train_view(win, gs, ui)
    else:
        _draw_list_view(win, gs, ui)


# ─────────────────────── LIST VIEW ────────────────────────────


def _draw_list_view(win, gs: GameState, ui: ModelLabUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " MODEL LAB ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, 14, f"({len(gs.player_models)} models)",
                curses.color_pair(PAIR_MUTED))
    y += 2

    if not gs.player_models:
        safe_addstr(win, y, 4, "No player-built models yet. Press T to start training.",
                    curses.color_pair(PAIR_MUTED))
        y += 2

        # Show unlock status
        if gs.active_companies():
            c = gs.active_companies()[0]
            ok, reason = check_unlock(gs, c.id)
            if ok:
                safe_addstr(win, y, 4, "Unlock requirements: MET — press T to configure training.",
                            curses.color_pair(PAIR_BADGE_GREEN) | curses.A_BOLD)
            else:
                safe_addstr(win, y, 4, f"Unlock requirements not met: {reason}",
                            curses.color_pair(PAIR_DANGER))
    else:
        hline(win, y, 2, w - 4, PAIR_BORDER); y += 1
        header = f"  {'NAME':<20} {'STATUS':<12} {'CAP':>6} {'LIC':>5}  AXES"
        safe_addstr(win, y, 2, header, curses.color_pair(PAIR_MUTED) | curses.A_BOLD)
        y += 1
        hline(win, y, 2, w - 4, PAIR_BORDER); y += 1

        for i, m in enumerate(gs.player_models):
            if y >= h - 8:
                break
            is_sel = (i == ui.selected)
            rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
            status = m.training_status
            status_p = PAIR_BADGE_AMBER if status == "training" else PAIR_BADGE_GREEN
            lic = "ON " if m.licensed else "OFF"
            lic_p = PAIR_ACCENT if m.licensed else PAIR_MUTED
            days_left = f"({m.training_days_remaining}d)" if status == "training" else ""

            safe_addstr(win, y, 2, " " * (w - 4), curses.color_pair(rp))
            safe_addstr(win, y, 3,
                        f"  {m.name[:19]:<20}",
                        curses.color_pair(rp))
            safe_addstr(win, y, 25,
                        f"{status:<10}{days_left}",
                        curses.color_pair(status_p if not is_sel else rp) | curses.A_BOLD)
            safe_addstr(win, y, 37,
                        f"{m.capability_rating:>5.1f}",
                        curses.color_pair(rp if is_sel else PAIR_ACCENT))
            safe_addstr(win, y, 43,
                        f"{lic:>5}",
                        curses.color_pair(rp if is_sel else lic_p) | curses.A_BOLD)

            # Compact axis summary
            axes_str = "  ".join(
                f"{ax['name'][:3]}:{m.axes.get(ax['name'], 0)}"
                for ax in AI_MODEL_AXES
            )
            safe_addstr(win, y, 50, axes_str[:w - 52], curses.color_pair(rp if is_sel else PAIR_MUTED))
            y += 1

        # Detail panel for selected model
        if gs.player_models and 0 <= ui.selected < len(gs.player_models):
            m = gs.player_models[ui.selected]
            y += 1
            hline(win, y, 2, w - 4, PAIR_BORDER); y += 1
            safe_addstr(win, y, 4, f"Selected: {m.name} v{m.version}",
                        curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
            safe_addstr(win, y, 4 + len(m.name) + 15,
                        f"Cap {m.capability_rating}/10",
                        curses.color_pair(PAIR_ACCENT))
            y += 1
            for ax in AI_MODEL_AXES:
                pts = m.axes.get(ax["name"], 0)
                bar = "█" * pts + "░" * (AXIS_POINT_BUDGET // len(AI_MODEL_AXES) - pts)
                safe_addstr(win, y, 6,
                            f"{ax['name']:<12} {pts:>2}pt  {bar[:10]}  {ax['desc']}",
                            curses.color_pair(PAIR_MUTED))
                y += 1
                if y >= h - 5:
                    break

    safe_addstr(win, h - 4, 2,
                "↑↓:select  L:toggle licensing  T:train new model  R:retire  Esc:back to Market",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


# ─────────────────────── TRAIN VIEW ───────────────────────────


def _draw_train_view(win, gs: GameState, ui: ModelLabUIState):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " TRAIN NEW MODEL ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    total_pts = sum(ui.axis_points)
    remaining = AXIS_POINT_BUDGET - total_pts
    budget_p = PAIR_DANGER if remaining < 0 else PAIR_ACCENT
    safe_addstr(win, y, 4,
                f"Point Budget: {total_pts}/{AXIS_POINT_BUDGET}  "
                f"Remaining: {remaining}",
                curses.color_pair(budget_p) | curses.A_BOLD)
    y += 2

    # Axis sliders
    safe_addstr(win, y, 4, "AXIS SLIDERS  (↑↓ select, ◄/► adjust)",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 4, w // 2, PAIR_BORDER); y += 1

    for i, ax in enumerate(AI_MODEL_AXES):
        is_sel = (i == ui.axis_sel) and not ui.name_input
        pts = ui.axis_points[i]
        bar = "█" * pts + "░" * (AXIS_POINT_BUDGET - pts)
        cp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        safe_addstr(win, y, 4, " " * (w // 2 - 5), curses.color_pair(cp))
        safe_addstr(win, y, 4,
                    f"{prefix}{ax['name']:<12} {pts:>2}pt  {bar[:20]}  {ax['desc'][:20]}",
                    curses.color_pair(cp if is_sel else PAIR_MUTED))
        y += 1

    y += 1

    # Name input
    name_focus = ui.name_input
    name_cp = PAIR_INPUT_FOCUS if name_focus else PAIR_INPUT_IDLE
    name_prefix = "▶ " if name_focus else "  "
    safe_addstr(win, y, 4, f"{name_prefix}Model Name : ",
                curses.color_pair(PAIR_ACCENT if name_focus else PAIR_MUTED) | curses.A_BOLD)
    safe_addstr(win, y, 18,
                f" {ui.model_name:<20} {'█' if name_focus else ''}",
                curses.color_pair(name_cp) | curses.A_BOLD)
    y += 2

    # Cost preview
    cost = AI_MODEL_TRAINING_COST_PER_POINT * total_pts
    token_cost = AI_MODEL_TOKEN_COST_PER_POINT * total_pts
    days = AI_MODEL_TRAINING_DAYS_PER_POINT * total_pts
    axes_dict = {AI_MODEL_AXES[i]["name"]: ui.axis_points[i] for i in range(len(AI_MODEL_AXES))}
    cap = compute_capability(axes_dict) if total_pts > 0 else 0.0

    safe_addstr(win, y, 4, "TRAINING PREVIEW",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 4, 40, PAIR_BORDER); y += 1
    safe_addstr(win, y, 6, f"Cash cost  : ${cost:,}", curses.color_pair(PAIR_MUTED)); y += 1
    safe_addstr(win, y, 6, f"Token cost : {token_cost:,}K tokens", curses.color_pair(PAIR_MUTED)); y += 1
    safe_addstr(win, y, 6, f"Duration   : {days} days (~{days // 30} months)", curses.color_pair(PAIR_MUTED)); y += 1
    safe_addstr(win, y, 6, f"Cap rating : {cap:.2f}/10",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD); y += 2

    # Unlock check
    if gs.active_companies():
        c = gs.active_companies()[0]
        ok, reason = check_unlock(gs, c.id)
        if not ok:
            safe_addstr(win, y, 4, f"LOCKED: {reason}", curses.color_pair(PAIR_DANGER))
            y += 1

    safe_addstr(win, h - 4, 2,
                "↑↓:select axis  ◄/►:adjust points  n:name input  Enter:start training  Esc:back",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)
