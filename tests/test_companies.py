"""Phase 4 — Company System and Offices tests.

Covers focus can-build gating, office cap + upgrade enforcement, legal-upgrade
gating (cash + research), VC/IPO eligibility, synergy bonus math, and
inter-subsidiary transfers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.models import Founder, Company, GameState
from vibe_coder_tycoon.engine import dispatch
from vibe_coder_tycoon.engine.systems import companies as co


# ─────────────────────── FIXTURES ─────────────────────────────

def _founder(**kw) -> Founder:
    defaults = dict(
        username="TestFounder", background_idx=0,
        reputation=50, burnout=0,
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
        cash=5000, monthly_revenue=2000, monthly_expenses=1000,
        debt=0, reputation=20, valuation=10000,
        office_level=1, mood=80,
        founded_month=1, founded_year=2025,
        auto_deposit_pct=0, cover_from_personal=False, months_negative=0,
    )
    defaults.update(kw)
    return Company(**defaults)


def _gs(companies=None, founder=None) -> GameState:
    return GameState(
        founder=founder or _founder(),
        year=2025, month=1, months_elapsed=0,
        active_ai_sub_idx=0,
        companies=companies if companies is not None else [_company()],
        projects=[], employees=[],
        news_feed=[], events={},
        research_progress={},
        settings={},
        schema_version=5,
    )


# ─────────────────────── FOCUS CAN-BUILD GATING ───────────────

def test_focus_allows_permitted_product():
    c = _company(focus_area="AI Tools")
    allowed, _ = co.can_build_project_type(c, "AI Wrapper")
    assert allowed is True


def test_focus_blocks_disallowed_product():
    c = _company(focus_area="AI Tools")
    allowed, reason = co.can_build_project_type(c, "Content Platform")
    assert allowed is False
    assert reason


def test_holding_company_cannot_build_anything():
    c = _company(focus_area="Holding Company")
    allowed, reason = co.can_build_project_type(c, "SaaS Web App")
    assert allowed is False
    assert "cannot build" in reason.lower()


def test_unknown_focus_has_no_restrictions():
    c = _company(focus_area="Totally Made Up Focus")
    allowed, _ = co.can_build_project_type(c, "SaaS Web App")
    assert allowed is True


# ─────────────────────── OFFICE CAP + UPGRADE ─────────────────

def test_office_cap_matches_level():
    assert co.get_office_employee_cap(_company(office_level=1)) == 2
    assert co.get_office_employee_cap(_company(office_level=2)) == 4
    assert co.get_office_employee_cap(_company(office_level=3)) == 6


def test_unlocked_roles_accumulate_with_level():
    roles_l1 = co.get_all_unlocked_roles(_company(office_level=1))
    roles_l3 = co.get_all_unlocked_roles(_company(office_level=3))
    assert "Vibe Coder" in roles_l1
    assert set(roles_l1).issubset(set(roles_l3))
    assert len(roles_l3) > len(roles_l1)


def test_upgrade_office_success_raises_level_and_cap():
    gs = _gs([_company(office_level=1, cash=5000)])
    result = dispatch(gs, "upgrade_office", company_id=0)
    assert result.ok
    c = gs.company_by_id(0)
    assert c.office_level == 2
    assert co.get_office_employee_cap(c) == 4
    assert c.cash == 2000  # 5000 - 3000 upgrade cost


def test_upgrade_office_blocked_insufficient_cash():
    gs = _gs([_company(office_level=1, cash=100)])
    result = dispatch(gs, "upgrade_office", company_id=0)
    assert not result.ok
    assert gs.company_by_id(0).office_level == 1


# ─────────────────────── LEGAL UPGRADE GATING ─────────────────

def test_legal_upgrade_blocked_insufficient_cash():
    # Sole Proprietorship -> LLC needs $2000
    gs = _gs([_company(legal_style="Sole Proprietorship", cash=500)])
    result = dispatch(gs, "upgrade_legal", company_id=0)
    assert not result.ok
    assert gs.company_by_id(0).legal_style == "Sole Proprietorship"


def test_legal_upgrade_success_with_cash():
    gs = _gs([_company(legal_style="Sole Proprietorship", cash=5000)])
    result = dispatch(gs, "upgrade_legal", company_id=0)
    assert result.ok
    assert gs.company_by_id(0).legal_style == "LLC"


def test_legal_upgrade_blocked_without_required_research():
    # Partnership -> C-Corporation needs $15000 + "Cap Table Basics" research
    gs = _gs([_company(legal_style="Partnership", cash=20000)])
    result = dispatch(gs, "upgrade_legal", company_id=0)
    assert not result.ok
    assert "research" in result.message.lower()
    assert gs.company_by_id(0).legal_style == "Partnership"


def test_legal_upgrade_succeeds_with_research():
    f = _founder(unlocked_research=["Cap Table Basics"])
    gs = _gs([_company(legal_style="Partnership", cash=20000)], founder=f)
    result = dispatch(gs, "upgrade_legal", company_id=0)
    assert result.ok
    assert gs.company_by_id(0).legal_style == "C-Corporation"


# ─────────────────────── VC / IPO ELIGIBILITY ─────────────────

def test_vc_ipo_eligibility_by_legal_structure():
    assert co.is_vc_eligible(_company(legal_style="Sole Proprietorship")) is False
    assert co.is_ipo_eligible(_company(legal_style="LLC")) is False
    assert co.is_vc_eligible(_company(legal_style="C-Corporation")) is True
    assert co.is_ipo_eligible(_company(legal_style="C-Corporation")) is True
    assert co.is_ipo_eligible(_company(legal_style="Public Company")) is True


# ─────────────────────── SYNERGY BONUS MATH ───────────────────

def test_synergy_bonus_applied_when_partner_present():
    # AI Tools synergizes with Infrastructure
    ai = _company(id=0, focus_area="AI Tools")
    infra = _company(id=1, focus_area="Infrastructure")
    gs = _gs([ai, infra])
    assert co.get_synergy_bonus(gs, ai) == 0.9


def test_no_synergy_without_partner():
    ai = _company(id=0, focus_area="AI Tools")
    gs = _gs([ai])
    assert co.get_synergy_bonus(gs, ai) == 1.0


def test_no_synergy_when_partner_inactive():
    ai = _company(id=0, focus_area="AI Tools")
    infra = _company(id=1, focus_area="Infrastructure", active=False)
    gs = _gs([ai, infra])
    assert co.get_synergy_bonus(gs, ai) == 1.0


# ─────────────────────── HOLDING + TRANSFERS ──────────────────

def test_set_parent_requires_holding_focus():
    holding = _company(id=0, focus_area="SaaS", name="NotAHolding")
    sub = _company(id=1, focus_area="AI Tools", name="Sub")
    gs = _gs([holding, sub])
    result = dispatch(gs, "set_parent_company", company_id=1, parent_id=0)
    assert not result.ok
    assert gs.company_by_id(1).parent_company_id == -1


def test_set_parent_success_with_holding():
    holding = _company(id=0, focus_area="Holding Company", name="Holdings")
    sub = _company(id=1, focus_area="AI Tools", name="Sub")
    gs = _gs([holding, sub])
    result = dispatch(gs, "set_parent_company", company_id=1, parent_id=0)
    assert result.ok
    assert gs.company_by_id(1).parent_company_id == 0


def test_transfer_between_parent_and_subsidiary():
    holding = _company(id=0, focus_area="Holding Company", name="Holdings", cash=1000)
    sub = _company(id=1, focus_area="AI Tools", name="Sub", cash=5000,
                   parent_company_id=0)
    gs = _gs([holding, sub])
    result = dispatch(gs, "transfer_between_companies",
                      from_id=1, to_id=0, amount=3000)
    assert result.ok
    assert gs.company_by_id(1).cash == 2000
    assert gs.company_by_id(0).cash == 4000


def test_transfer_between_siblings():
    holding = _company(id=0, focus_area="Holding Company", name="Holdings")
    sub_a = _company(id=1, name="A", cash=5000, parent_company_id=0)
    sub_b = _company(id=2, name="B", cash=1000, parent_company_id=0)
    gs = _gs([holding, sub_a, sub_b])
    result = dispatch(gs, "transfer_between_companies",
                      from_id=1, to_id=2, amount=2000)
    assert result.ok
    assert gs.company_by_id(1).cash == 3000
    assert gs.company_by_id(2).cash == 3000


def test_transfer_blocked_outside_holding_group():
    a = _company(id=0, name="A", cash=5000)
    b = _company(id=1, name="B", cash=1000)
    gs = _gs([a, b])
    result = dispatch(gs, "transfer_between_companies",
                      from_id=0, to_id=1, amount=1000)
    assert not result.ok
    assert gs.company_by_id(0).cash == 5000


def test_transfer_blocked_insufficient_cash():
    holding = _company(id=0, focus_area="Holding Company", cash=0)
    sub = _company(id=1, cash=500, parent_company_id=0)
    gs = _gs([holding, sub])
    result = dispatch(gs, "transfer_between_companies",
                      from_id=1, to_id=0, amount=1000)
    assert not result.ok
    assert gs.company_by_id(1).cash == 500


def test_transfer_rejects_nonpositive_amount():
    holding = _company(id=0, focus_area="Holding Company")
    sub = _company(id=1, cash=500, parent_company_id=0)
    gs = _gs([holding, sub])
    result = dispatch(gs, "transfer_between_companies",
                      from_id=1, to_id=0, amount=0)
    assert not result.ok
