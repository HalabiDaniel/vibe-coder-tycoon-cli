"""
Phase 10 — Player-Built AI Models

Players train custom models using axis sliders (Coding, Reasoning, Creativity,
Speed, Context, Multimodal). Training costs cash, tokens, and real in-game
time. Finished models can be licensed for monthly API revenue or used in
dev sessions just like catalog models.
"""

from ...constants import (
    AI_MODEL_AXES, AXIS_POINT_BUDGET,
    AI_MODEL_TRAINING_COST_PER_POINT, AI_MODEL_TRAINING_DAYS_PER_POINT,
    AI_MODEL_TOKEN_COST_PER_POINT, AI_MODEL_LICENSE_BASE_REVENUE,
    PLAYER_MODEL_UNLOCK, MONTH_NAMES,
)
from ...models import GameState, AIModel
from ..actions import register, ActionResult
from .finance import consume_tokens, adjust_reputation


# ─────────────────────── CAPABILITY MATH ──────────────────────


def compute_capability(axes: dict) -> float:
    """Weighted average of axis values, scaled to 0–10."""
    total = sum(
        axes.get(ax["name"], 0) * ax["weight"]
        for ax in AI_MODEL_AXES
    )
    max_total = AXIS_POINT_BUDGET * max(ax["weight"] for ax in AI_MODEL_AXES)
    # Normalise against what a perfect single-axis allocation would give.
    # A full 30-point budget spread proportionally gives a score of 10.
    normalised = total / (AXIS_POINT_BUDGET * sum(ax["weight"] for ax in AI_MODEL_AXES)) * 10.0
    return round(min(10.0, max(0.0, normalised)), 2)


# ─────────────────────── UNLOCK CHECK ─────────────────────────


def check_unlock(gs: GameState, company_id: int):
    """Return (ok: bool, reason: str)."""
    c = gs.company_by_id(company_id)
    if c is None:
        return False, "Company not found."
    req = PLAYER_MODEL_UNLOCK
    if c.focus_area != "AI Tools":
        return False, "Company focus must be AI Tools."
    if c.office_level < req["min_office_level"]:
        return False, f"Need Office Level {req['min_office_level']} (have {c.office_level})."
    if gs.year < req["min_year"]:
        return False, f"Available from {req['min_year']} (currently {gs.year})."
    if c.datacenter_tier < req["min_datacenter_tier"]:
        return False, f"Need Datacenter Tier {req['min_datacenter_tier']}."
    team = gs.employees_for_company(company_id)
    researchers = sum(1 for e in team if e.role == "AI Researcher")
    trainers    = sum(1 for e in team if e.role == "Model Trainer")
    if researchers < req["min_researchers"]:
        return False, f"Need {req['min_researchers']} AI Researchers (have {researchers})."
    if trainers < req["min_trainers"]:
        return False, f"Need {req['min_trainers']} Model Trainers (have {trainers})."
    if c.cash < req["min_cash"]:
        return False, f"Need ${req['min_cash']:,} in company cash (have ${c.cash:,})."
    return True, "OK"


# ─────────────────────── CATALOG BRIDGE ───────────────────────


def player_models_as_catalog(gs: GameState) -> list:
    """Convert ready player models into the same dict shape used by AI_MODELS."""
    out = []
    for m in gs.player_models:
        if m.training_status != "ready":
            continue
        speed_pts = m.axes.get("Speed", 0)
        coding_pts = m.axes.get("Coding", 0)
        reasoning_pts = m.axes.get("Reasoning", 0)
        # Derive stats from axes in 1–6 range matching the catalog
        speed   = max(1, min(6, 1 + speed_pts // 5))
        quality = max(1, min(6, 1 + (coding_pts + reasoning_pts) // 10))
        bug_risk = max(1, min(5, 6 - quality))
        tokens  = 1   # self-hosted, low cost
        out.append({
            "name":      m.name,
            "company":   "Your Lab",
            "year":      m.trained_year,
            "score":     m.capability_rating,
            "speed":     speed,
            "quality":   quality,
            "bug_risk":  bug_risk,
            "tokens":    tokens,
            "out_cost":  0.0,
            "desc":      f"Your custom model v{m.version}. Cap rating {m.capability_rating}/10.",
            "series":    None,
            "status":    "player",
            "is_player_model": True,
            "model_id":  m.model_id,
        })
    return out


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_player_models_tick(gs: GameState) -> list:
    """Advance training timers and pay out licensing revenue."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    for m in gs.player_models:
        if m.training_status == "training":
            m.training_days_remaining = max(0, m.training_days_remaining - 30)
            if m.training_days_remaining == 0:
                m.training_status = "ready"
                m.trained_year = gs.year
                c = gs.company_by_id(m.company_id)
                events.append((
                    "🤖",
                    f"Model '{m.name}' training complete! Cap {m.capability_rating}/10.",
                    "good", date_str,
                ))

        elif m.training_status == "ready" and m.licensed:
            c = gs.company_by_id(m.company_id)
            if c and c.active:
                rep_factor = 1.0 + gs.founder.reputation / 200.0
                rev = int(m.capability_rating * rep_factor * AI_MODEL_LICENSE_BASE_REVENUE)
                if rev > 0:
                    c.cash += rev
                    events.append((
                        "💰",
                        f"'{m.name}' API licensing: +${rev:,} to {c.name}",
                        "good", date_str,
                    ))

    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("start_model_training")
def _start_model_training(
    gs: GameState, company_id: int, name: str, axes: dict, invest_points: dict
) -> ActionResult:
    ok, reason = check_unlock(gs, company_id)
    if not ok:
        return ActionResult(ok=False, message=reason)

    total_points = sum(invest_points.values())
    if total_points <= 0:
        return ActionResult(ok=False, message="Must invest at least 1 point.")
    if total_points > AXIS_POINT_BUDGET:
        return ActionResult(ok=False,
                            message=f"Total points {total_points} exceeds budget {AXIS_POINT_BUDGET}.")

    cost = AI_MODEL_TRAINING_COST_PER_POINT * total_points
    token_cost = AI_MODEL_TOKEN_COST_PER_POINT * total_points
    c = gs.company_by_id(company_id)
    if c.cash < cost:
        return ActionResult(ok=False,
                            message=f"Need ${cost:,} (have ${c.cash:,}).")

    c.cash -= cost
    consume_tokens(gs, token_cost)

    model_id = gs._next_model_id
    gs._next_model_id += 1

    full_axes = {ax["name"]: invest_points.get(ax["name"], 0) for ax in AI_MODEL_AXES}
    cap = compute_capability(full_axes)
    training_days = total_points * AI_MODEL_TRAINING_DAYS_PER_POINT

    existing = sum(1 for m in gs.player_models
                   if m.company_id == company_id and m.name == name)
    version = existing + 1

    m = AIModel(
        name=name,
        axes=full_axes,
        version=version,
        company_id=company_id,
        capability_rating=cap,
        model_id=model_id,
        training_status="training",
        training_days_remaining=training_days,
        trained_year=gs.year,
    )
    gs.player_models.append(m)
    return ActionResult(
        ok=True,
        message=(
            f"Training '{name}' started! {training_days} days, "
            f"${cost:,} spent. Cap rating: {cap}/10."
        ),
    )


@register("toggle_model_licensing")
def _toggle_model_licensing(gs: GameState, model_id: int) -> ActionResult:
    for m in gs.player_models:
        if m.model_id == model_id:
            if m.training_status != "ready":
                return ActionResult(ok=False, message="Model is still training.")
            m.licensed = not m.licensed
            state = "enabled" if m.licensed else "disabled"
            return ActionResult(ok=True, message=f"Licensing {state} for '{m.name}'.")
    return ActionResult(ok=False, message="Model not found.")


@register("retire_player_model")
def _retire_player_model(gs: GameState, model_id: int) -> ActionResult:
    for m in gs.player_models:
        if m.model_id == model_id:
            gs.player_models.remove(m)
            return ActionResult(ok=True, message=f"'{m.name}' retired.")
    return ActionResult(ok=False, message="Model not found.")
