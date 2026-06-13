"""
Phase 3 — Product Lifecycle tests
Covers: launch resolution, monthly tick, obsolescence, minor/major update, discontinue, versioning, auto-update.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, advance_month, dispatch
from vibe_coder_tycoon.models import Founder, Project
from vibe_coder_tycoon.engine.systems.products import (
    launch_product, monthly_product_tick, _obsolescence_factor, _calc_revenue_from_users
)
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs():
    f = Founder(username="Tester", background_idx=0, reputation=40, burnout=0,
                skill_prototyping=50, skill_sales=30, skill_tech=40, skill_management=30,
                total_tokens_used=0)
    return make_new_game(f, 3)  # DeepVault Coder


def _finished_project(ptype="SaaS Web App", quality=70, hype=60, bug_count=2,
                      scope="Standard", faked=0):
    p = Project(
        name="TestApp", ptype=ptype, model="DeepVault Coder",
        stack="T3 Stack", niche="Productivity", company_id=0,
        status="Dev Complete", progress=100, revenue=0, users=0, morale=80,
        tokens_used=300, design_score=float(quality), tech_score=float(quality - 5),
        quality_score=quality, hype=hype, scope=scope, bug_count=bug_count,
        faked_features=[f"Feat{i}" for i in range(faked)],
    )
    return p


# ─────────────────────── LAUNCH RESOLUTION ────────────────────

def test_launch_sets_status():
    gs = _gs()
    gs.projects.append(_finished_project())
    result = dispatch(gs, "dev_launch", project_idx=0)
    assert result.ok
    assert gs.projects[0].status == "Launched"


def test_launch_sets_revenue_model():
    gs = _gs()
    gs.projects.append(_finished_project(ptype="SaaS Web App"))
    dispatch(gs, "dev_launch", project_idx=0)
    assert gs.projects[0].revenue_model == "Subscription"


def test_launch_mobile_uses_ads_model():
    gs = _gs()
    gs.projects.append(_finished_project(ptype="Mobile App"))
    dispatch(gs, "dev_launch", project_idx=0)
    assert gs.projects[0].revenue_model == "Ads"


def test_launch_rolls_obsolescence_window():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    assert p.obsolescence_months > 0


def test_launch_sets_active_users():
    gs = _gs()
    gs.projects.append(_finished_project(quality=80, hype=70))
    dispatch(gs, "dev_launch", project_idx=0)
    assert gs.projects[0].active_users >= 5


def test_high_quality_low_hype_has_low_churn():
    gs = _gs()
    gs.projects.append(_finished_project(quality=90, hype=30, bug_count=0))
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    low_churn = p.churn_rate

    gs2 = _gs()
    gs2.projects.append(_finished_project(quality=30, hype=90, bug_count=10))
    dispatch(gs2, "dev_launch", project_idx=0)
    high_churn = gs2.projects[0].churn_rate

    assert low_churn < high_churn


def test_faked_features_increase_churn_at_launch():
    gs = _gs()
    gs.projects.append(_finished_project(hype=60, quality=60, faked=3))
    rep_before = gs.founder.reputation
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    assert p.churn_rate > 0.05
    assert gs.founder.reputation < rep_before + 10  # reputation gain reduced by faked penalty


def test_launch_sets_revenue_history():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    assert len(gs.projects[0].revenue_history) == 1


def test_launch_not_ready_fails():
    gs = _gs()
    p = _finished_project()
    p.status = "In Dev"
    gs.projects.append(p)
    result = dispatch(gs, "product_launch", project_idx=0)
    assert not result.ok


# ─────────────────────── MONTHLY TICK ─────────────────────────

def test_monthly_tick_ages_product():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    assert p.age_months == 0
    monthly_product_tick(gs, p, "Feb 2025")
    assert p.age_months == 1


def test_quality_product_grows_users():
    gs = _gs()
    gs.projects.append(_finished_project(quality=90, hype=60, bug_count=0))
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    initial_users = p.active_users
    for _ in range(6):
        monthly_product_tick(gs, p, "Mar 2025")
    assert p.active_users >= initial_users  # quality > churn → net growth


def test_buggy_product_loses_users():
    gs = _gs()
    gs.projects.append(_finished_project(quality=20, hype=80, bug_count=20, faked=3))
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    initial_users = p.active_users
    for _ in range(6):
        monthly_product_tick(gs, p, "Mar 2025")
    assert p.active_users <= initial_users  # high churn → net decline


def test_revenue_history_capped_at_12():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    for i in range(15):
        monthly_product_tick(gs, p, f"Month {i}")
    assert len(p.revenue_history) == 12


# ─────────────────────── OBSOLESCENCE ─────────────────────────

def test_obsolescence_factor_fresh():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.age_months = 0
    p.obsolescence_months = 24
    assert _obsolescence_factor(p) == 1.0


def test_obsolescence_factor_at_50pct():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.age_months = 12
    p.obsolescence_months = 24
    assert _obsolescence_factor(p) == 1.0  # exactly 50% — still 1.0


def test_obsolescence_factor_past_midpoint():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.age_months = 18
    p.obsolescence_months = 24  # 75% through window
    factor = _obsolescence_factor(p)
    assert 0.1 < factor < 1.0


def test_obsolescence_factor_floored_at_01():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.age_months = 100
    p.obsolescence_months = 24
    assert _obsolescence_factor(p) == 0.1


# ─────────────────────── MINOR UPDATE ─────────────────────────

def test_minor_update_resets_age():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.age_months = 10
    result = dispatch(gs, "product_minor_update", project_idx=0)
    assert result.ok
    assert p.age_months == 4  # 10 - 6


def test_minor_update_reduces_churn():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    p.churn_rate = 0.08
    dispatch(gs, "product_minor_update", project_idx=0)
    assert p.churn_rate < 0.08


def test_minor_update_costs_cash():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    c = gs.company_by_id(0)
    cash_before = c.cash
    dispatch(gs, "product_minor_update", project_idx=0)
    assert c.cash == cash_before - 150


def test_minor_update_insufficient_cash_fails():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    c = gs.company_by_id(0)
    c.cash = 50
    result = dispatch(gs, "product_minor_update", project_idx=0)
    assert not result.ok


def test_minor_update_not_launched_fails():
    gs = _gs()
    gs.projects.append(_finished_project())
    result = dispatch(gs, "product_minor_update", project_idx=0)
    assert not result.ok


# ─────────────────────── MAJOR REVISION ───────────────────────

def test_major_revision_sets_in_dev():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    result = dispatch(gs, "product_major_revision", project_idx=0)
    assert result.ok
    assert gs.projects[0].status == "In Dev"


def test_major_revision_bumps_version():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_major_revision", project_idx=0)
    assert gs.projects[0].version == 2


def test_major_revision_creates_dev_session():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_major_revision", project_idx=0)
    assert gs.projects[0].dev_session is not None


def test_major_revision_carries_legacy_quality():
    gs = _gs()
    gs.projects.append(_finished_project(quality=80))
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    dispatch(gs, "product_major_revision", project_idx=0)
    assert p.design_score > 0  # carried forward (40% of 80 = 32)
    assert p.design_score < 80


def test_major_revision_on_in_dev_fails():
    gs = _gs()
    gs.projects.append(_finished_project())
    result = dispatch(gs, "product_major_revision", project_idx=0)
    assert not result.ok


# ─────────────────────── DISCONTINUE ──────────────────────────

def test_discontinue_sets_sunset():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    result = dispatch(gs, "product_discontinue", project_idx=0)
    assert result.ok
    p = gs.projects[0]
    assert p.status == "Sunset"
    assert p.discontinued is True


def test_discontinue_zeroes_revenue():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    result = dispatch(gs, "product_discontinue", project_idx=0)
    assert gs.projects[0].revenue == 0
    assert gs.projects[0].active_users == 0


def test_discontinue_already_sunset_fails():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_discontinue", project_idx=0)
    result = dispatch(gs, "product_discontinue", project_idx=0)
    assert not result.ok


# ─────────────────────── NEW VERSION ──────────────────────────

def test_new_version_creates_child_project():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    result = dispatch(gs, "product_new_version", project_idx=0)
    assert result.ok
    assert len(gs.projects) == 2


def test_new_version_increments_version_number():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_new_version", project_idx=0)
    assert gs.projects[1].version == 2


def test_new_version_transfers_users():
    gs = _gs()
    gs.projects.append(_finished_project(quality=80, hype=70))
    dispatch(gs, "dev_launch", project_idx=0)
    p_orig = gs.projects[0]
    orig_users = p_orig.active_users
    dispatch(gs, "product_new_version", project_idx=0)
    p_new = gs.projects[1]
    assert p_new.active_users > 0
    assert p_orig.active_users + p_new.active_users == orig_users


def test_new_version_child_in_dev():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_new_version", project_idx=0)
    assert gs.projects[1].status == "In Dev"
    assert gs.projects[1].dev_session is not None


# ─────────────────────── AUTO-UPDATE ──────────────────────────

def test_set_auto_update_interval():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    result = dispatch(gs, "product_set_auto_update", project_idx=0, interval=2)
    assert result.ok
    assert gs.projects[0].auto_update_interval == 2
    assert gs.projects[0].auto_update_countdown == 2


def test_auto_update_fires_on_tick():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_set_auto_update", project_idx=0, interval=1)
    p = gs.projects[0]
    p.age_months = 10  # give it some age to reset
    events = monthly_product_tick(gs, p, "Jan 2026")
    assert any("Auto-updated" in str(e) for e in events)
    assert p.age_months < 10  # age was reset by update


def test_auto_update_disable():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_set_auto_update", project_idx=0, interval=2)
    result = dispatch(gs, "product_set_auto_update", project_idx=0, interval=0)
    assert result.ok
    assert gs.projects[0].auto_update_interval == 0


# ─────────────────────── SERIALIZATION ────────────────────────

def test_phase3_fields_survive_round_trip():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    dispatch(gs, "product_set_auto_update", project_idx=0, interval=3)
    p = gs.projects[0]
    p.age_months = 5
    p.revenue_history = [100, 200, 300]

    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    p2 = gs2.projects[0]

    assert p2.revenue_model == "Subscription"
    assert p2.active_users == p.active_users
    assert p2.churn_rate == p.churn_rate
    assert p2.obsolescence_months == p.obsolescence_months
    assert p2.age_months == 5
    assert p2.auto_update_interval == 3
    assert p2.revenue_history == [100, 200, 300]
    assert p2.version == 1
    assert p2.discontinued is False


def test_advance_month_uses_product_tick():
    gs = _gs()
    gs.projects.append(_finished_project())
    dispatch(gs, "dev_launch", project_idx=0)
    p = gs.projects[0]
    rev_before = p.revenue
    advance_month(gs)
    assert p.age_months == 1  # monthly_product_tick was called


# ─────────────────────── RUNNER ───────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__} — {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
