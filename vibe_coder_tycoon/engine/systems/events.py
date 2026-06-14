"""
Phase 13 — Random Events (GDD §21).

A weighted event scheduler. Each month `monthly_event_tick` may fire one event
from EVENT_CATALOG. Selection probability is modulated by:

  • Vibe        — hot Vibe (>50) raises chaos: more negative + meme events.
  • Founder sanity — low sanity raises negative/founder-event likelihood.
  • Reputation  — higher reputation slightly favours positive events.

Events are either:
  • "instant" — effects applied immediately, returns a single event tuple.
  • "choice"  — a card is pushed to gs.pending_event_cards for the player to
                resolve via the `resolve_event_choice` action (an overlay).

Per-event cooldowns and a short global cooldown keep the feed from spamming.
"""

import random

from ...constants import (
    MONTH_NAMES, EVENT_CATALOG, EVENT_BASE_MONTHLY_CHANCE, EVENT_GLOBAL_COOLDOWN,
)
from ...models import GameState
from ..actions import register, ActionResult
from .finance import adjust_reputation, add_vibe, consume_tokens


# ─────────────────────── EFFECT APPLICATION ───────────────────


def _random_active_company(gs: GameState):
    active = gs.active_companies()
    return random.choice(active) if active else None


def _random_live_product(gs: GameState):
    live = [p for p in gs.projects if p.status in ("Launched", "Growing") and not p.discontinued]
    return random.choice(live) if live else None


def apply_effects(gs: GameState, effects: dict) -> list:
    """Apply a flat effects dict to the game state. Returns human-readable notes."""
    notes = []
    for key, val in effects.items():
        if val == 0:
            continue
        if key == "personal_cash":
            gs.founder.personal_cash = max(0.0, gs.founder.personal_cash + val)
            notes.append(f"{'+' if val > 0 else ''}${val:,.0f} personal")
        elif key == "company_cash":
            c = _random_active_company(gs)
            if c is not None:
                c.cash = max(0, c.cash + val)
                notes.append(f"{'+' if val > 0 else ''}${val:,.0f} to {c.name}")
        elif key == "reputation":
            adjust_reputation(gs, val)
            notes.append(f"{'+' if val > 0 else ''}{val} rep")
        elif key == "vibe":
            add_vibe(gs, float(val))
            notes.append(f"{'+' if val > 0 else ''}{val} vibe")
        elif key == "sanity":
            gs.founder.sanity = max(0, min(100, gs.founder.sanity + val))
            notes.append(f"{'+' if val > 0 else ''}{val} sanity")
        elif key == "tokens" and val > 0:
            consume_tokens(gs, val)
            notes.append(f"+{val}K tokens")
        elif key == "hype":
            p = _random_live_product(gs)
            if p is not None:
                p.hype = max(0, min(100, p.hype + val))
                notes.append(f"{'+' if val > 0 else ''}{val} hype on {p.name}")
    return notes


# ─────────────────────── ELIGIBILITY + WEIGHTING ──────────────


def _requirement_met(gs: GameState, req) -> bool:
    if not req:
        return True
    if req == "has_company":
        return bool(gs.active_companies())
    if req == "has_product":
        return any(p.status in ("Launched", "Growing") and not p.discontinued
                   for p in gs.projects)
    if req == "has_employees":
        return bool(gs.employees)
    if req == "is_public":
        return any(c.is_public for c in gs.active_companies())
    return True


def _category_multiplier(gs: GameState, category: str) -> float:
    """Modulate an event's weight by Vibe, founder sanity, and reputation."""
    vibe = gs.founder.vibe if gs.founder else 50.0
    sanity = gs.founder.sanity if gs.founder else 100
    rep = gs.founder.reputation if gs.founder else 50

    vibe_heat = max(0.0, (vibe - 50.0) / 50.0)      # 0 at calm, 1 at max chaos
    low_sanity = max(0.0, (50 - sanity) / 50.0)     # 0 when sanity>=50, 1 at 0

    if category == "negative":
        return 1.0 + vibe_heat * 1.2 + low_sanity * 1.0
    if category == "meme":
        return 1.0 + vibe_heat * 0.6
    if category == "founder":
        return 1.0 + low_sanity * 1.5
    if category == "positive":
        # Calm + good reputation favours good fortune; chaos suppresses it.
        return max(0.2, 1.0 - vibe_heat * 0.5 + (rep - 50) / 100.0 * 0.4)
    return 1.0


def eligible_events(gs: GameState) -> list:
    """Return [(event, weight)] for events that pass gates and cooldowns."""
    out = []
    for evt in EVENT_CATALOG:
        if gs.year < evt.get("min_year", 0):
            continue
        if not _requirement_met(gs, evt.get("requires")):
            continue
        last = gs.event_cooldowns.get(evt["id"])
        if last is not None and (gs.months_elapsed - last) < evt.get("cooldown", 0):
            continue
        weight = evt["weight"] * _category_multiplier(gs, evt["category"])
        if weight > 0:
            out.append((evt, weight))
    return out


def event_fire_chance(gs: GameState) -> float:
    """Overall monthly chance an event fires (clamped 0–0.95)."""
    vibe = gs.founder.vibe if gs.founder else 50.0
    sanity = gs.founder.sanity if gs.founder else 100
    heat = max(0.0, (vibe - 50.0) / 50.0)
    low_sanity = max(0.0, (50 - sanity) / 50.0)
    chance = EVENT_BASE_MONTHLY_CHANCE + heat * 0.2 + low_sanity * 0.15
    return max(0.0, min(0.95, chance))


# ─────────────────────── MONTHLY TICK ─────────────────────────


def _push_choice_card(gs: GameState, evt: dict, date_str: str) -> tuple:
    card = {
        "card_id": (max([c.get("card_id", -1) for c in gs.pending_event_cards], default=-1) + 1),
        "event_id": evt["id"],
        "icon": evt["icon"],
        "title": evt["headline"],
        "body": evt.get("body", ""),
        "category": evt["category"],
        "choices": [
            {"label": ch["label"], "effects": ch["effects"], "result": ch.get("result", "")}
            for ch in evt["choices"]
        ],
    }
    gs.pending_event_cards.append(card)
    return (evt["icon"], f"{evt['headline']} (decision needed)", "warn", date_str)


def maybe_trigger_event(gs: GameState) -> list:
    """Possibly fire one weighted event this month. Returns event tuples."""
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    # Respect a short global cooldown so events don't fire every single month.
    last_global = gs.event_cooldowns.get("_global")
    if last_global is not None and (gs.months_elapsed - last_global) < EVENT_GLOBAL_COOLDOWN:
        return []

    if random.random() > event_fire_chance(gs):
        return []

    pool = eligible_events(gs)
    if not pool:
        return []

    events_out = []
    evt = random.choices([e for e, _ in pool], weights=[w for _, w in pool])[0]
    gs.event_cooldowns[evt["id"]] = gs.months_elapsed
    gs.event_cooldowns["_global"] = gs.months_elapsed

    kind_pair = {"positive": "good", "meme": "neutral",
                 "negative": "bad", "founder": "warn"}
    if evt["kind"] == "choice":
        events_out.append(_push_choice_card(gs, evt, date_str))
    else:
        notes = apply_effects(gs, evt.get("effects", {}))
        suffix = f"  ({', '.join(notes)})" if notes else ""
        events_out.append((evt["icon"], evt["headline"] + suffix,
                           kind_pair.get(evt["category"], "neutral"), date_str))
    return events_out


def monthly_event_tick(gs: GameState) -> list:
    return maybe_trigger_event(gs)


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("resolve_event_choice")
def _resolve_event_choice(gs: GameState, card_id: int, choice_idx: int) -> ActionResult:
    card = next((c for c in gs.pending_event_cards if c.get("card_id") == card_id), None)
    if card is None:
        return ActionResult(ok=False, message="Event card not found.")
    choices = card.get("choices", [])
    if choice_idx < 0 or choice_idx >= len(choices):
        return ActionResult(ok=False, message="Invalid choice.")
    choice = choices[choice_idx]
    notes = apply_effects(gs, choice.get("effects", {}))
    gs.pending_event_cards = [c for c in gs.pending_event_cards if c.get("card_id") != card_id]

    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    result_msg = choice.get("result", "Resolved.")
    suffix = f"  ({', '.join(notes)})" if notes else ""
    gs.events.insert(0, (card["icon"], f"{card['title']} — {result_msg}{suffix}",
                         "neutral", date_str))
    return ActionResult(ok=True, message=result_msg + suffix)
