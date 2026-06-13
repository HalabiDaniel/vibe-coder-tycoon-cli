"""Phase 1 finance system tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.models import Founder, Company, GameState, Loan
from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.engine.systems import finance


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
        id=0, name="TestCo", legal_style="Solo Hustle",
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


def _gs(**kw) -> GameState:
    f = kw.pop("founder", _founder())
    c = kw.pop("company", _company())
    return GameState(
        founder=f,
        year=2025, month=1, months_elapsed=0,
        active_ai_sub_idx=0,
        companies=[c],
        projects=[], employees=[],
        news_feed=[], events={},
        research_progress={},
        settings={},
        schema_version=2,
    )


# ─────────────────────── MONTHLY SETTLEMENT ───────────────────

def test_positive_net_adds_to_cash():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 5000
    c.monthly_revenue = 2000
    c.monthly_expenses = 1000
    finance.monthly_settlement(gs)
    assert c.cash == 6000  # 5000 + (2000 - 1000)


def test_negative_net_no_cover():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 5000
    c.monthly_revenue = 500
    c.monthly_expenses = 1000
    c.cover_from_personal = False
    finance.monthly_settlement(gs)
    assert c.cash == 4500
    assert c.months_negative == 1


def test_negative_net_with_cover_from_personal():
    gs = _gs(founder=_founder(personal_cash=2000.0))
    c = gs.companies[0]
    c.cash = 5000
    c.monthly_revenue = 500
    c.monthly_expenses = 1000
    c.cover_from_personal = True
    finance.monthly_settlement(gs)
    # Personal covers the -500 shortfall
    assert gs.founder.personal_cash == 1500.0
    assert c.months_negative == 0


def test_cover_personal_insufficient_funds():
    gs = _gs(founder=_founder(personal_cash=100.0))
    c = gs.companies[0]
    c.cash = 0
    c.monthly_revenue = 0
    c.monthly_expenses = 500
    c.cover_from_personal = True
    finance.monthly_settlement(gs)
    # Personal can't cover — months_negative should increment
    assert c.months_negative == 1
    assert gs.founder.personal_cash == 100.0  # unchanged


def test_auto_deposit():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 5000
    c.monthly_revenue = 2000
    c.monthly_expenses = 1000
    c.auto_deposit_pct = 25
    finance.monthly_settlement(gs)
    net = 1000  # 2000 - 1000
    deposit = int(net * 0.25)  # 250
    assert gs.founder.personal_cash == 1000.0 + deposit
    assert c.cash == 5000 + net - deposit


def test_vibe_decays_per_month():
    gs = _gs(founder=_founder(vibe=50.0))
    finance.monthly_settlement(gs)
    assert gs.founder.vibe == 49.5


def test_vibe_floored_at_zero():
    gs = _gs(founder=_founder(vibe=0.0))
    finance.monthly_settlement(gs)
    assert gs.founder.vibe == 0.0


# ─────────────────────── TOKENS ───────────────────────────────

def test_tokens_monotonically_increase():
    gs = _gs(founder=_founder(total_tokens_used=0))
    finance.consume_tokens(gs, 5)
    assert gs.founder.total_tokens_used == 5
    finance.consume_tokens(gs, 10)
    assert gs.founder.total_tokens_used == 15
    finance.consume_tokens(gs, 0)
    assert gs.founder.total_tokens_used == 15  # zero consume is a no-op


def test_token_milestone_fires():
    gs = _gs(founder=_founder(total_tokens_used=9))
    events = finance.consume_tokens(gs, 2)  # crosses 10 threshold
    assert any("Token Milestone" in e[1] for e in events)
    assert any("Prompt Apprentice" in e[1] for e in events)


def test_token_milestone_not_repeated():
    gs = _gs(founder=_founder(total_tokens_used=15))
    events = finance.consume_tokens(gs, 5)
    # Already past the 10 threshold — no new milestone
    assert not any("Prompt Apprentice" in e[1] for e in events)


# ─────────────────────── REPUTATION ───────────────────────────

def test_reputation_clamped_upper():
    gs = _gs(founder=_founder(reputation=98))
    finance.adjust_reputation(gs, 10)
    assert gs.founder.reputation == 100


def test_reputation_clamped_lower():
    gs = _gs(founder=_founder(reputation=2))
    finance.adjust_reputation(gs, -10)
    assert gs.founder.reputation == 0


def test_reputation_mid_delta():
    gs = _gs(founder=_founder(reputation=50))
    finance.adjust_reputation(gs, 15)
    assert gs.founder.reputation == 65


# ─────────────────────── DISPATCH ACTIONS ─────────────────────

def test_dispatch_deposit_to_company():
    gs = _gs(founder=_founder(personal_cash=500.0))
    c = gs.companies[0]
    c.cash = 1000
    result = dispatch(gs, "deposit_to_company", company_id=0, amount=200)
    assert result.ok
    assert gs.founder.personal_cash == 300.0
    assert c.cash == 1200


def test_dispatch_deposit_insufficient():
    gs = _gs(founder=_founder(personal_cash=100.0))
    result = dispatch(gs, "deposit_to_company", company_id=0, amount=200)
    assert not result.ok


def test_dispatch_withdraw_to_personal():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 3000
    result = dispatch(gs, "withdraw_to_personal", company_id=0, amount=500)
    assert result.ok
    assert c.cash == 2500
    assert gs.founder.personal_cash == 1500.0


def test_dispatch_withdraw_insufficient():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 100
    result = dispatch(gs, "withdraw_to_personal", company_id=0, amount=500)
    assert not result.ok


def test_dispatch_set_auto_deposit():
    gs = _gs()
    c = gs.companies[0]
    assert c.auto_deposit_pct == 0
    result = dispatch(gs, "set_auto_deposit", company_id=0, pct=25)
    assert result.ok
    assert c.auto_deposit_pct == 25


def test_dispatch_toggle_cover_personal():
    gs = _gs()
    c = gs.companies[0]
    assert c.cover_from_personal is False
    result = dispatch(gs, "toggle_cover_personal", company_id=0)
    assert result.ok
    assert c.cover_from_personal is True
    dispatch(gs, "toggle_cover_personal", company_id=0)
    assert c.cover_from_personal is False


def test_dispatch_unknown_action():
    gs = _gs()
    result = dispatch(gs, "nonexistent_action")
    assert not result.ok


# ─────────────────────── VIBE MULTIPLIER ──────────────────────

def test_vibe_multiplier_range():
    gs = _gs(founder=_founder(vibe=0.0))
    assert abs(finance.get_vibe_multiplier(gs) - 0.8) < 0.01
    gs.founder.vibe = 100.0
    assert abs(finance.get_vibe_multiplier(gs) - 1.5) < 0.01


# ─────────────────────── LOAN MONTHLY PAYMENT ─────────────────

def test_loan_deducted_from_net():
    gs = _gs()
    c = gs.companies[0]
    loan = Loan(
        lender="VibeBank", principal=6000, balance=6000,
        rate=0.08, term_months=12, company_id=0,
        monthly_payment=500,
    )
    c.loans = [loan]
    c.cash = 5000
    c.monthly_revenue = 2000
    c.monthly_expenses = 1000
    finance.monthly_settlement(gs)
    # net = 2000 - 1000 - 500 (loan) = 500
    assert c.cash == 5500


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception:
            print(f"  ✗ {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
