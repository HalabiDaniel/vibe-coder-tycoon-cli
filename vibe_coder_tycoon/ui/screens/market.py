import curses
from dataclasses import dataclass

from ..colors import *
from ..helpers import *
from ...constants import MONTH_NAMES, SUBSCRIPTION_TIERS, IDE_CATALOG
from ...models import GameState
from ...engine.systems.models_ai import (
    available_models, available_ides, get_subscription, get_ide, era_blurb,
)


# ─────────────────────── MARKET TAB ───────────────────────────

@dataclass
class MarketUIState:
    model_sel: int = 0      # selection index into the available-models list
    model_scroll: int = 0


def draw_market(win, gs: GameState, ui: "MarketUIState"):
    h, w = win.getmaxyx()
    mid = int(w * 0.58)
    lw = mid - 3

    # ── Header: era banner ─────────────────────────────────────
    month = MONTH_NAMES[gs.month - 1]
    safe_addstr(win, 3, 2, " MARKET & TECH ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, 3, 18, f"{month} {gs.year}", curses.color_pair(PAIR_MUTED))
    safe_addstr(win, 4, 2, f"🌅 {gs.current_era}",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    safe_addstr(win, 4, 4 + len(gs.current_era) + 3, era_blurb(gs.current_era)[:w - mid],
                curses.color_pair(PAIR_MUTED) | curses.A_DIM)

    # ── Left: your tools + available model browser ─────────────
    y = 6
    sub = get_subscription(gs.subscription_tier)
    ide = get_ide(gs.active_ide)
    mcost = sub["monthly"] if sub else 0
    mcost_label = f"${mcost}/mo" + (" + per-token" if sub and sub["per_token"] else "")

    safe_addstr(win, y, 2, "YOUR TOOLS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER); y += 1
    safe_addstr(win, y, 4, f"Subscription : {gs.subscription_tier}  ({mcost_label})",
                curses.color_pair(PAIR_ACCENT)); y += 1
    safe_addstr(win, y, 4, f"Active IDE   : {gs.active_ide}"
                + (f"  +{int((ide['dev_speed_mult']-1)*100)}% dev" if ide else ""),
                curses.color_pair(PAIR_ACCENT)); y += 1
    safe_addstr(win, y, 4, f"Default Model: {gs.active_model or '—'}",
                curses.color_pair(PAIR_ACCENT)); y += 2

    models = available_models(gs)
    safe_addstr(win, y, 2, f"AVAILABLE AI MODELS ({len(models)} unlocked, year ≤ {gs.year})",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 4, f"  {'MODEL':<24}{'CO':<14}{'YR':>4} {'SCORE':>6} {'$/1M':>7}",
                curses.color_pair(PAIR_MUTED) | curses.A_BOLD)
    y += 1
    hline(win, y, 2, lw, PAIR_BORDER); y += 1

    list_h = max(3, h - y - 4)
    if ui.model_sel < ui.model_scroll:
        ui.model_scroll = ui.model_sel
    elif ui.model_sel >= ui.model_scroll + list_h:
        ui.model_scroll = ui.model_sel - list_h + 1
    visible = models[ui.model_scroll:ui.model_scroll + list_h]
    for i, m in enumerate(visible):
        real_idx = ui.model_scroll + i
        is_sel = (real_idx == ui.model_sel)
        is_active = (m["name"] == gs.active_model)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        sp = PAIR_BADGE_GREEN if m["score"] >= 8 else PAIR_ACCENT if m["score"] >= 6 else PAIR_MUTED
        cost = f"${m['out_cost']:.0f}" if m["out_cost"] else "open"
        mark = "►" if is_active else " "
        safe_addstr(win, y, 2, " " * lw, curses.color_pair(rp))
        safe_addstr(win, y, 3,
                    f"{mark} {m['name'][:23]:<24}{m['company'][:13]:<14}{m['year']:>4} "
                    f"{m['score']:>5.1f} {cost:>7}",
                    curses.color_pair(rp if is_sel else sp))
        y += 1

    # ── Right: subscription tiers + IDEs ───────────────────────
    rx = mid + 2
    rw = w - mid - 4
    ry = 6

    safe_addstr(win, ry, rx, "SUBSCRIPTION TIERS  [S: cycle]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw - 1, PAIR_BORDER); ry += 1
    for s in SUBSCRIPTION_TIERS:
        is_cur = (s["name"] == gs.subscription_tier)
        cp = PAIR_BADGE_GREEN if is_cur else PAIR_MUTED
        cost = f"${s['monthly']}/mo" if not s["per_token"] else f"${s['per_token']:.2f}/Ktok"
        cur = " ← ACTIVE" if is_cur else ""
        safe_addstr(win, ry, rx + 1, f"{s['name']:<12}{cost:<12}{cur}",
                    curses.color_pair(cp) | (curses.A_BOLD if is_cur else 0))
        safe_addstr(win, ry + 1, rx + 3, s["desc"][:rw - 5],
                    curses.color_pair(PAIR_MUTED) | curses.A_DIM)
        ry += 2

    ry += 1
    safe_addstr(win, ry, rx, "IDEs  [I: cycle unlocked]",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    hline(win, ry, rx, rw - 1, PAIR_BORDER); ry += 1
    avail = {i["name"] for i in available_ides(gs)}
    for ide_d in IDE_CATALOG:
        unlocked = ide_d["name"] in avail
        is_cur = (ide_d["name"] == gs.active_ide)
        if is_cur:
            cp = PAIR_BADGE_GREEN
        elif unlocked:
            cp = PAIR_MUTED
        else:
            cp = PAIR_MUTED
        lock = "" if unlocked else f"  🔒{ide_d['year']}"
        cur = " ←" if is_cur else ""
        boost = f"+{int((ide_d['dev_speed_mult']-1)*100)}% dev"
        line = f"{ide_d['name']:<18}{boost:<10}{lock}{cur}"
        attr = curses.color_pair(cp) | (curses.A_BOLD if is_cur else
                                        (0 if unlocked else curses.A_DIM))
        safe_addstr(win, ry, rx + 1, line[:rw - 2], attr)
        ry += 1
        if ry >= h - 4:
            break

    safe_addstr(win, h - 3, 2,
                "Up/Down: browse models  |  Enter: set default model  |  S: subscription  |  I: IDE",
                curses.color_pair(PAIR_MUTED))
