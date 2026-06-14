"""Phase 7 tech-timeline / models / IDEs / subscriptions tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.models import Founder, Company, GameState
from vibe_coder_tycoon.engine import dispatch, advance_month
from vibe_coder_tycoon.engine.systems import models_ai
from vibe_coder_tycoon.data.ai_models import AI_MODELS


def _founder(**kw) -> Founder:
    defaults = dict(
        username="T7", background_idx=0, reputation=60, burnout=0,
        skill_prototyping=40, skill_sales=20, skill_tech=35, skill_management=20,
        total_tokens_used=0, personal_cash=100000.0, vibe=50.0, sanity=100,
    )
    defaults.update(kw)
    return Founder(**defaults)


def _company(**kw) -> Company:
    defaults = dict(
        id=0, name="TestCo", legal_style="Sole Proprietorship",
        focus_area="AI Tools", funding_style="Bootstrapped", risk_appetite="Balanced",
        cash=50000, monthly_revenue=0, monthly_expenses=0, debt=0, reputation=20,
        valuation=10000, office_level=8, mood=80, founded_month=1, founded_year=2025,
    )
    defaults.update(kw)
    return Company(**defaults)


def _gs(year=2025, **kw) -> GameState:
    return GameState(
        founder=kw.pop("founder", _founder()), year=year, month=1, months_elapsed=0,
        active_ai_sub_idx=0, companies=[_company()], projects=[], employees=[],
        news_feed=[], events=[], research_progress={}, settings={},
        current_era=models_ai.era_for_year(year),
    )


# ─────────────────────── YEAR GATING ──────────────────────────

def test_models_gated_by_year():
    gs = _gs(year=2022)
    avail = models_ai.available_models(gs)
    assert avail, "should have some 2022-era models"
    assert all(m["year"] <= 2022 for m in avail)
    # A later year unlocks strictly more
    gs_late = _gs(year=2026)
    assert len(models_ai.available_models(gs_late)) > len(avail)


def test_set_active_model_rejects_future():
    gs = _gs(year=2022)
    future = max(AI_MODELS, key=lambda m: m["year"])
    if future["year"] > 2022:
        res = dispatch(gs, "set_active_model", model_name=future["name"])
        assert not res.ok


def test_set_active_ide_rejects_future():
    gs = _gs(year=2022)
    res = dispatch(gs, "set_active_ide", ide_name="Clod Code")  # 2025
    assert not res.ok
    res2 = dispatch(gs, "set_active_ide", ide_name="CodeBox")   # 2022
    assert res2.ok


# ─────────────────────── ERAS ─────────────────────────────────

def test_era_for_year():
    assert models_ai.era_for_year(2022) == "The Discovery Era"
    assert models_ai.era_for_year(2025) == "The Builder Era"
    assert models_ai.era_for_year(2028) == "The Agent Era"
    assert models_ai.era_for_year(2033) == "The Automation Era"
    assert models_ai.era_for_year(2040) == "The God Complex Era"


def test_era_transition_emits_event():
    gs = _gs(year=2026)  # Builder Era
    gs.month = 12
    gs.current_era = "The Builder Era"
    advance_month(gs)  # -> 2027 Jan, Agent Era
    assert gs.year == 2027
    assert gs.current_era == "The Agent Era"
    assert any("Agent Era" in (n.get("headline", "")) for n in gs.news_feed)


# ─────────────────────── POST-2042 AUTO-VERSION ───────────────

def test_post_2042_auto_versioning():
    gs = _gs(year=2045)
    future = models_ai._future_models(gs)
    assert future, "frontier models should be generated after 2042"
    assert all(m["year"] == 2045 for m in future)
    assert all(m["score"] <= 10.0 for m in future)


# ─────────────────────── SUBSCRIPTION COST ────────────────────

def test_flat_subscription_cost_hits_personal_cash():
    gs = _gs()
    dispatch(gs, "set_subscription_tier", tier="Pro+")
    before = gs.founder.personal_cash
    events = models_ai.subscription_settlement(gs)
    assert gs.founder.personal_cash == before - 200
    assert gs.tokens_this_month == 0
    assert events


def test_api_subscription_scales_with_tokens():
    gs = _gs()
    dispatch(gs, "set_subscription_tier", tier="API Usage")
    gs.tokens_this_month = 1000
    before = gs.founder.personal_cash
    models_ai.subscription_settlement(gs)
    # per_token 0.03 * 1000 = 30
    assert before - gs.founder.personal_cash == 30


def test_self_hosted_rejects_paid_model():
    gs = _gs(year=2026)
    dispatch(gs, "set_subscription_tier", tier="Self-Hosted")
    paid = next((m for m in models_ai.available_models(gs) if m["out_cost"] > 0), None)
    if paid:
        res = dispatch(gs, "set_active_model", model_name=paid["name"])
        assert not res.ok


# ─────────────────────── DEV MODIFIERS ────────────────────────

def test_dev_modifiers_reflect_ide_and_sub():
    gs = _gs(year=2026)
    dispatch(gs, "set_active_ide", ide_name="Clod Code")
    dispatch(gs, "set_subscription_tier", tier="Pro+")
    mods = models_ai.get_dev_modifiers(gs)
    assert mods["dev_speed_mult"] > 1.0
    assert mods["bug_mult"] < 1.0


def test_get_model_stats_fallback():
    gs = _gs()
    # Unknown model name falls back to active subscription's basic stats.
    stats = models_ai.get_model_stats(gs, "Nonexistent Model 9000")
    assert {"speed", "quality", "bug_risk", "tokens"} <= set(stats)
