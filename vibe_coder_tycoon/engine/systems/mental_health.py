"""
Phase 6 — Mental Health and Founder Wellbeing

Per-month sanity drain/recovery for employees and the founder, threshold-based
named conditions, the Touch Grass rotation (employees leave ~1 month and return
automatically), and the founder-sanity → global-negative-event link.

The monthly model compresses the GDD's day-level "1-2 weeks" Touch Grass window
into roughly one settlement cycle, matching the rest of the engine's cadence.
"""

import random

from ...constants import (
    CONDITIONS, FOUNDER_CONDITIONS, MONTH_NAMES,
    TEAM_RECHARGE_COST, INSPIRE_VIBE_COST, DISTRACTION_COST,
)
from ...models import GameState
from ..actions import register, ActionResult
from .finance import add_vibe


# ─────────────────────── CONTRIBUTION MULTIPLIER ──────────────


def employee_stat_mult(emp) -> float:
    """How much a condition scales an employee's work output. Used by the
    development team-bonus math (Phase 2/5)."""
    cond = CONDITIONS.get(emp.condition)
    if cond is None:
        return 1.0
    return cond.get("stat_mult", 1.0)


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_tick(gs: GameState) -> list:
    """Settle mental health for the month. Returns event tuples."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    f = gs.founder

    # Founder vibe heavily colours the whole studio's mood.
    vibe = f.vibe
    high_vibe = vibe >= 90

    for emp in gs.employees:
        # Touch Grass: skip them, return when the timer elapses.
        if emp.state == "touch_grass":
            if gs.months_elapsed >= emp.state_until:
                emp.state = "active"
                emp.sanity = max(emp.sanity, 45)
                emp.condition = ""
                emp.condition_until = 0
                events.append(("🌱", f"{emp.name} returned from Touch Grass, refreshed.",
                               "good", date_str))
            continue

        assigned = (0 <= emp.assigned_project_id < len(gs.projects))
        drain = 0
        if assigned:
            p = gs.projects[emp.assigned_project_id]
            drain = 4
            if vibe >= 70:
                drain += (vibe - 70) / 8.0           # chaotic environment
            drain += min(6, p.bug_count * 0.5)        # buggy projects are stressful
        else:
            # Resting between projects recovers sanity.
            drain = -7

        if high_vibe:
            drain += 5                                 # Startup Mania burns people out

        emp.sanity = int(max(0, min(100, emp.sanity - drain)))

        # ── Evaluate conditions ────────────────────────────────
        new_cond = _eval_employee_condition(gs, emp, high_vibe)
        if new_cond != emp.condition:
            emp.condition = new_cond
            if new_cond:
                events.append(("🧠", f"{emp.name}: {new_cond} ({CONDITIONS[new_cond]['effect']}).",
                               "bad" if CONDITIONS[new_cond]["stat_mult"] < 1 else "warn", date_str))

        # ── Touch Grass at zero sanity ─────────────────────────
        if emp.sanity <= 0 and emp.state == "active":
            emp.state = "touch_grass"
            emp.state_until = gs.months_elapsed + 1
            emp.condition = "Burnout"
            emp.assigned_project_id = -1
            events.append(("🌴", f"{emp.name} hit zero sanity — gone to Touch Grass for a while.",
                           "bad", date_str))

    # ── Founder wellbeing ─────────────────────────────────────
    events.extend(_founder_tick(gs, date_str))
    return events


def _eval_employee_condition(gs: GameState, emp, high_vibe: bool) -> str:
    """Return the condition name an employee should currently have ("" = none).
    Timed conditions (Framework Fatigue / AI Doom Spiral) persist until their
    timer clears; threshold conditions follow sanity directly."""
    # Persist a still-running timed condition.
    if emp.condition in ("Framework Fatigue", "AI Doom Spiral"):
        if gs.months_elapsed < emp.condition_until:
            return emp.condition

    if emp.sanity < 10:
        return "Existential Crisis"
    if emp.sanity < 20:
        return "Burnout"
    if high_vibe:
        return "Startup Mania"

    # Rare research-driven doom spiral.
    if emp.research >= 65 and random.random() < 0.04:
        emp.condition_until = gs.months_elapsed + 1
        return "AI Doom Spiral"
    return ""


def _founder_tick(gs: GameState, date_str: str) -> list:
    events = []
    f = gs.founder

    drain = 0
    # Idle (no in-dev projects) lets the founder recover a little.
    in_dev = any(p.status == "In Dev" for p in gs.projects)
    drain += 2 if in_dev else -4
    if f.vibe >= 80:
        drain += 3
    # Company cash crises grind the founder down.
    for c in gs.active_companies():
        if c.months_negative > 0:
            drain += 2
    f.sanity = int(max(0, min(100, f.sanity - drain)))

    # Founder conditions
    conds = []
    if f.sanity < 15:
        conds.append("Doom Scrolling")
    elif f.sanity < 25:
        conds.append("Founder Burnout")
    if conds != f.conditions:
        f.conditions = conds
        if conds:
            events.append(("😵", f"Founder condition: {conds[0]} — {FOUNDER_CONDITIONS[conds[0]]['effect']}.",
                           "bad", date_str))

    # Low founder sanity raises global negative-event probability.
    neg_chance = max(0.0, (40 - f.sanity) / 100.0)
    if neg_chance > 0 and random.random() < neg_chance:
        bad = random.choice([
            "A careless 2am deploy took a product down for an hour.",
            "You snapped at a customer on social. Screenshots are circulating.",
            "Decision paralysis cost you a launch window.",
            "You forgot to renew a domain. Brief panic ensued.",
        ])
        from .finance import adjust_reputation
        adjust_reputation(gs, -2)
        events.append(("⚠️", f"Low-sanity slip: {bad} (Rep -2)", "bad", date_str))

    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("team_recharge")
def _team_recharge(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if c.cash < TEAM_RECHARGE_COST:
        return ActionResult(ok=False,
                            message=f"Need ${TEAM_RECHARGE_COST:,} (company has ${c.cash:,}).")
    team = [e for e in gs.employees_for_company(company_id) if e.state == "active"]
    if not team:
        return ActionResult(ok=False, message="No active employees to recharge.")
    c.cash -= TEAM_RECHARGE_COST
    for e in team:
        e.sanity = min(100, e.sanity + 25)
        e.mood = min(100, e.mood + 15)
        if e.condition in ("Burnout", "Existential Crisis"):
            e.condition = ""
    return ActionResult(ok=True,
                        message=f"Team Recharge: {len(team)} staff at {c.name} feel human again.")


@register("inspirational_talk")
def _inspirational_talk(gs: GameState, emp_index: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    if gs.founder.vibe < INSPIRE_VIBE_COST:
        return ActionResult(ok=False,
                            message=f"Need {INSPIRE_VIBE_COST:.0f} Vibe to give a talk.")
    e = gs.employees[emp_index]
    add_vibe(gs, -INSPIRE_VIBE_COST)
    e.sanity = min(100, e.sanity + 20)
    resolved = ""
    if e.condition in ("Existential Crisis", "Burnout"):
        resolved = f" Resolved {e.condition}."
        e.condition = ""
    return ActionResult(ok=True, message=f"{e.name} feels seen.{resolved}")


@register("distraction")
def _distraction(gs: GameState, emp_index: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    e = gs.employees[emp_index]
    c = gs.company_by_id(e.company_id)
    if c is None or c.cash < DISTRACTION_COST:
        return ActionResult(ok=False, message=f"Need ${DISTRACTION_COST:,} in company cash.")
    c.cash -= DISTRACTION_COST
    e.sanity = min(100, e.sanity + 10)
    msg = "Took the mind off it."
    if e.condition == "AI Doom Spiral":
        e.condition = ""
        e.condition_until = 0
        msg = "Snapped out of the AI Doom Spiral."
    return ActionResult(ok=True, message=f"{e.name}: {msg}")


@register("founder_take_break")
def _founder_take_break(gs: GameState) -> ActionResult:
    f = gs.founder
    f.sanity = min(100, f.sanity + 25)
    f.burnout = max(0, f.burnout - 20)
    add_vibe(gs, -10.0)
    f.conditions = []
    return ActionResult(ok=True, message="You took a real break. Sanity restored, Vibe cooled.")
