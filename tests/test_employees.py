"""Phase 5 employee system tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.models import Founder, Company, Project, Employee, GameState
from vibe_coder_tycoon.engine import dispatch
from vibe_coder_tycoon.engine.systems import finance, employees
from vibe_coder_tycoon.constants import xp_threshold, TRAINING_ACTIONS


# ─────────────────────── FIXTURES ─────────────────────────────

def _founder(**kw) -> Founder:
    defaults = dict(
        username="TestFounder", background_idx=0,
        reputation=60, burnout=0,
        skill_prototyping=40, skill_sales=20,
        skill_tech=35, skill_management=20,
        total_tokens_used=0,
        personal_cash=1000.0, vibe=50.0, sanity=100,
    )
    defaults.update(kw)
    return Founder(**defaults)


def _company(**kw) -> Company:
    defaults = dict(
        id=0, name="TestCo", legal_style="Sole Proprietorship",
        focus_area="AI Tools", funding_style="Bootstrapped",
        risk_appetite="Balanced",
        cash=50000, monthly_revenue=0, monthly_expenses=300,
        debt=0, reputation=20, valuation=10000,
        office_level=8, mood=80,
        founded_month=1, founded_year=2025,
    )
    defaults.update(kw)
    return Company(**defaults)


def _emp(**kw) -> Employee:
    defaults = dict(
        name="Dev One", role="Vibe Coder", level=1, salary=2000,
        mood=80, skill=60, hired_year=2025, company_id=0,
        coding=60, prompting=60, research=50, marketing=40, sanity=80,
    )
    defaults.update(kw)
    return Employee(**defaults)


def _gs(**kw) -> GameState:
    f = kw.pop("founder", _founder())
    c = kw.pop("company", _company())
    return GameState(
        founder=f, year=2025, month=1, months_elapsed=0,
        active_ai_sub_idx=0, companies=[c], projects=[], employees=[],
        news_feed=[], events=[], research_progress={}, settings={},
        schema_version=6,
    )


# ─────────────────────── HIRING GATES ─────────────────────────

def test_hire_within_cap():
    gs = _gs(company=_company(office_level=1))  # cap 2
    cand = employees.generate_candidate(gs, 0, role="Vibe Coder")
    res = dispatch(gs, "hire_employee", company_id=0, candidate=cand)
    assert res.ok
    assert len(gs.employees) == 1


def test_hire_blocked_over_cap():
    gs = _gs(company=_company(office_level=1))  # cap 2
    gs.employees = [_emp(), _emp(name="Two")]
    cand = employees.generate_candidate(gs, 0, role="Vibe Coder")
    res = dispatch(gs, "hire_employee", company_id=0, candidate=cand)
    assert not res.ok
    assert "full" in res.message.lower()


def test_hire_blocked_role_locked():
    gs = _gs(company=_company(office_level=1))  # only lvl-1 roles
    cand = employees.generate_candidate(gs, 0, role="Vibe Coder")
    cand.role = "Finance Gremlin"  # unlocks at level 5
    res = dispatch(gs, "hire_employee", company_id=0, candidate=cand)
    assert not res.ok
    assert "office level" in res.message.lower()


def test_hire_blocked_low_reputation():
    gs = _gs(founder=_founder(reputation=5), company=_company(office_level=8))
    cand = employees.generate_candidate(gs, 0, role="Operations Goblin")
    cand.role = "Operations Goblin"  # min_reputation 60
    res = dispatch(gs, "hire_employee", company_id=0, candidate=cand)
    assert not res.ok
    assert "reputation" in res.message.lower()


# ─────────────────────── ASSIGNMENT & CONTRIBUTION ────────────

def test_assign_and_team_bonus():
    gs = _gs()
    p = Project(name="P", ptype="SaaS Web App", model="m", stack="s", niche="n",
                company_id=0, status="In Dev", progress=0, revenue=0, users=0,
                morale=80, tokens_used=0)
    gs.projects.append(p)
    gs.employees.append(_emp(coding=80, prompting=80, research=70))
    base = employees.get_project_team_bonus(gs, 0)
    assert base["design_mult"] == 1.0  # nobody assigned yet

    res = dispatch(gs, "assign_employee", emp_index=0, project_idx=0)
    assert res.ok
    bonus = employees.get_project_team_bonus(gs, 0)
    assert bonus["design_mult"] > 1.0
    assert bonus["tech_mult"] > 1.0
    assert bonus["bug_mult"] < 1.0  # QA suppresses bugs


def test_assign_rejects_other_company():
    gs = _gs()
    gs.companies.append(_company(id=1, name="Other"))
    p = Project(name="P", ptype="SaaS Web App", model="m", stack="s", niche="n",
                company_id=1, status="In Dev", progress=0, revenue=0, users=0,
                morale=80, tokens_used=0)
    gs.projects.append(p)
    gs.employees.append(_emp(company_id=0))
    res = dispatch(gs, "assign_employee", emp_index=0, project_idx=0)
    assert not res.ok


# ─────────────────────── XP / LEVELING ────────────────────────

def test_award_xp_levels_up():
    gs = _gs()
    p = Project(name="P", ptype="SaaS Web App", model="m", stack="s", niche="n",
                company_id=0, status="In Dev", progress=0, revenue=0, users=0,
                morale=80, tokens_used=0)
    gs.projects.append(p)
    e = _emp(assigned_project_id=0, level=1, coding=50)
    gs.employees.append(e)
    # threshold for level 1 is 100; grant 120
    events = employees.award_project_xp(gs, 0, amount=120)
    assert e.level == 2
    assert e.coding > 50  # primary stat boosted
    assert any("leveled up" in ev[1] for ev in events)


def test_xp_only_to_assigned():
    gs = _gs()
    p = Project(name="P", ptype="SaaS Web App", model="m", stack="s", niche="n",
                company_id=0, status="In Dev", progress=0, revenue=0, users=0,
                morale=80, tokens_used=0)
    gs.projects.append(p)
    assigned = _emp(name="A", assigned_project_id=0)
    idle = _emp(name="B", assigned_project_id=-1)
    gs.employees += [assigned, idle]
    employees.award_project_xp(gs, 0, amount=50)
    assert assigned.xp == 50
    assert idle.xp == 0


# ─────────────────────── TRAINING ─────────────────────────────

def test_training_boosts_stat_and_costs_cash():
    gs = _gs()
    e = _emp(prompting=50)
    gs.employees.append(e)
    cash_before = gs.companies[0].cash
    # index 0 = Pair Prompting (+prompting 6)
    res = dispatch(gs, "train_employee", emp_index=0, training_idx=0)
    assert res.ok
    assert e.prompting == 56
    assert gs.companies[0].cash == cash_before - TRAINING_ACTIONS[0]["cost"]


def test_training_blocked_no_cash():
    gs = _gs(company=_company(cash=10))
    gs.employees.append(_emp())
    res = dispatch(gs, "train_employee", emp_index=0, training_idx=2)
    assert not res.ok


# ─────────────────────── PAYROLL ──────────────────────────────

def test_payroll_deducted_in_settlement():
    gs = _gs(company=_company(cash=10000, monthly_revenue=5000, monthly_expenses=1000))
    gs.employees.append(_emp(salary=2000))
    gs.employees.append(_emp(name="Two", salary=1500))
    finance.monthly_settlement(gs)
    # net = 5000 - 1000 - (2000+1500) = 500
    assert gs.companies[0].cash == 10500


def test_fire_frees_payroll():
    gs = _gs()
    gs.employees.append(_emp(salary=2000))
    assert employees.company_payroll(gs, 0) == 2000
    res = dispatch(gs, "fire_employee", emp_index=0)
    assert res.ok
    assert employees.company_payroll(gs, 0) == 0
