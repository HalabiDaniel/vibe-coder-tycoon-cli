"""
Phase 1 — Resource and Finance Core
Monthly settlement, transfers, auto-deposit, vibe/token/reputation helpers.
"""

from ...constants import MONTH_NAMES, TOKEN_MILESTONES
from ...models import GameState, Loan
from ..actions import register, ActionResult


# ─────────────────────── MONTHLY SETTLEMENT ───────────────────


def monthly_settlement(gs: GameState) -> list:
    """Settle all company finances for the current month. Returns events list."""
    events = []
    f = gs.founder
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    for c in gs.active_companies():
        net = c.monthly_revenue - c.monthly_expenses

        # Deduct loan repayments
        for loan in list(c.loans):
            payment = loan.monthly_payment if isinstance(loan, Loan) else loan.get("monthly_payment", 0)
            net -= payment

        if net >= 0:
            c.cash += net
            c.months_negative = 0
            if c.auto_deposit_pct > 0 and net > 0:
                deposit = int(net * c.auto_deposit_pct / 100)
                c.cash -= deposit
                f.personal_cash += deposit
                events.append(
                    ("💰", f"Auto-deposit: +${deposit:,} to personal from {c.name}", "good", date_str)
                )
        else:
            if c.cover_from_personal and f.personal_cash >= abs(net):
                f.personal_cash += net  # net is negative
                c.months_negative = 0
                events.append(
                    ("💸", f"Personal funds covered {c.name} (${abs(net):,})", "warn", date_str)
                )
            else:
                c.cash = max(0, c.cash + net)
                c.months_negative += 1
                events.append(
                    ("⚠️", f"{c.name} cash negative! ({c.months_negative} mo)", "bad", date_str)
                )

        c.valuation = max(0, c.cash + c.monthly_revenue * 12)

    # Vibe passive decay (0.5 per month, floored at 0)
    f.vibe = max(0.0, f.vibe - 0.5)

    return events


# ─────────────────────── RESOURCE HELPERS ─────────────────────


def consume_tokens(gs: GameState, amount: int) -> list:
    """Increment lifetime token count. Returns milestone events if any hit."""
    events = []
    before = gs.founder.total_tokens_used
    gs.founder.total_tokens_used += amount
    after = gs.founder.total_tokens_used
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    for threshold, title in TOKEN_MILESTONES:
        if before < threshold <= after:
            events.append(
                ("🪙", f"Token Milestone: {title} ({threshold:,}K tokens used!)", "good", date_str)
            )
            gs.founder.achievements.append(f"Token: {title}")
    return events


def adjust_reputation(gs: GameState, delta: int) -> None:
    gs.founder.reputation = max(0, min(100, gs.founder.reputation + delta))


def add_vibe(gs: GameState, amount: float) -> None:
    gs.founder.vibe = max(0.0, min(100.0, gs.founder.vibe + amount))


def get_vibe_multiplier(gs: GameState) -> float:
    """High vibe increases speed and chaos. Returns a 0.8–1.5 multiplier."""
    v = gs.founder.vibe / 100.0
    return 0.8 + v * 0.7


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("deposit_to_company")
def _deposit_to_company(gs: GameState, company_id: int, amount: int) -> ActionResult:
    if amount <= 0:
        return ActionResult(ok=False, message="Amount must be positive.")
    f = gs.founder
    if f.personal_cash < amount:
        return ActionResult(ok=False, message=f"Not enough personal cash (${f.personal_cash:,.0f} available).")
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    f.personal_cash -= amount
    c.cash += amount
    return ActionResult(ok=True, message=f"Deposited ${amount:,} to {c.name}.")


@register("withdraw_to_personal")
def _withdraw_to_personal(gs: GameState, company_id: int, amount: int) -> ActionResult:
    if amount <= 0:
        return ActionResult(ok=False, message="Amount must be positive.")
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if c.cash < amount:
        return ActionResult(ok=False, message=f"Not enough company cash (${c.cash:,} available).")
    c.cash -= amount
    gs.founder.personal_cash += amount
    return ActionResult(ok=True, message=f"Withdrew ${amount:,} to personal from {c.name}.")


@register("set_auto_deposit")
def _set_auto_deposit(gs: GameState, company_id: int, pct: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    c.auto_deposit_pct = max(0, min(100, pct))
    if c.auto_deposit_pct == 0:
        return ActionResult(ok=True, message=f"Auto-deposit disabled for {c.name}.")
    return ActionResult(ok=True, message=f"Auto-deposit set to {c.auto_deposit_pct}% for {c.name}.")


@register("toggle_cover_personal")
def _toggle_cover_personal(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    c.cover_from_personal = not c.cover_from_personal
    state = "enabled" if c.cover_from_personal else "disabled"
    return ActionResult(ok=True, message=f"Cover-from-personal {state} for {c.name}.")


@register("consume_tokens")
def _consume_tokens_action(gs: GameState, amount: int) -> ActionResult:
    events = consume_tokens(gs, amount)
    return ActionResult(ok=True, message=f"Consumed {amount:,}K tokens.", events=events)


@register("adjust_reputation")
def _adjust_reputation_action(gs: GameState, delta: int) -> ActionResult:
    before = gs.founder.reputation
    adjust_reputation(gs, delta)
    return ActionResult(ok=True, message=f"Reputation: {before} → {gs.founder.reputation}")


@register("add_vibe")
def _add_vibe_action(gs: GameState, amount: float) -> ActionResult:
    before = gs.founder.vibe
    add_vibe(gs, amount)
    return ActionResult(ok=True, message=f"Vibe: {before:.0f} → {gs.founder.vibe:.0f}")
