"""
Phase 11 — Loans, Lenders, Investors, Funding

Investor offers are generated probabilistically each month based on reputation
and company MRR. Accepted deals become FundingDeals with requirements the
company must hit within a deadline. Existing LENDERS are accessible via
apply_for_loan. Loan defaults triggered by bankruptcy-adjacent months are
tracked and penalise future rates.
"""

import random
import math

from ...constants import LENDERS, FUNDING_ROUNDS, INVESTOR_NAMES, MONTH_NAMES
from ...models import GameState, Loan, FundingDeal
from ..actions import register, ActionResult
from .finance import adjust_reputation


# ─────────────────────── LENDER HELPERS ───────────────────────


def get_eligible_lenders(gs: GameState, company_id: int) -> list:
    """Return LENDERS the founder qualifies for. Defaults raise rates."""
    rep = gs.founder.reputation
    defaults = getattr(gs, "loan_default_count", 0)
    out = []
    for lender in LENDERS:
        if rep >= lender["min_reputation"]:
            entry = dict(lender)
            if defaults > 0:
                entry["rate"] = round(entry["rate"] + 0.03 * defaults, 4)
            out.append(entry)
    return out


def amortized_payment(principal: int, annual_rate: float, term_months: int) -> int:
    """Standard amortizing monthly payment, rounded up to nearest dollar."""
    if annual_rate <= 0 or term_months <= 0:
        return max(1, principal // max(1, term_months))
    r = annual_rate / 12.0
    payment = principal * r / (1 - (1 + r) ** (-term_months))
    return max(1, math.ceil(payment))


# ─────────────────────── INVESTOR OFFER GENERATION ────────────


def _company_mrr(gs: GameState, c) -> int:
    return c.monthly_revenue


def _company_metric(gs: GameState, c, metric: str) -> int:
    if metric == "mrr":
        return _company_mrr(gs, c)
    if metric == "revenue":
        return sum(p.lifetime_revenue for p in gs.projects if p.company_id == c.id)
    if metric == "users":
        return sum(p.active_users for p in gs.projects
                   if p.company_id == c.id and p.status in ("Launched", "Growing"))
    return 0


def generate_investor_offer(gs: GameState, company_id: int) -> dict | None:
    """Build a random eligible offer dict (not yet a FundingDeal)."""
    c = gs.company_by_id(company_id)
    if c is None or not c.active:
        return None
    rep = gs.founder.reputation
    mrr = _company_mrr(gs, c)

    eligible = [
        r for r in FUNDING_ROUNDS
        if (rep >= r["min_reputation"]
            and mrr >= r["min_mrr"]
            and gs.year >= r["min_year"])
    ]
    if not eligible:
        return None

    # Weight towards the highest-tier eligible round (more interesting)
    rnd = random.choices(eligible, weights=[i + 1 for i in range(len(eligible))])[0]
    lo, hi = rnd["amount_range"]
    amount = random.randint(lo, hi)
    eq_lo, eq_hi = rnd["equity_range"]
    equity_pct = round(random.uniform(eq_lo, eq_hi), 3)
    target = int(amount * rnd["req_multiplier"] / rnd["req_months"])
    deadline = gs.months_elapsed + rnd["req_months"]
    investor = random.choice(INVESTOR_NAMES)

    return {
        "offer_id":         len(gs.pending_offers),
        "round_type":       rnd["name"],
        "amount":           amount,
        "equity_pct":       equity_pct,
        "requirement_desc": (
            f"Reach ${target:,}/{rnd['req_metric'].upper()}/mo within "
            f"{rnd['req_months']} months"
        ),
        "requirement_metric": rnd["req_metric"],
        "requirement_target": target,
        "deadline_month":     deadline,
        "company_id":         company_id,
        "investor_name":      investor,
        "negotiated":         False,
    }


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_investors_tick(gs: GameState) -> list:
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    # Check active funding deals
    for deal in list(gs.funding_deals):
        if deal.status != "active":
            continue
        c = gs.company_by_id(deal.company_id)
        actual = _company_metric(gs, c, deal.requirement_metric) if c else 0

        if actual >= deal.requirement_target:
            deal.status = "met"
            events.append((
                "🎉",
                f"Funding requirement met for '{deal.round_type}'! {deal.investor_name} is happy.",
                "good", date_str,
            ))
        elif gs.months_elapsed > deal.deadline_month:
            deal.status = "failed"
            adjust_reputation(gs, -10)
            penalty = int(deal.amount * 0.20)
            if c and c.active:
                c.cash = max(0, c.cash - penalty)
            events.append((
                "💔",
                (f"Funding deal with {deal.investor_name} failed! "
                 f"-10 rep, ${penalty:,} penalty."),
                "bad", date_str,
            ))

    # Randomly generate new investor offers
    active = gs.active_companies()
    if (len(gs.pending_offers) < 2
            and gs.founder.reputation >= 30
            and active
            and random.random() < 0.15):
        best = max(active, key=lambda c: _company_mrr(gs, c))
        offer = generate_investor_offer(gs, best.id)
        if offer:
            offer["offer_id"] = len(gs.pending_offers)
            gs.pending_offers.append(offer)
            events.append((
                "📬",
                (f"Investor offer from {offer['investor_name']}! "
                 f"{offer['round_type']}: ${offer['amount']:,} for "
                 f"{offer['equity_pct']:.0%} equity."),
                "good", date_str,
            ))

    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("apply_for_loan")
def _apply_for_loan(
    gs: GameState, company_id: int, lender_name: str, amount: int
) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    eligible = get_eligible_lenders(gs, company_id)
    lender = next((l for l in eligible if l["name"] == lender_name), None)
    if lender is None:
        return ActionResult(ok=False, message=f"Lender '{lender_name}' not eligible or not found.")
    if amount <= 0:
        return ActionResult(ok=False, message="Amount must be positive.")
    if amount > lender["max_amount"]:
        return ActionResult(ok=False,
                            message=f"Max loan from {lender_name} is ${lender['max_amount']:,}.")
    monthly = amortized_payment(amount, lender["rate"], lender["term_months"])
    loan = Loan(
        lender=lender_name,
        principal=amount,
        balance=amount,
        rate=lender["rate"],
        term_months=lender["term_months"],
        company_id=company_id,
        monthly_payment=monthly,
    )
    c.loans.append(loan)
    c.cash += amount
    return ActionResult(
        ok=True,
        message=(
            f"Loan approved! ${amount:,} at {lender['rate']:.0%}/yr, "
            f"${monthly:,}/mo for {lender['term_months']} months."
        ),
    )


@register("accept_investor_offer")
def _accept_investor_offer(
    gs: GameState, offer_id: int, company_id: int
) -> ActionResult:
    offer = next((o for o in gs.pending_offers if o["offer_id"] == offer_id), None)
    if offer is None:
        return ActionResult(ok=False, message="Offer not found.")
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")

    deal = FundingDeal(
        deal_id=len(gs.funding_deals),
        round_type=offer["round_type"],
        amount=offer["amount"],
        equity_pct=offer["equity_pct"],
        requirement_desc=offer["requirement_desc"],
        requirement_metric=offer["requirement_metric"],
        requirement_target=offer["requirement_target"],
        deadline_month=offer["deadline_month"],
        company_id=company_id,
        investor_name=offer["investor_name"],
        status="active",
        month_accepted=gs.months_elapsed,
    )
    gs.funding_deals.append(deal)
    gs.pending_offers = [o for o in gs.pending_offers if o["offer_id"] != offer_id]
    c.cash += offer["amount"]
    adjust_reputation(gs, 3)
    return ActionResult(
        ok=True,
        message=(
            f"Accepted {offer['round_type']} from {offer['investor_name']}! "
            f"${offer['amount']:,} deposited. +3 rep."
        ),
    )


@register("reject_investor_offer")
def _reject_investor_offer(gs: GameState, offer_id: int) -> ActionResult:
    offer = next((o for o in gs.pending_offers if o["offer_id"] == offer_id), None)
    if offer is None:
        return ActionResult(ok=False, message="Offer not found.")
    gs.pending_offers = [o for o in gs.pending_offers if o["offer_id"] != offer_id]
    return ActionResult(ok=True, message=f"Rejected offer from {offer['investor_name']}.")


@register("negotiate_offer")
def _negotiate_offer(gs: GameState, offer_id: int) -> ActionResult:
    offer = next((o for o in gs.pending_offers if o["offer_id"] == offer_id), None)
    if offer is None:
        return ActionResult(ok=False, message="Offer not found.")
    if offer.get("negotiated"):
        return ActionResult(ok=False, message="Already negotiated once — take it or leave it.")
    offer["amount"] = int(offer["amount"] * 1.30)
    offer["equity_pct"] = round(offer["equity_pct"] + 0.03, 3)
    offer["requirement_target"] = int(offer["requirement_target"] * 1.40)
    offer["negotiated"] = True
    offer["requirement_desc"] = (
        f"Reach ${offer['requirement_target']:,}/"
        f"{offer['requirement_metric'].upper()}/mo by deadline"
    )
    return ActionResult(
        ok=True,
        message=(
            f"Negotiated up! Now ${offer['amount']:,} at "
            f"{offer['equity_pct']:.0%} equity. Requirement raised."
        ),
    )
