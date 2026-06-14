"""
Phase 14 — Victory, Bankruptcy, Endgame
GDD §24, §25.

Closes the gameplay loop:
- Milestone achievements fire once and persist on the founder profile.
- Companies that run negative for too long go bankrupt (close, discontinue
  products, lose employees, default loans, log to the graveyard).
- The player wins as a trillionaire (net worth) or via the Token Singularity.
- The player loses (game over) after staying fully insolvent for a year.

`endgame_tick(gs)` is the single entry point called once per monthly settlement
from `advance_month`. All randomness-free; safe to call repeatedly.
"""

from ...constants import (
    MONTH_NAMES, MILESTONES, BANKRUPTCY_MONTHS, GAME_OVER_MONTHS,
    TRILLIONAIRE_THRESHOLD, TOKEN_SINGULARITY_THRESHOLD,
)
from ...models import GameState, Loan
from ..actions import register, ActionResult
from .stocks import net_worth
from .finance import adjust_reputation


def _date_str(gs: GameState) -> str:
    return f"{MONTH_NAMES[gs.month - 1]} {gs.year}"


# ─────────────────────── MILESTONE METRICS ────────────────────


def _launched_count(gs: GameState) -> int:
    return len([p for p in gs.projects if p.status != "In Dev"])


def _metric_value(gs: GameState, metric: str) -> float:
    if metric == "companies":
        return len(gs.companies)
    if metric == "employees":
        return len(gs.employees)
    if metric == "launched":
        return _launched_count(gs)
    if metric == "lifetime_revenue":
        return sum(p.lifetime_revenue for p in gs.projects)
    if metric == "net_worth":
        return net_worth(gs)
    if metric == "public_companies":
        return len([c for c in gs.companies if getattr(c, "is_public", False)])
    if metric == "player_models":
        return len(gs.player_models)
    if metric == "templates":
        return len(gs.templates)
    return 0


def check_milestones(gs: GameState) -> list:
    """Fire any milestones whose metric has crossed its target. Persist on the
    founder profile (achievements). Returns event tuples for the news feed."""
    events = []
    f = gs.founder
    if f is None:
        return events
    date_str = _date_str(gs)
    for m in MILESTONES:
        if m["title"] in f.achievements:
            continue
        if _metric_value(gs, m["metric"]) >= m["target"]:
            f.achievements.append(m["title"])
            events.append(
                ("🏅", f"Milestone unlocked: {m['title']} — {m['desc']}", "good", date_str)
            )
    return events


# ─────────────────────── BANKRUPTCY ───────────────────────────


def process_bankruptcies(gs: GameState) -> list:
    """Close any company that has been negative for BANKRUPTCY_MONTHS without a
    bailout. Discontinues products, lets staff go, defaults loans, and writes a
    graveyard record."""
    events = []
    date_str = _date_str(gs)

    for c in list(gs.active_companies()):
        if c.months_negative < BANKRUPTCY_MONTHS:
            continue

        # Tally what we lose for the graveyard record.
        company_projects = gs.projects_for_company(c.id)
        company_emps = gs.employees_for_company(c.id)
        products_lost = [p.name for p in company_projects if not p.discontinued]
        staff_lost = len(company_emps)
        lifetime_rev = sum(p.lifetime_revenue for p in company_projects)

        # Discontinue every product the company owned.
        for p in company_projects:
            if not p.discontinued:
                p.discontinued = True
                p.status = "Sunset"
                p.active_users = 0
                p.users = 0
                p.revenue = 0

        # Let the whole team go.
        gs.employees = [e for e in gs.employees if e.company_id != c.id]

        # Default any outstanding loans (debt does not transfer to personal).
        for loan in list(c.loans):
            bal = loan.balance if isinstance(loan, Loan) else loan.get("balance", 0)
            if bal > 0:
                if isinstance(loan, Loan):
                    loan.balance = 0
                else:
                    loan["balance"] = 0
                gs.loan_default_count = getattr(gs, "loan_default_count", 0) + 1
                adjust_reputation(gs, -8)
                events.append(
                    ("💀", f"Loan defaulted as {c.name} folded. -8 rep.", "bad", date_str)
                )

        # Fail any active funding deals tied to this company.
        for deal in gs.funding_deals:
            if deal.company_id == c.id and deal.status == "active":
                deal.status = "failed"

        # Close the company and write its tombstone.
        c.active = False
        c.cash = 0
        c.monthly_revenue = 0
        record = {
            "name": c.name,
            "founded_year": c.founded_year,
            "closed_year": gs.year,
            "closed_month": gs.month,
            "products": products_lost,
            "staff_lost": staff_lost,
            "lifetime_revenue": lifetime_rev,
            "cause": "Bankruptcy",
        }
        gs.graveyard.append(record)
        c.history.append(f"Bankrupt in {date_str} after {c.months_negative} months underwater.")
        adjust_reputation(gs, -5)
        events.append(
            ("🪦", f"{c.name} went bankrupt — products sunset, {staff_lost} let go.", "bad", date_str)
        )

    return events


# ─────────────────────── WIN / LOSE ───────────────────────────


def _is_insolvent_month(gs: GameState) -> bool:
    """True if the player is fully broke this month: no personal cash and no
    company that is staying cash-positive."""
    f = gs.founder
    personal_broke = (f is None) or (f.personal_cash <= 0)
    actives = gs.active_companies()
    if not actives:
        companies_broke = True
    else:
        companies_broke = all(c.months_negative > 0 for c in actives)
    return personal_broke and companies_broke


def check_endgame(gs: GameState) -> list:
    """Update peak net worth, then evaluate victory and game-over conditions."""
    events = []
    date_str = _date_str(gs)

    nw = net_worth(gs)
    if nw > gs.peak_net_worth:
        gs.peak_net_worth = nw

    # ── Victory (continue-after-win allowed; only announced once) ──
    if not gs.victory:
        if nw >= TRILLIONAIRE_THRESHOLD:
            gs.victory = True
            gs.victory_type = "trillionaire"
            events.append(
                ("🏆", "TRILLIONAIRE! Net worth crossed $1,000,000,000,000.", "good", date_str)
            )
        elif gs.founder and gs.founder.total_tokens_used >= TOKEN_SINGULARITY_THRESHOLD:
            gs.victory = True
            gs.victory_type = "token_singularity"
            events.append(
                ("🌌", "TOKEN SINGULARITY! 1e12 lifetime tokens consumed.", "good", date_str)
            )

    # ── Game over (insolvent for a full year) ──
    if not gs.game_over:
        if _is_insolvent_month(gs):
            gs.broke_months += 1
            if gs.broke_months >= GAME_OVER_MONTHS:
                gs.game_over = True
                gs.game_over_reason = (
                    f"Insolvent for {gs.broke_months} consecutive months."
                )
                events.append(
                    ("☠️", "GAME OVER — the empire ran out of runway.", "bad", date_str)
                )
        else:
            gs.broke_months = 0

    return events


# ─────────────────────── ENTRY POINT ──────────────────────────


def endgame_tick(gs: GameState) -> list:
    """Run all Phase 14 settlement: bankruptcies, then win/lose, then milestones.
    Order matters: bankruptcies adjust net worth before the victory check, and
    milestones run last so end-state changes are reflected."""
    events = []
    events.extend(process_bankruptcies(gs))
    events.extend(check_endgame(gs))
    events.extend(check_milestones(gs))
    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("continue_after_win")
def _continue_after_win(gs: GameState) -> ActionResult:
    if not gs.victory:
        return ActionResult(ok=False, message="No victory to continue from.")
    gs.endgame_continue = True
    return ActionResult(ok=True, message="Continuing the empire after victory.")
