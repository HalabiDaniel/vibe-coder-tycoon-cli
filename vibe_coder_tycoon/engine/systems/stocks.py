"""
Phase 12 — Stock Market, IPO, Net Worth

The exchange hosts a set of parody public companies (market context only — the
player cannot buy them) plus any of the player's own companies that have gone
public via IPO. A parody index tracks the broad market.

IPO pipeline (per company):
    private ("")  --prepare_ipo-->  "Pricing"  --price_ipo-->  "Trading" (public)

Daily price movement is simulated in batches inside the monthly tick: each
public company and the index take ~21 small random-walk steps biased by a
deterministic performance drift. Net worth aggregates personal cash, company
balances, and the market value of the founder's retained public equity — the
trillionaire victory metric.
"""

import random

from ...constants import (
    MONTH_NAMES,
    PARODY_PUBLIC_COMPANIES,
    IPO_MIN_POSITIVE_MRR_MONTHS,
    IPO_BANK_COST_PCT,
    IPO_BANK_COST_MIN,
    IPO_PUBLIC_FLOAT_PCT,
    IPO_DUE_DILIGENCE_CHANCE,
)
from ...models import GameState
from ..actions import register, ActionResult
from .finance import adjust_reputation

_TRADING_DAYS = 21          # simulated price steps per month
_HISTORY_CAP = 90           # retained price points per company / index


# ─────────────────────── MARKET SETUP ─────────────────────────


def init_market(gs: GameState) -> None:
    """Seed the parody market snapshot. Idempotent — no-op if already present."""
    if gs.market:
        return
    companies = []
    for spec in PARODY_PUBLIC_COMPANIES:
        companies.append({
            "name":     spec["name"],
            "ticker":   spec["ticker"],
            "price":    float(spec["base_price"]),
            "drift":    spec["drift"],
            "volatility": spec["volatility"],
            "founder":  spec["founder"],
            "history":  [float(spec["base_price"])],
        })
    gs.market = {
        "index": 1000.0,
        "index_history": [1000.0],
        "companies": companies,
    }


# ─────────────────────── NET WORTH ────────────────────────────


def public_equity_value(gs: GameState) -> float:
    """Market value of the founder's retained equity across public companies."""
    total = 0.0
    for c in gs.companies:
        if c.active and c.is_public:
            total += c.share_price * c.shares_outstanding * c.player_equity_pct
    return total


def net_worth(gs: GameState) -> float:
    """personal_cash + Σ company balances + Σ public equity value."""
    personal = gs.founder.personal_cash if gs.founder else 0.0
    company_cash = sum(c.cash for c in gs.companies if c.active)
    return float(personal) + float(company_cash) + public_equity_value(gs)


# ─────────────────────── IPO ELIGIBILITY ──────────────────────


def ipo_bank_cost(c) -> int:
    """Investment-bank fee for taking a company public."""
    return max(IPO_BANK_COST_MIN, int(c.valuation * IPO_BANK_COST_PCT))


def ipo_eligibility(gs: GameState, company_id: int) -> tuple[bool, str]:
    """Return (eligible, reason). reason explains the first failing gate."""
    c = gs.company_by_id(company_id)
    if c is None or not c.active:
        return False, "Company not found."
    if c.is_public:
        return False, "Already public."
    if c.ipo_stage == "Pricing":
        return False, "IPO already in progress — set a price."
    if c.legal_style != "C-Corporation":
        return False, "Must be a C-Corporation to IPO."
    if c.positive_mrr_streak < IPO_MIN_POSITIVE_MRR_MONTHS:
        return (False,
                f"Needs {IPO_MIN_POSITIVE_MRR_MONTHS} consecutive months of positive MRR "
                f"({c.positive_mrr_streak} so far).")
    cost = ipo_bank_cost(c)
    if c.cash < cost:
        return False, f"Cannot afford investment bank fee (${cost:,})."
    return True, "Eligible for IPO."


def pricing_demand_factor(gs: GameState, c) -> float:
    """How the market adjusts the founder's set price (0.5–1.5)."""
    rep_factor = (gs.founder.reputation - 50) / 50.0 * 0.4     # ±0.4
    rev_factor = min(0.4, c.monthly_revenue / 100_000 * 0.4)   # 0–0.4
    return max(0.5, min(1.5, 1.0 + rep_factor + rev_factor))


# ─────────────────────── PRICE MOVEMENT ───────────────────────


def performance_drift(gs: GameState, c) -> float:
    """Deterministic monthly drift fraction from reputation + revenue level."""
    rep_factor = (c.reputation - 50) / 50.0 * 0.04             # ±0.04
    rev_factor = min(0.05, c.monthly_revenue / 50_000 * 0.05)  # 0–0.05
    return rep_factor + rev_factor


def apply_price_shock(c, pct: float) -> None:
    """Immediately move a public company's share price by `pct` (e.g. +0.05)."""
    if not c.is_public or c.share_price <= 0:
        return
    c.share_price = max(0.01, round(c.share_price * (1 + pct), 2))
    c.share_price_history.append(c.share_price)
    c.share_price_history = c.share_price_history[-_HISTORY_CAP:]


def _walk(price: float, daily_drift: float, volatility: float) -> float:
    step = daily_drift + random.gauss(0, volatility)
    return max(0.01, price * (1 + step))


def _tick_parody_market(gs: GameState) -> None:
    mk = gs.market
    if not mk:
        return
    index_total = 0.0
    for comp in mk["companies"]:
        for _ in range(_TRADING_DAYS):
            comp["price"] = round(
                _walk(comp["price"], comp["drift"] / _TRADING_DAYS, comp["volatility"]), 2
            )
        comp["history"].append(comp["price"])
        comp["history"] = comp["history"][-_HISTORY_CAP:]
        index_total += comp["price"]
    # Index = scaled average of parody company prices
    avg = index_total / max(1, len(mk["companies"]))
    mk["index"] = round(avg * 4.0, 2)
    mk["index_history"].append(mk["index"])
    mk["index_history"] = mk["index_history"][-_HISTORY_CAP:]


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_stocks_tick(gs: GameState) -> list:
    """Update MRR streaks, move parody + player share prices, fire pressure events."""
    init_market(gs)
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    # Track positive-MRR streaks for IPO eligibility
    for c in gs.active_companies():
        if c.monthly_revenue > 0:
            c.positive_mrr_streak += 1
        else:
            c.positive_mrr_streak = 0

    # Move the parody market / index
    _tick_parody_market(gs)

    # Move the player's public companies
    for c in gs.active_companies():
        if not c.is_public or c.share_price <= 0:
            continue
        drift = performance_drift(gs, c)
        vol = 0.02
        for _ in range(_TRADING_DAYS):
            c.share_price = round(_walk(c.share_price, drift / _TRADING_DAYS, vol), 2)
        c.share_price_history.append(c.share_price)
        c.share_price_history = c.share_price_history[-_HISTORY_CAP:]

        # Shareholder pressure on a bad month
        if c.months_negative >= 1 and random.random() < 0.5:
            apply_price_shock(c, -0.08)
            adjust_reputation(gs, -2)
            events.append((
                "📉",
                f"Shareholder pressure on {c.name}! Bad quarter drags the stock down.",
                "bad", date_str,
            ))

    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("prepare_ipo")
def _prepare_ipo(gs: GameState, company_id: int) -> ActionResult:
    eligible, reason = ipo_eligibility(gs, company_id)
    if not eligible:
        return ActionResult(ok=False, message=reason)
    c = gs.company_by_id(company_id)
    cost = ipo_bank_cost(c)
    c.cash -= cost
    c.ipo_stage = "Pricing"
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    msg = (f"Investment bank hired for ${cost:,}. Due diligence underway — "
           f"set your share price next.")
    # Due-diligence event may surface an issue
    if random.random() < IPO_DUE_DILIGENCE_CHANCE:
        penalty = max(1, int(cost * 0.25))
        c.cash = max(0, c.cash - penalty)
        adjust_reputation(gs, -3)
        events.append((
            "🔍",
            f"Due diligence on {c.name} flagged issues! -3 rep, ${penalty:,} cleanup.",
            "warn", date_str,
        ))
        msg += " (Due diligence surfaced some issues.)"
    return ActionResult(ok=True, message=msg, events=events)


@register("price_ipo")
def _price_ipo(
    gs: GameState, company_id: int, price: float, shares: int
) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if c.ipo_stage != "Pricing":
        return ActionResult(ok=False, message="Run IPO preparation first.")
    if price <= 0:
        return ActionResult(ok=False, message="Share price must be positive.")
    if shares <= 0:
        return ActionResult(ok=False, message="Shares outstanding must be positive.")

    demand = pricing_demand_factor(gs, c)
    opening = max(0.01, round(price * demand, 2))
    float_shares = int(shares * IPO_PUBLIC_FLOAT_PCT)
    proceeds = int(opening * float_shares)

    c.is_public = True
    c.ipo_stage = "Trading"
    c.legal_style = "Public Company"
    c.share_price = opening
    c.shares_outstanding = shares
    c.player_equity_pct = round(1.0 - IPO_PUBLIC_FLOAT_PCT, 4)
    c.share_price_history = [opening]
    c.cash += proceeds
    adjust_reputation(gs, 10)

    if "First company IPO" not in gs.founder.achievements:
        gs.founder.achievements.append("First company IPO")

    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    events = [(
        "🔔",
        (f"{c.name} IPO'd at ${opening:,.2f}/share! Raised ${proceeds:,} "
         f"selling {IPO_PUBLIC_FLOAT_PCT:.0%} float."),
        "good", date_str,
    )]
    return ActionResult(
        ok=True,
        message=(
            f"🎉 {c.name} is PUBLIC! Opened at ${opening:,.2f} "
            f"(you set ${price:,.2f}, demand ×{demand:.2f}). "
            f"Raised ${proceeds:,}. +10 rep."
        ),
        events=events,
    )
