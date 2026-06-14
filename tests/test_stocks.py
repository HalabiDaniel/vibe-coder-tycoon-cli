"""
Phase 12 — Stock Market, IPO, Net Worth tests.

Covers: net-worth math, IPO eligibility gates, pricing demand adjustment,
the IPO pipeline actions, price-movement drivers, parody market tick,
shareholder pressure, launch price reaction, and persistence round-trip.
"""

import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.models import Founder
from vibe_coder_tycoon.engine.systems import stocks
from vibe_coder_tycoon.constants import (
    IPO_MIN_POSITIVE_MRR_MONTHS, IPO_PUBLIC_FLOAT_PCT, TRILLIONAIRE_THRESHOLD,
)
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(reputation=60, year=2028):
    f = Founder(username="Tester", background_idx=0, reputation=reputation,
                burnout=0, skill_prototyping=50, skill_sales=30,
                skill_tech=40, skill_management=30, total_tokens_used=0)
    gs = make_new_game(f, 3)
    gs.year = year
    return gs


def _make_ipo_ready(gs, company_id=0):
    c = gs.company_by_id(company_id)
    c.legal_style = "C-Corporation"
    c.positive_mrr_streak = IPO_MIN_POSITIVE_MRR_MONTHS
    c.monthly_revenue = 20_000
    c.cash = 500_000
    c.valuation = 1_000_000
    return c


# ─────────────────────── NET WORTH ────────────────────────────

def test_net_worth_basic():
    gs = _gs()
    gs.founder.personal_cash = 1000.0
    gs.companies[0].cash = 5000
    assert stocks.net_worth(gs) == 6000.0


def test_net_worth_includes_public_equity():
    gs = _gs()
    gs.founder.personal_cash = 0.0
    c = gs.companies[0]
    c.cash = 0
    c.is_public = True
    c.share_price = 100.0
    c.shares_outstanding = 1_000_000
    c.player_equity_pct = 0.8
    # equity value = 100 * 1,000,000 * 0.8 = 80,000,000
    assert stocks.net_worth(gs) == 80_000_000.0


def test_public_equity_value_zero_when_private():
    gs = _gs()
    c = gs.companies[0]
    c.share_price = 100.0
    c.shares_outstanding = 1000
    assert stocks.public_equity_value(gs) == 0.0


# ─────────────────────── IPO ELIGIBILITY ──────────────────────

def test_ipo_requires_c_corp():
    gs = _gs()
    c = gs.companies[0]
    c.legal_style = "LLC"
    c.positive_mrr_streak = 24
    ok, reason = stocks.ipo_eligibility(gs, 0)
    assert not ok
    assert "C-Corp" in reason


def test_ipo_requires_mrr_streak():
    gs = _gs()
    c = gs.companies[0]
    c.legal_style = "C-Corporation"
    c.positive_mrr_streak = 3
    c.cash = 500_000
    ok, reason = stocks.ipo_eligibility(gs, 0)
    assert not ok
    assert "positive MRR" in reason


def test_ipo_requires_bank_fee_affordable():
    gs = _gs()
    c = _make_ipo_ready(gs)
    c.cash = 100   # can't afford the fee
    ok, reason = stocks.ipo_eligibility(gs, 0)
    assert not ok
    assert "afford" in reason.lower()


def test_ipo_eligible_when_all_met():
    gs = _gs()
    _make_ipo_ready(gs)
    ok, reason = stocks.ipo_eligibility(gs, 0)
    assert ok, reason


# ─────────────────────── PRICING ADJUSTMENT ───────────────────

def test_pricing_demand_higher_with_reputation():
    gs_lo = _gs(reputation=20)
    gs_hi = _gs(reputation=90)
    c_lo = _make_ipo_ready(gs_lo)
    c_hi = _make_ipo_ready(gs_hi)
    assert stocks.pricing_demand_factor(gs_hi, c_hi) > stocks.pricing_demand_factor(gs_lo, c_lo)


def test_pricing_demand_clamped():
    gs = _gs(reputation=100)
    c = _make_ipo_ready(gs)
    c.monthly_revenue = 10_000_000
    assert stocks.pricing_demand_factor(gs, c) <= 1.5


# ─────────────────────── IPO PIPELINE ─────────────────────────

def test_prepare_ipo_charges_bank_and_advances_stage():
    gs = _gs()
    c = _make_ipo_ready(gs)
    cash_before = c.cash
    result = dispatch(gs, "prepare_ipo", company_id=0)
    assert result.ok, result.message
    assert c.ipo_stage == "Pricing"
    assert c.cash < cash_before   # bank fee charged


def test_prepare_ipo_rejected_when_ineligible():
    gs = _gs()
    gs.companies[0].legal_style = "LLC"
    result = dispatch(gs, "prepare_ipo", company_id=0)
    assert not result.ok


def test_price_ipo_makes_company_public():
    gs = _gs()
    c = _make_ipo_ready(gs)
    dispatch(gs, "prepare_ipo", company_id=0)
    cash_before = c.cash
    result = dispatch(gs, "price_ipo", company_id=0, price=50.0, shares=1_000_000)
    assert result.ok, result.message
    assert c.is_public
    assert c.legal_style == "Public Company"
    assert c.ipo_stage == "Trading"
    assert c.share_price > 0
    assert c.shares_outstanding == 1_000_000
    assert c.player_equity_pct == round(1.0 - IPO_PUBLIC_FLOAT_PCT, 4)
    assert c.cash > cash_before   # IPO proceeds deposited


def test_price_ipo_requires_preparation():
    gs = _gs()
    _make_ipo_ready(gs)
    result = dispatch(gs, "price_ipo", company_id=0, price=50.0, shares=1000)
    assert not result.ok


def test_ipo_grants_achievement():
    gs = _gs()
    _make_ipo_ready(gs)
    dispatch(gs, "prepare_ipo", company_id=0)
    dispatch(gs, "price_ipo", company_id=0, price=50.0, shares=1_000_000)
    assert "First company IPO" in gs.founder.achievements


# ─────────────────────── PRICE MOVEMENT DRIVERS ───────────────

def test_performance_drift_rewards_reputation():
    gs = _gs()
    c = gs.companies[0]
    c.monthly_revenue = 10_000
    c.reputation = 90
    high = stocks.performance_drift(gs, c)
    c.reputation = 20
    low = stocks.performance_drift(gs, c)
    assert high > low


def test_performance_drift_rewards_revenue():
    gs = _gs()
    c = gs.companies[0]
    c.reputation = 50
    c.monthly_revenue = 50_000
    high = stocks.performance_drift(gs, c)
    c.monthly_revenue = 0
    low = stocks.performance_drift(gs, c)
    assert high > low


def test_apply_price_shock_moves_price():
    gs = _gs()
    c = gs.companies[0]
    c.is_public = True
    c.share_price = 100.0
    stocks.apply_price_shock(c, 0.10)
    assert c.share_price > 100.0
    assert c.share_price_history[-1] == c.share_price


def test_apply_price_shock_noop_when_private():
    gs = _gs()
    c = gs.companies[0]
    c.share_price = 100.0
    stocks.apply_price_shock(c, 0.10)
    assert c.share_price == 100.0


# ─────────────────────── MONTHLY TICK ─────────────────────────

def test_monthly_tick_updates_mrr_streak():
    gs = _gs()
    c = gs.companies[0]
    c.monthly_revenue = 5000
    stocks.monthly_stocks_tick(gs)
    assert c.positive_mrr_streak == 1
    stocks.monthly_stocks_tick(gs)
    assert c.positive_mrr_streak == 2


def test_monthly_tick_resets_streak_on_zero_mrr():
    gs = _gs()
    c = gs.companies[0]
    c.positive_mrr_streak = 5
    c.monthly_revenue = 0
    stocks.monthly_stocks_tick(gs)
    assert c.positive_mrr_streak == 0


def test_monthly_tick_moves_parody_market():
    gs = _gs()
    stocks.init_market(gs)
    hist_before = len(gs.market["index_history"])
    stocks.monthly_stocks_tick(gs)
    assert len(gs.market["index_history"]) == hist_before + 1


def test_monthly_tick_moves_public_company_price():
    gs = _gs()
    c = gs.companies[0]
    c.is_public = True
    c.share_price = 100.0
    c.shares_outstanding = 1000
    hist_before = len(c.share_price_history)
    stocks.monthly_stocks_tick(gs)
    assert len(c.share_price_history) == hist_before + 1


def test_shareholder_pressure_on_bad_month():
    random.seed(1)
    gs = _gs()
    c = gs.companies[0]
    c.is_public = True
    c.share_price = 100.0
    c.shares_outstanding = 1000
    c.months_negative = 3
    # Run several ticks; with months_negative>0 pressure should eventually fire
    fired = False
    for _ in range(20):
        events = stocks.monthly_stocks_tick(gs)
        if any("pressure" in e[1].lower() for e in events):
            fired = True
            break
    assert fired


# ─────────────────────── LAUNCH REACTION ──────────────────────

def test_launch_bumps_public_company_stock():
    from vibe_coder_tycoon.models import Project
    gs = _gs()
    c = gs.companies[0]
    c.is_public = True
    c.share_price = 100.0
    c.shares_outstanding = 1000
    p = Project(
        name="Test", ptype="SaaS", model="m", stack="s", niche="n",
        company_id=c.id, status="Dev Complete", progress=100, revenue=0,
        users=0, morale=80, tokens_used=0, quality_score=70,
    )
    gs.projects.append(p)
    price_before = c.share_price
    result = dispatch(gs, "product_launch", project_idx=0)
    assert result.ok, result.message
    assert c.share_price > price_before


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_stocks_round_trip():
    gs = _gs()
    c = gs.companies[0]
    c.is_public = True
    c.ipo_stage = "Trading"
    c.share_price = 123.45
    c.shares_outstanding = 2_000_000
    c.player_equity_pct = 0.8
    c.positive_mrr_streak = 14
    c.share_price_history = [100.0, 110.0, 123.45]
    stocks.init_market(gs)
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    c2 = gs2.companies[0]
    assert c2.is_public
    assert c2.ipo_stage == "Trading"
    assert c2.share_price == 123.45
    assert c2.shares_outstanding == 2_000_000
    assert c2.player_equity_pct == 0.8
    assert c2.positive_mrr_streak == 14
    assert c2.share_price_history == [100.0, 110.0, 123.45]
    assert gs2.market.get("companies")


def test_trillionaire_threshold_constant():
    assert TRILLIONAIRE_THRESHOLD == 1_000_000_000_000
