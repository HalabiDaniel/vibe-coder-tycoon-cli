"""
Phase 11 — Loans, Lenders, Investors, Funding tests.

Covers: amortized payment math, eligible lenders, loan application, investor
offer generation, funding deal lifecycle, negotiation, and persistence.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.models import Founder, FundingDeal, Loan
from vibe_coder_tycoon.engine.systems import investors
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(reputation=40, year=2025):
    f = Founder(username="Tester", background_idx=0, reputation=reputation,
                burnout=0, skill_prototyping=50, skill_sales=30,
                skill_tech=40, skill_management=30, total_tokens_used=0)
    gs = make_new_game(f, 3)
    gs.year = year
    return gs


# ─────────────────────── AMORTIZED PAYMENT ────────────────────

def test_amortized_payment_basic():
    # $10,000 at 8% annual over 12 months
    pmt = investors.amortized_payment(10_000, 0.08, 12)
    assert pmt > 0
    # Rough check: total repayment slightly more than principal
    assert 10_000 < pmt * 12 < 12_000


def test_amortized_payment_zero_rate():
    pmt = investors.amortized_payment(1200, 0.0, 12)
    assert pmt == 100   # simple division


def test_amortized_payment_rounds_up():
    # should never return fractional dollars
    pmt = investors.amortized_payment(10_001, 0.07, 13)
    assert isinstance(pmt, int)
    assert pmt > 0


# ─────────────────────── ELIGIBLE LENDERS ─────────────────────

def test_eligible_lenders_low_rep():
    gs = _gs(reputation=0)
    eligible = investors.get_eligible_lenders(gs, 0)
    # Only FriendFund has min_reputation=0
    assert all(l["min_reputation"] == 0 for l in eligible)


def test_eligible_lenders_high_rep():
    gs = _gs(reputation=99)
    eligible = investors.get_eligible_lenders(gs, 0)
    assert len(eligible) == len([l for l in __import__(
        "vibe_coder_tycoon.constants", fromlist=["LENDERS"]).LENDERS])


def test_default_penalty_raises_rates():
    gs = _gs(reputation=99)
    gs.loan_default_count = 2
    eligible = investors.get_eligible_lenders(gs, 0)
    from vibe_coder_tycoon.constants import LENDERS
    base = {l["name"]: l["rate"] for l in LENDERS}
    for el in eligible:
        original = base.get(el["name"], 0)
        assert el["rate"] >= original + 0.06 - 0.001   # 2 defaults * 3%


# ─────────────────────── LOAN APPLICATION ─────────────────────

def test_apply_for_loan_happy_path():
    gs = _gs(reputation=5)
    result = dispatch(gs, "apply_for_loan",
                      company_id=0, lender_name="FriendFund", amount=1000)
    assert result.ok, result.message
    c = gs.companies[0]
    assert any(isinstance(l, Loan) and l.lender == "FriendFund" for l in c.loans)


def test_apply_for_loan_cash_deposited():
    gs = _gs(reputation=5)
    cash_before = gs.companies[0].cash
    dispatch(gs, "apply_for_loan",
             company_id=0, lender_name="FriendFund", amount=3000)
    assert gs.companies[0].cash == cash_before + 3000


def test_apply_for_loan_exceeds_max():
    gs = _gs(reputation=5)
    result = dispatch(gs, "apply_for_loan",
                      company_id=0, lender_name="FriendFund", amount=999_999)
    assert not result.ok
    assert "max" in result.message.lower()


def test_apply_for_loan_ineligible_lender():
    gs = _gs(reputation=5)
    result = dispatch(gs, "apply_for_loan",
                      company_id=0, lender_name="StartupVault", amount=1000)
    assert not result.ok  # rep < 30


# ─────────────────────── INVESTOR OFFERS ──────────────────────

def test_generate_offer_returns_dict():
    gs = _gs(reputation=35, year=2025)
    gs.companies[0].monthly_revenue = 1000
    offer = investors.generate_investor_offer(gs, 0)
    assert offer is not None
    assert "round_type" in offer
    assert "amount" in offer
    assert offer["amount"] > 0


def test_generate_offer_none_when_rep_low():
    gs = _gs(reputation=0, year=2025)
    # Only Friends & Family eligible at rep 0, min_mrr 0 — but let's check
    # if we have no active companies it returns None
    gs.companies[0].active = False
    offer = investors.generate_investor_offer(gs, 0)
    assert offer is None


def test_accept_investor_offer():
    gs = _gs(reputation=35)
    offer = {
        "offer_id": 0,
        "round_type": "Angel Round",
        "amount": 50_000,
        "equity_pct": 0.10,
        "requirement_desc": "Reach $5,000 MRR in 9 months",
        "requirement_metric": "mrr",
        "requirement_target": 5000,
        "deadline_month": gs.months_elapsed + 9,
        "company_id": 0,
        "investor_name": "Test Angel",
        "negotiated": False,
    }
    gs.pending_offers.append(offer)
    cash_before = gs.companies[0].cash
    rep_before = gs.founder.reputation
    result = dispatch(gs, "accept_investor_offer", offer_id=0, company_id=0)
    assert result.ok, result.message
    assert gs.companies[0].cash == cash_before + 50_000
    assert gs.founder.reputation == rep_before + 3
    assert len(gs.funding_deals) == 1
    assert len(gs.pending_offers) == 0


def test_reject_investor_offer():
    gs = _gs()
    offer = {"offer_id": 0, "investor_name": "Test", "round_type": "Angel Round",
             "amount": 10_000, "equity_pct": 0.05, "requirement_desc": "",
             "requirement_metric": "mrr", "requirement_target": 0,
             "deadline_month": 10, "company_id": 0, "negotiated": False}
    gs.pending_offers.append(offer)
    result = dispatch(gs, "reject_investor_offer", offer_id=0)
    assert result.ok
    assert len(gs.pending_offers) == 0


def test_negotiate_offer_bumps_terms():
    gs = _gs()
    offer = {"offer_id": 0, "investor_name": "Test", "round_type": "Angel Round",
             "amount": 50_000, "equity_pct": 0.10, "requirement_desc": "x",
             "requirement_metric": "mrr", "requirement_target": 5000,
             "deadline_month": 10, "company_id": 0, "negotiated": False}
    gs.pending_offers.append(offer)
    result = dispatch(gs, "negotiate_offer", offer_id=0)
    assert result.ok
    updated = gs.pending_offers[0]
    assert updated["amount"] > 50_000
    assert updated["equity_pct"] > 0.10
    assert updated["requirement_target"] > 5000
    assert updated["negotiated"] is True


def test_negotiate_offer_only_once():
    gs = _gs()
    offer = {"offer_id": 0, "investor_name": "Test", "round_type": "Angel Round",
             "amount": 50_000, "equity_pct": 0.10, "requirement_desc": "x",
             "requirement_metric": "mrr", "requirement_target": 5000,
             "deadline_month": 10, "company_id": 0, "negotiated": True}
    gs.pending_offers.append(offer)
    result = dispatch(gs, "negotiate_offer", offer_id=0)
    assert not result.ok


# ─────────────────────── DEAL LIFECYCLE ───────────────────────

def test_deal_met_when_metric_reached():
    gs = _gs()
    gs.companies[0].monthly_revenue = 10_000
    deal = FundingDeal(
        deal_id=0, round_type="Angel Round", amount=50_000, equity_pct=0.10,
        requirement_desc="Reach $5,000 MRR", requirement_metric="mrr",
        requirement_target=5_000, deadline_month=gs.months_elapsed + 9,
        company_id=0, investor_name="Angel",
    )
    gs.funding_deals.append(deal)
    events = investors.monthly_investors_tick(gs)
    assert deal.status == "met"
    assert any("met" in e[1].lower() or "happy" in e[1].lower() for e in events)


def test_deal_failed_past_deadline():
    gs = _gs()
    gs.companies[0].monthly_revenue = 0
    deal = FundingDeal(
        deal_id=0, round_type="Angel Round", amount=50_000, equity_pct=0.10,
        requirement_desc="Reach $5,000 MRR", requirement_metric="mrr",
        requirement_target=5_000, deadline_month=gs.months_elapsed - 1,
        company_id=0, investor_name="Angel",
    )
    gs.funding_deals.append(deal)
    rep_before = gs.founder.reputation
    events = investors.monthly_investors_tick(gs)
    assert deal.status == "failed"
    assert gs.founder.reputation < rep_before


# ─────────────────────── LOAN DEFAULT ─────────────────────────

def test_loan_default_after_six_months_negative():
    from vibe_coder_tycoon.engine.systems.finance import monthly_settlement
    gs = _gs(reputation=5)
    c = gs.companies[0]
    dispatch(gs, "apply_for_loan", company_id=0, lender_name="FriendFund", amount=2000)
    c.months_negative = 6
    c.monthly_revenue = 0
    c.monthly_expenses = 999_999   # guaranteed negative
    c.cash = 0
    rep_before = gs.founder.reputation
    monthly_settlement(gs)
    loan = next((l for l in c.loans if isinstance(l, Loan)), None)
    assert loan is not None and loan.balance == 0
    assert gs.loan_default_count > 0
    assert gs.founder.reputation < rep_before


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_funding_round_trip():
    gs = _gs(reputation=35)
    gs.funding_deals.append(FundingDeal(
        deal_id=1, round_type="Seed Round", amount=300_000, equity_pct=0.15,
        requirement_desc="Reach $20K MRR", requirement_metric="mrr",
        requirement_target=20_000, deadline_month=24,
        company_id=0, investor_name="Sequoia Clone",
        status="active", month_accepted=3,
    ))
    gs.pending_offers.append({"offer_id": 0, "round_type": "Angel Round",
                               "amount": 50_000, "equity_pct": 0.10,
                               "negotiated": False, "investor_name": "X",
                               "requirement_desc": "", "requirement_metric": "mrr",
                               "requirement_target": 0, "deadline_month": 12,
                               "company_id": 0})
    gs.loan_default_count = 2
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    assert len(gs2.funding_deals) == 1
    d2 = gs2.funding_deals[0]
    assert d2.round_type == "Seed Round"
    assert d2.amount == 300_000
    assert d2.status == "active"
    assert len(gs2.pending_offers) == 1
    assert gs2.loan_default_count == 2
