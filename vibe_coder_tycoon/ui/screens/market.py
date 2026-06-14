import curses
from dataclasses import dataclass

from ..colors import *
from ..helpers import *
from ...constants import MONTH_NAMES, SUBSCRIPTION_TIERS, IDE_CATALOG
from ...models import GameState
from ...engine.systems.models_ai import (
    available_models, available_ides, get_subscription, get_ide, era_blurb,
)
from ...engine.systems.stocks import (
    net_worth, public_equity_value, ipo_eligibility, ipo_bank_cost,
    pricing_demand_factor,
)


# ─────────────────────── MARKET TAB ───────────────────────────

@dataclass
class MarketUIState:
    model_sel: int = 0      # selection index into the available-models list
    model_scroll: int = 0
    view: str = "market"    # "market" | "model_lab" | "stocks" | "ipo"
    # Phase 12 — stock view / IPO launcher
    stock_company_sel: int = 0
    ipo_field: int = 0      # 0 = price, 1 = shares
    ipo_price: str = ""
    ipo_shares: str = ""
    message: str = ""


def _sparkline(history: list, width: int = 24) -> str:
    """Render a compact unicode sparkline from a price history list."""
    blocks = "▁▂▃▄▅▆▇█"
    if not history:
        return ""
    pts = history[-width:]
    lo, hi = min(pts), max(pts)
    span = hi - lo
    if span <= 0:
        return blocks[0] * len(pts)
    out = []
    for v in pts:
        idx = int((v - lo) / span * (len(blocks) - 1))
        out.append(blocks[idx])
    return "".join(out)


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
                "Up/Down: browse models  |  Enter: set default  |  S: subscription  |  I: IDE  |  L: Model Lab  |  T: Stock Exchange",
                curses.color_pair(PAIR_MUTED))


# ─────────────────────── STOCK EXCHANGE VIEW ──────────────────


def draw_stocks(win, gs: GameState, ui: "MarketUIState"):
    h, w = win.getmaxyx()
    mid = int(w * 0.52)
    lw = mid - 3

    mk = gs.market or {}
    index_val = mk.get("index", 0.0)
    index_hist = mk.get("index_history", [])

    # ── Header: net worth + index ──────────────────────────────
    safe_addstr(win, 3, 2, " 📈 STOCK EXCHANGE ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, 3, 22, f"{MONTH_NAMES[gs.month - 1]} {gs.year}",
                curses.color_pair(PAIR_MUTED))

    nw = net_worth(gs)
    eq = public_equity_value(gs)
    progress = min(1.0, nw / 1_000_000_000_000)
    safe_addstr(win, 4, 2, f"💎 NET WORTH: {fmt_money_short(nw)}",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    safe_addstr(win, 4, 34, f"(public equity {fmt_money_short(eq)})",
                curses.color_pair(PAIR_MUTED))
    safe_addstr(win, 5, 2,
                f"🏆 Trillionaire progress: {progress * 100:.4f}%  toward $1T",
                curses.color_pair(PAIR_WARN))

    # ── Left: parody index + parody companies ──────────────────
    y = 7
    delta = ""
    if len(index_hist) >= 2:
        d = index_hist[-1] - index_hist[-2]
        arrow = "▲" if d >= 0 else "▼"
        delta = f"  {arrow} {abs(d):.1f}"
    safe_addstr(win, y, 2, f"VIBE-100 INDEX: {index_val:,.1f}{delta}",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 4, _sparkline(index_hist, lw - 6),
                curses.color_pair(PAIR_ACCENT)); y += 1
    hline(win, y, 2, lw, PAIR_BORDER); y += 1

    safe_addstr(win, y, 4, f"  {'TICKER':<7}{'COMPANY':<16}{'PRICE':>9} {'TREND':>10}",
                curses.color_pair(PAIR_MUTED) | curses.A_BOLD); y += 1
    for comp in mk.get("companies", []):
        if y >= h - 3:
            break
        hist = comp.get("history", [])
        chg_pair = PAIR_ACCENT
        if len(hist) >= 2 and hist[-1] < hist[-2]:
            chg_pair = PAIR_DANGER
        safe_addstr(win, y, 4,
                    f"  {comp['ticker']:<7}{comp['name'][:15]:<16}"
                    f"${comp['price']:>8,.2f}",
                    curses.color_pair(PAIR_PANEL))
        safe_addstr(win, y, 4 + 7 + 16 + 9 + 2, _sparkline(hist, 8),
                    curses.color_pair(chg_pair))
        y += 1

    # ── Right: player's companies / IPO status ─────────────────
    rx = mid + 2
    rw = w - mid - 4
    ry = 7
    safe_addstr(win, ry, rx, "YOUR COMPANIES",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); ry += 1
    hline(win, ry, rx, rw - 1, PAIR_BORDER); ry += 1

    for c in gs.active_companies():
        if ry >= h - 4:
            break
        if c.is_public:
            safe_addstr(win, ry, rx, f"🔔 {c.name[:rw - 4]}",
                        curses.color_pair(PAIR_BADGE_GREEN) | curses.A_BOLD); ry += 1
            mcap = c.share_price * c.shares_outstanding
            stake = mcap * c.player_equity_pct
            safe_addstr(win, ry, rx + 2,
                        f"${c.share_price:,.2f}/sh  cap {fmt_money_short(mcap)}",
                        curses.color_pair(PAIR_ACCENT)); ry += 1
            safe_addstr(win, ry, rx + 2,
                        f"your {c.player_equity_pct:.0%} = {fmt_money_short(stake)}",
                        curses.color_pair(PAIR_MUTED)); ry += 1
            safe_addstr(win, ry, rx + 2, _sparkline(c.share_price_history, rw - 4),
                        curses.color_pair(PAIR_ACCENT)); ry += 1
        else:
            ok, reason = ipo_eligibility(gs, c.id)
            tag = "✅ IPO-ready" if ok else ("⏳ in pricing" if c.ipo_stage == "Pricing" else "🔒 private")
            tp = PAIR_BADGE_GREEN if ok else PAIR_MUTED
            safe_addstr(win, ry, rx, f"{c.name[:rw - 14]}",
                        curses.color_pair(PAIR_PANEL) | curses.A_BOLD)
            safe_addstr(win, ry, rx + rw - 13, tag, curses.color_pair(tp)); ry += 1
            safe_addstr(win, ry, rx + 2,
                        f"MRR streak {c.positive_mrr_streak}mo  {c.legal_style[:18]}",
                        curses.color_pair(PAIR_MUTED)); ry += 1
            if not ok and c.ipo_stage != "Pricing":
                safe_addstr(win, ry, rx + 2, reason[:rw - 4],
                            curses.color_pair(PAIR_MUTED) | curses.A_DIM); ry += 1
        ry += 1

    if ui.message:
        mp = PAIR_ACCENT if ("✓" in ui.message or "🎉" in ui.message) else PAIR_DANGER
        safe_addstr(win, h - 4, 2, ui.message[:w - 4],
                    curses.color_pair(mp) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2,
                "P: launch/manage IPO  |  Esc/T: back to tools",
                curses.color_pair(PAIR_MUTED))


# ─────────────────────── IPO LAUNCHER VIEW ────────────────────


def _ipo_companies(gs: GameState) -> list:
    """Companies that can start or are mid-IPO."""
    out = []
    for c in gs.active_companies():
        if c.is_public:
            continue
        ok, _ = ipo_eligibility(gs, c.id)
        if ok or c.ipo_stage == "Pricing":
            out.append(c)
    return out


def draw_ipo(win, gs: GameState, ui: "MarketUIState"):
    h, w = win.getmaxyx()
    y = 3
    safe_addstr(win, y, 2, " 🔔 IPO LAUNCHER ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 2

    companies = _ipo_companies(gs)
    if not companies:
        safe_addstr(win, y, 4,
                    "No companies eligible for IPO yet.",
                    curses.color_pair(PAIR_DANGER)); y += 1
        safe_addstr(win, y, 4,
                    "Requires a C-Corporation with 12 consecutive months of positive MRR.",
                    curses.color_pair(PAIR_MUTED)); y += 1
        safe_addstr(win, h - 3, 2, "Esc: back", curses.color_pair(PAIR_MUTED))
        return

    ui.stock_company_sel = max(0, min(ui.stock_company_sel, len(companies) - 1))
    safe_addstr(win, y, 4, "SELECT COMPANY  (↑↓)",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
    hline(win, y, 4, w // 2, PAIR_BORDER); y += 1
    for i, c in enumerate(companies):
        is_sel = (i == ui.stock_company_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        stage = "(pricing)" if c.ipo_stage == "Pricing" else "(ready)"
        safe_addstr(win, y, 4, " " * (w // 2 - 5), curses.color_pair(rp))
        safe_addstr(win, y, 4, f"{prefix}{c.name[:30]}  {stage}",
                    curses.color_pair(rp))
        y += 1

    y += 1
    c = companies[ui.stock_company_sel]

    if c.ipo_stage != "Pricing":
        # Stage 1: Preparation
        cost = ipo_bank_cost(c)
        safe_addstr(win, y, 4, "STAGE 1 — PREPARATION",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
        safe_addstr(win, y, 6,
                    f"Hiring an investment bank costs ${cost:,} (4% of valuation).",
                    curses.color_pair(PAIR_MUTED)); y += 1
        safe_addstr(win, y, 6,
                    "Triggers due diligence — may surface issues. Press Enter to proceed.",
                    curses.color_pair(PAIR_MUTED)); y += 2
        safe_addstr(win, y, 6, "[ Enter ] Hire bank & begin IPO",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD); y += 1
    else:
        # Stage 2: Pricing
        demand = pricing_demand_factor(gs, c)
        safe_addstr(win, y, 4, "STAGE 2 — PRICING",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
        safe_addstr(win, y, 6,
                    f"Market demand factor: ×{demand:.2f} "
                    f"(driven by reputation {gs.founder.reputation} & revenue ${c.monthly_revenue:,}/mo)",
                    curses.color_pair(PAIR_MUTED)); y += 2

        pf = curses.color_pair(PAIR_INPUT_FOCUS if ui.ipo_field == 0 else PAIR_INPUT_IDLE) | curses.A_BOLD
        sf = curses.color_pair(PAIR_INPUT_FOCUS if ui.ipo_field == 1 else PAIR_INPUT_IDLE) | curses.A_BOLD
        cur0 = "█" if ui.ipo_field == 0 else ""
        cur1 = "█" if ui.ipo_field == 1 else ""
        safe_addstr(win, y, 6, f"Share price ($): {ui.ipo_price}{cur0}", pf); y += 1
        safe_addstr(win, y, 6, f"Shares issued  : {ui.ipo_shares}{cur1}", sf); y += 2

        try:
            price = float(ui.ipo_price or "0")
            shares = int(ui.ipo_shares or "0")
        except ValueError:
            price, shares = 0.0, 0
        if price > 0 and shares > 0:
            from ...constants import IPO_PUBLIC_FLOAT_PCT
            opening = price * demand
            proceeds = int(opening * shares * IPO_PUBLIC_FLOAT_PCT)
            safe_addstr(win, y, 6,
                        f"Opening ~${opening:,.2f}/sh  →  raise ~{fmt_money_short(proceeds)} "
                        f"({IPO_PUBLIC_FLOAT_PCT:.0%} float). You keep {1 - IPO_PUBLIC_FLOAT_PCT:.0%}.",
                        curses.color_pair(PAIR_ACCENT) | curses.A_BOLD); y += 1
        safe_addstr(win, y + 1, 6, "[ Enter ] Price & go public",
                    curses.color_pair(PAIR_BUTTON_FOCUS) | curses.A_BOLD)

    if ui.message:
        mp = PAIR_ACCENT if ("✓" in ui.message or "🎉" in ui.message) else PAIR_DANGER
        safe_addstr(win, h - 4, 2, ui.message[:w - 4],
                    curses.color_pair(mp) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2,
                "↑↓:company  Tab:switch field  Type values  Enter:confirm  Esc:back",
                curses.color_pair(PAIR_MUTED))
