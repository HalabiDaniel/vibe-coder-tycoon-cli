"""
Phase 7 — Tech Timeline, AI Models, IDEs, Subscriptions

Year-gated access to the model/IDE catalog, era progression, post-2042
auto-versioning, and subscription costs. This is the layer that turns the
project wizard's model/IDE/tier choices into real inputs to the Phase 2
development simulation.
"""

from ...constants import (
    ERAS, IDE_CATALOG, SUBSCRIPTION_TIERS, MONTH_NAMES, AI_SUBS,
)
from ...data.ai_models import AI_MODELS
from ...models import GameState
from ..actions import register, ActionResult


# ─────────────────────── LOOKUP / GATING ──────────────────────


_MODEL_BY_NAME = {m["name"]: m for m in AI_MODELS}


def get_model(name: str) -> dict | None:
    return _MODEL_BY_NAME.get(name)


def available_models(gs: GameState) -> list:
    """All catalog models released on/before the current in-game year, plus any
    post-2042 auto-versioned frontier models. Player models come first."""
    from .player_models import player_models_as_catalog
    player = player_models_as_catalog(gs)
    year = gs.year
    out = [m for m in AI_MODELS if m["year"] <= year]
    out.extend(_future_models(gs))
    out.sort(key=lambda m: (-m["year"], -m["score"], m["name"]))
    return player + out


def available_model_names(gs: GameState) -> list:
    return [m["name"] for m in available_models(gs)]


def _future_models(gs: GameState) -> list:
    """After 2042 the top lineages release a new version every year (GDD §15)."""
    if gs.year <= 2042:
        return []
    # Find the strongest model in each major series and project forward.
    best_by_series = {}
    for m in AI_MODELS:
        s = m["series"] or m["company"]
        cur = best_by_series.get(s)
        if cur is None or m["score"] > cur["score"]:
            best_by_series[s] = m
    top = sorted(best_by_series.values(), key=lambda m: -m["score"])[:4]
    bump = gs.year - 2042
    out = []
    for base in top:
        score = min(10.0, round(base["score"] + bump * 0.1, 1))
        out.append({
            **base,
            "name": f"{base['series'] or base['company']} v{2 + bump}",
            "year": gs.year,
            "status": "frontier",
            "score": score,
            "quality": min(6, base["quality"] + 1),
            "bug_risk": max(1, base["bug_risk"] - 1),
            "desc": f"Auto-incremented {base['series']} frontier model for {gs.year}.",
        })
    return out


# ─────────────────────── ERAS ─────────────────────────────────


def era_for_year(year: int) -> str:
    name = ERAS[0][1]
    for start, ename, _ in ERAS:
        if year >= start:
            name = ename
    return name


def era_blurb(name: str) -> str:
    for _, ename, blurb in ERAS:
        if ename == name:
            return blurb
    return ""


# ─────────────────────── IDE / SUBSCRIPTION ───────────────────


def get_ide(name: str) -> dict | None:
    for ide in IDE_CATALOG:
        if ide["name"] == name:
            return ide
    return None


def available_ides(gs: GameState) -> list:
    return [ide for ide in IDE_CATALOG if ide["year"] <= gs.year]


def get_subscription(name: str) -> dict | None:
    for s in SUBSCRIPTION_TIERS:
        if s["name"] == name:
            return s
    return None


# ─────────────────────── DEV INTEGRATION ──────────────────────


def get_model_stats(gs: GameState, model_name: str) -> dict:
    """
    Resolve the speed/quality/bug_risk/tokens stats for the model a project is
    using. Falls back to the legacy AI_SUBS list (for old saves) and finally to
    the founder's active subscription's basic tier.
    """
    m = get_model(model_name)
    if m is not None:
        return {"speed": m["speed"], "quality": m["quality"],
                "bug_risk": m["bug_risk"], "tokens": m["tokens"],
                "name": m["name"], "score": m["score"]}
    for sub in AI_SUBS:
        if sub["name"] == model_name:
            return {"speed": sub["speed"], "quality": sub["quality"],
                    "bug_risk": sub["bug_risk"], "tokens": sub["tokens"],
                    "name": sub["name"], "score": sub["quality"] * 2}
    sub = AI_SUBS[gs.active_ai_sub_idx]
    return {"speed": sub["speed"], "quality": sub["quality"],
            "bug_risk": sub["bug_risk"], "tokens": sub["tokens"],
            "name": sub["name"], "score": sub["quality"] * 2}


def get_dev_modifiers(gs: GameState) -> dict:
    """IDE + subscription multipliers applied on top of model stats in the
    development tick: dev_speed_mult, bug_mult, token_mult."""
    ide = get_ide(gs.active_ide) or {}
    sub = get_subscription(gs.subscription_tier) or {}
    return {
        "dev_speed_mult": ide.get("dev_speed_mult", 1.0) * sub.get("speed_mult", 1.0),
        "bug_mult": ide.get("bug_mult", 1.0),
        "token_mult": ide.get("token_mult", 1.0),
    }


# ─────────────────────── MONTHLY HOOKS ─────────────────────────


def subscription_settlement(gs: GameState) -> list:
    """Charge the founder's subscription each month. Returns event tuples."""
    events = []
    sub = get_subscription(gs.subscription_tier)
    if sub is None:
        return events
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    cost = sub["monthly"]
    if sub["per_token"] > 0:
        cost += int(gs.tokens_this_month * sub["per_token"])
    if cost > 0:
        gs.founder.personal_cash -= cost
        events.append(("💳", f"{sub['name']} subscription: -${cost:,}", "warn", date_str))
    gs.tokens_this_month = 0
    return events


def timeline_tick(gs: GameState) -> list:
    """Detect era transitions and announce notable new model releases. Called
    once per simulated month (cheap; only acts on year boundaries)."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    new_era = era_for_year(gs.year)
    if new_era != gs.current_era:
        gs.current_era = new_era
        events.append(("🌅", f"New Era: {new_era}", "good", date_str))
        gs.news_feed.insert(0, {
            "icon": "🌅", "headline": f"{new_era} begins — {era_blurb(new_era)}",
            "category": "Era", "date": date_str, "effect": None,
        })

    # Announce up to 2 top models that became available this year (in January).
    if gs.month == 1:
        releases = sorted(
            [m for m in AI_MODELS if m["year"] == gs.year],
            key=lambda m: -m["score"],
        )[:2]
        for m in releases:
            gs.news_feed.insert(0, {
                "icon": "🤖",
                "headline": f"{m['company']} releases {m['name']} (score {m['score']}/10)",
                "category": "Tools", "date": date_str, "effect": None,
            })
    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("set_subscription_tier")
def _set_subscription_tier(gs: GameState, tier: str) -> ActionResult:
    sub = get_subscription(tier)
    if sub is None:
        return ActionResult(ok=False, message=f"Unknown tier: {tier}.")
    gs.subscription_tier = tier
    note = " (open-weight models only)" if sub["open_only"] else ""
    return ActionResult(ok=True, message=f"Subscription set to {tier}{note}.")


@register("set_active_ide")
def _set_active_ide(gs: GameState, ide_name: str) -> ActionResult:
    ide = get_ide(ide_name)
    if ide is None:
        return ActionResult(ok=False, message=f"Unknown IDE: {ide_name}.")
    if ide["year"] > gs.year:
        return ActionResult(ok=False, message=f"{ide_name} isn't available until {ide['year']}.")
    gs.active_ide = ide_name
    return ActionResult(ok=True, message=f"IDE set to {ide_name}.")


@register("set_active_model")
def _set_active_model(gs: GameState, model_name: str) -> ActionResult:
    m = get_model(model_name)
    if m is None:
        return ActionResult(ok=False, message=f"Unknown model: {model_name}.")
    if m["year"] > gs.year:
        return ActionResult(ok=False, message=f"{model_name} isn't released until {m['year']}.")
    sub = get_subscription(gs.subscription_tier)
    if sub and sub.get("open_only") and m["out_cost"] > 0:
        return ActionResult(ok=False,
                            message=f"{model_name} isn't open-weight — switch off Self-Hosted to use it.")
    gs.active_model = model_name
    return ActionResult(ok=True, message=f"Default model set to {model_name}.")
