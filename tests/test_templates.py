"""
Phase 8 — Templates tests.

Covers: build flow through the dev phase, bonus application (design/tech/time/
bugs), version comparison (better tools → stronger template), company-scope
enforcement, and save round-trip.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, advance_month, dispatch
from vibe_coder_tycoon.models import Founder, Company, Project, Template
from vibe_coder_tycoon.engine.systems import templates as tm
from vibe_coder_tycoon.engine.systems.development import start_dev_session, _finalize_dev
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs():
    f = Founder(username="Tester", background_idx=0, reputation=40, burnout=0,
                skill_prototyping=50, skill_sales=30, skill_tech=40, skill_management=30,
                total_tokens_used=0)
    return make_new_game(f, 3)


def _second_company(gs, focus="SaaS"):
    cid = len(gs.companies)
    c = Company(
        id=cid, name="SecondCo", legal_style="LLC", focus_area=focus,
        funding_style="Bootstrapped", risk_appetite="Balanced",
        cash=10_000, monthly_revenue=0, monthly_expenses=0, debt=0,
        reputation=20, valuation=10_000, office_level=1, mood=80,
        founded_month=1, founded_year=2025,
    )
    gs.companies.append(c)
    return c


# ─────────────────────── BUILD FLOW ───────────────────────────

def test_build_template_creates_in_dev_project():
    gs = _gs()
    cash_before = gs.companies[0].cash
    res = dispatch(gs, "build_template", company_id=0, template_type="SaaS Boilerplate")
    assert res.ok
    builds = [p for p in gs.projects if p.is_template]
    assert len(builds) == 1
    assert builds[0].status == "In Dev"
    assert gs.companies[0].cash < cash_before   # build cost paid


def test_build_template_insufficient_cash():
    gs = _gs()
    gs.companies[0].cash = 10
    res = dispatch(gs, "build_template", company_id=0, template_type="AI Agent Scaffold")
    assert not res.ok
    assert not any(p.is_template for p in gs.projects)


def test_template_finalizes_into_asset():
    gs = _gs()
    dispatch(gs, "build_template", company_id=0, template_type="SaaS Boilerplate")
    p = next(p for p in gs.projects if p.is_template)
    # Force the build to completion and finalize.
    p.design_score = 80.0
    p.tech_score = 70.0
    p.bug_count = 0
    p.dev_day = p.dev_total_days
    _finalize_dev(gs, p)
    assert p.status == "Template"
    assert len(gs.templates) == 1
    t = gs.templates[0]
    assert t.design_bonus > 0 and t.tech_bonus > 0
    assert 0 < t.time_reduction <= 0.30
    assert 0 < t.bug_reduction <= 0.50


# ─────────────────────── BONUS APPLICATION ────────────────────

def _make_template(gs, cid, version=1, design=12.0, tech=10.0, time_r=0.2, bug_r=0.3):
    t = Template(name=f"SaaS Boilerplate v{version}", template_type="SaaS Boilerplate",
                 version=version, company_id=cid, design_bonus=design, tech_bonus=tech,
                 time_reduction=time_r, bug_reduction=bug_r, built_year=2025)
    gs.templates.append(t)
    return len(gs.templates) - 1


def test_template_applies_headstart_and_time_cut():
    gs = _gs()
    tid = _make_template(gs, 0, design=12.0, tech=10.0, time_r=0.25)
    p = Project(name="App", ptype="SaaS Web App", model="DeepVault Coder",
                stack="T3", niche="Productivity", company_id=0, status="In Dev",
                progress=0, revenue=0, users=0, morale=80, tokens_used=0,
                scope="Standard", template_id=tid)
    gs.projects.append(p)
    start_dev_session(gs, len(gs.projects) - 1)
    assert p.design_score >= 12.0
    assert p.tech_score >= 10.0
    assert p.dev_total_days < 60   # time reduction applied


def test_template_bug_multiplier():
    gs = _gs()
    tid = _make_template(gs, 0, bug_r=0.4)
    p = Project(name="App", ptype="SaaS Web App", model="X", stack="T3",
                niche="Productivity", company_id=0, status="In Dev", progress=0,
                revenue=0, users=0, morale=80, tokens_used=0, template_id=tid)
    gs.projects.append(p)
    assert abs(tm.template_bug_multiplier(gs, p) - 0.6) < 1e-6


# ─────────────────────── VERSIONING ───────────────────────────

def test_versions_increment_per_company_and_type():
    gs = _gs()
    _make_template(gs, 0, version=1)
    assert tm.next_template_version(gs, 0, "SaaS Boilerplate") == 2
    assert tm.next_template_version(gs, 0, "Auth Framework") == 1


def test_better_build_yields_stronger_template():
    gs = _gs()
    # v1 built with weak scores
    p1 = Project(name="t1", ptype="Developer Tool", model="", stack="Internal",
                 niche="Internal", company_id=0, status="In Dev", progress=0,
                 revenue=0, users=0, morale=80, tokens_used=0, is_template=True,
                 template_type="SaaS Boilerplate", design_score=40.0, tech_score=35.0,
                 dev_total_days=20, dev_day=20)
    gs.projects.append(p1)
    _finalize_dev(gs, p1)
    # v2 built with strong scores (better tools/team)
    p2 = Project(name="t2", ptype="Developer Tool", model="", stack="Internal",
                 niche="Internal", company_id=0, status="In Dev", progress=0,
                 revenue=0, users=0, morale=80, tokens_used=0, is_template=True,
                 template_type="SaaS Boilerplate", design_score=90.0, tech_score=85.0,
                 dev_total_days=20, dev_day=20)
    gs.projects.append(p2)
    _finalize_dev(gs, p2)
    v1, v2 = gs.templates[0], gs.templates[1]
    assert v2.version == 2
    assert v2.design_bonus > v1.design_bonus
    assert v2.tech_bonus > v1.tech_bonus
    assert v2.bug_reduction >= v1.bug_reduction


# ─────────────────────── COMPANY SCOPE ────────────────────────

def test_templates_company_scoped():
    gs = _gs()
    c2 = _second_company(gs)
    _make_template(gs, 0)
    assert len(tm.templates_for_company(gs, 0)) == 1
    assert len(tm.templates_for_company(gs, c2.id)) == 0


def test_other_company_template_not_applied():
    gs = _gs()
    c2 = _second_company(gs)
    tid = _make_template(gs, c2.id, design=20.0, tech=20.0, time_r=0.3)
    # A company-0 project that (incorrectly) references c2's template must not benefit.
    p = Project(name="App", ptype="SaaS Web App", model="X", stack="T3",
                niche="Productivity", company_id=0, status="In Dev", progress=0,
                revenue=0, users=0, morale=80, tokens_used=0, scope="Standard",
                template_id=tid)
    gs.projects.append(p)
    start_dev_session(gs, len(gs.projects) - 1)
    assert p.design_score == 0.0
    assert p.tech_score == 0.0
    assert p.dev_total_days == 60   # no time cut
    assert tm.template_bug_multiplier(gs, p) == 1.0


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_template_round_trip():
    gs = _gs()
    _make_template(gs, 0, design=11.0, tech=9.0, time_r=0.15, bug_r=0.25)
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    assert len(gs2.templates) == 1
    t = gs2.templates[0]
    assert t.template_type == "SaaS Boilerplate"
    assert abs(t.design_bonus - 11.0) < 1e-6
    assert abs(t.bug_reduction - 0.25) < 1e-6
