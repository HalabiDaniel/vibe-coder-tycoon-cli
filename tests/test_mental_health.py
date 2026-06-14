"""Phase 6 mental-health system tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.models import Founder, Company, Project, Employee, GameState
from vibe_coder_tycoon.engine import dispatch
from vibe_coder_tycoon.engine.systems import mental_health
from vibe_coder_tycoon.constants import (
    CONDITIONS, TEAM_RECHARGE_COST, INSPIRE_VIBE_COST,
)


# ─────────────────────── FIXTURES ─────────────────────────────

def _founder(**kw) -> Founder:
    defaults = dict(
        username="MH", background_idx=0, reputation=60, burnout=0,
        skill_prototyping=40, skill_sales=20, skill_tech=35, skill_management=20,
        total_tokens_used=0, personal_cash=1000.0, vibe=50.0, sanity=100,
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


def _emp(**kw) -> Employee:
    defaults = dict(
        name="Dev One", role="Vibe Coder", level=1, salary=2000, mood=80, skill=60,
        hired_year=2025, company_id=0, coding=60, prompting=60, research=50,
        marketing=40, sanity=80,
    )
    defaults.update(kw)
    return Employee(**defaults)


def _gs(**kw) -> GameState:
    f = kw.pop("founder", _founder())
    c = kw.pop("company", _company())
    emps = kw.pop("employees", [])
    projs = kw.pop("projects", [])
    return GameState(
        founder=f, year=2025, month=1, months_elapsed=kw.pop("months_elapsed", 0),
        active_ai_sub_idx=0, companies=[c], projects=projs, employees=emps,
        news_feed=[], events=[], research_progress={}, settings={},
    )


def _proj(**kw) -> Project:
    defaults = dict(
        name="P", ptype="SaaS Web App", model="ChatNPC Basic", stack="T3", niche="Dev",
        company_id=0, status="In Dev", progress=10, revenue=0, users=0, morale=80,
        tokens_used=0,
    )
    defaults.update(kw)
    return Project(**defaults)


# ─────────────────────── DRAIN / RECOVERY ─────────────────────

def test_assigned_employee_sanity_drains():
    e = _emp(sanity=80, assigned_project_id=0)
    gs = _gs(employees=[e], projects=[_proj(bug_count=4)])
    mental_health.monthly_tick(gs)
    assert e.sanity < 80


def test_idle_employee_recovers():
    e = _emp(sanity=50, assigned_project_id=-1)
    gs = _gs(employees=[e])
    mental_health.monthly_tick(gs)
    assert e.sanity > 50


# ─────────────────────── CONDITIONS ───────────────────────────

def test_sanity_threshold_conditions():
    e = _emp(assigned_project_id=-1)
    gs = _gs(employees=[e])
    e.sanity = 8
    assert mental_health._eval_employee_condition(gs, e, False) == "Existential Crisis"
    e.sanity = 18
    assert mental_health._eval_employee_condition(gs, e, False) == "Burnout"
    e.sanity = 50
    assert mental_health._eval_employee_condition(gs, e, False) == ""


def test_startup_mania_high_vibe():
    e = _emp(sanity=60)
    gs = _gs(founder=_founder(vibe=95), employees=[e])
    assert mental_health._eval_employee_condition(gs, e, high_vibe=True) == "Startup Mania"


def test_condition_stat_multiplier():
    e = _emp(condition="Burnout")
    assert mental_health.employee_stat_mult(e) == CONDITIONS["Burnout"]["stat_mult"]
    e2 = _emp(condition="")
    assert mental_health.employee_stat_mult(e2) == 1.0


# ─────────────────────── TOUCH GRASS ──────────────────────────

def test_touch_grass_on_zero_and_return():
    e = _emp(sanity=2, assigned_project_id=0)
    gs = _gs(employees=[e], projects=[_proj(bug_count=10)], founder=_founder(vibe=95))
    mental_health.monthly_tick(gs)
    assert e.state == "touch_grass"
    assert e.assigned_project_id == -1
    # Advance to the return month
    gs.months_elapsed = e.state_until
    mental_health.monthly_tick(gs)
    assert e.state == "active"
    assert e.sanity >= 40


# ─────────────────────── FOUNDER LINK ─────────────────────────

def test_founder_sanity_drains_with_dev_and_crisis():
    gs = _gs(projects=[_proj()])
    gs.companies[0].months_negative = 2
    mental_health.monthly_tick(gs)
    assert gs.founder.sanity < 100


def test_founder_conditions_at_low_sanity():
    gs = _gs(founder=_founder(sanity=20), projects=[_proj()])
    mental_health._founder_tick(gs, "Jan 2025")
    assert gs.founder.conditions  # some condition set


# ─────────────────────── ACTIONS ──────────────────────────────

def test_team_recharge_restores_and_costs():
    e = _emp(sanity=20, condition="Burnout")
    gs = _gs(employees=[e], company=_company(cash=TEAM_RECHARGE_COST + 10))
    res = dispatch(gs, "team_recharge", company_id=0)
    assert res.ok
    assert e.sanity == 45
    assert e.condition == ""
    assert gs.companies[0].cash == 10


def test_team_recharge_blocked_when_broke():
    e = _emp(sanity=20)
    gs = _gs(employees=[e], company=_company(cash=0))
    res = dispatch(gs, "team_recharge", company_id=0)
    assert not res.ok


def test_inspirational_talk_spends_vibe_and_resolves():
    e = _emp(sanity=8, condition="Existential Crisis")
    gs = _gs(employees=[e], founder=_founder(vibe=50))
    res = dispatch(gs, "inspirational_talk", emp_index=0)
    assert res.ok
    assert e.condition == ""
    assert gs.founder.vibe == 50 - INSPIRE_VIBE_COST


def test_distraction_resolves_doom_spiral():
    e = _emp(condition="AI Doom Spiral")
    gs = _gs(employees=[e], company=_company(cash=1000))
    res = dispatch(gs, "distraction", emp_index=0)
    assert res.ok
    assert e.condition == ""


def test_founder_take_break_restores():
    gs = _gs(founder=_founder(sanity=30, vibe=60, conditions=["Founder Burnout"]))
    res = dispatch(gs, "founder_take_break")
    assert res.ok
    assert gs.founder.sanity == 55
    assert gs.founder.conditions == []
