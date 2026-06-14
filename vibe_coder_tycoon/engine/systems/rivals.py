"""
Phase 13 — Background Rivals (GDD §22).

Rivals are lightweight, non-interactive competitors. They occupy product
verticals (matching a project's `ptype`) and accumulate market presence, which
gently suppresses the player's sales in that vertical via `saturation_factor`.

Per the GDD, the player cannot sabotage, poach, or acquire rivals — that's the
post-launch 2.0 expansion. Rivals only:
  • drift their market presence each month,
  • occasionally launch a fresh clone in a vertical the player operates in,
  • surface as subtle news / market-saturation pressure.
"""

import random

from ...constants import (
    MONTH_NAMES, PROJECT_TYPES, RIVAL_TAGLINES,
    RIVAL_SATURATION_FLOOR, RIVAL_MAX_ACTIVE,
)
from ...models import GameState, RivalCompany
from . import content


# ─────────────────────── CREATION ─────────────────────────────


def _make_rival(vertical: str, year: int, rng=None) -> RivalCompany:
    r = rng if rng is not None else random
    return RivalCompany(
        name=content.gen_company_name(r),
        focus="AI Tools",
        vertical=vertical,
        product_name=content.gen_product_name(vertical, r),
        market_presence=round(r.uniform(8.0, 25.0), 1),
        founded_year=year,
        aggression=round(r.uniform(0.3, 0.9), 2),
        tagline=r.choice(RIVAL_TAGLINES),
    )


def seed_initial_rivals(gs: GameState, count: int = 2, rng=None) -> None:
    """Seed a couple of background rivals at game start. Idempotent-ish."""
    if gs.rivals:
        return
    r = rng if rng is not None else random
    verticals = list(PROJECT_TYPES)
    r.shuffle(verticals)
    for v in verticals[:count]:
        gs.rivals.append(_make_rival(v, gs.year, r))


# ─────────────────────── SATURATION ───────────────────────────


def vertical_presence(gs: GameState, vertical: str) -> float:
    """Total rival market presence in a vertical (0–100+)."""
    return sum(rv.market_presence for rv in gs.rivals if rv.vertical == vertical)


def saturation_factor(gs: GameState, vertical: str) -> float:
    """
    Sales multiplier (<=1.0) for a player product in `vertical`. More rival
    presence → more saturation → lower factor, floored by RIVAL_SATURATION_FLOOR.
    """
    presence = vertical_presence(gs, vertical)
    factor = 1.0 - (presence / 200.0)        # 100 presence → 0.5
    return max(RIVAL_SATURATION_FLOOR, min(1.0, factor))


def _player_verticals(gs: GameState) -> list:
    return list({p.ptype for p in gs.projects
                 if p.status in ("Launched", "Growing") and not p.discontinued})


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_rivals_tick(gs: GameState) -> list:
    """Grow rival presence, occasionally spawn a clone, surface news."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    # Drift existing rivals' presence (random walk biased by aggression).
    for rv in gs.rivals:
        drift = rv.aggression * random.uniform(-1.0, 2.0)
        rv.market_presence = max(1.0, min(100.0, rv.market_presence + drift))

    player_verts = _player_verticals(gs)

    # Occasionally a rival launches a clone in one of the player's verticals.
    if player_verts and len(gs.rivals) < RIVAL_MAX_ACTIVE and random.random() < 0.12:
        vertical = random.choice(player_verts)
        rival = _make_rival(vertical, gs.year)
        gs.rivals.append(rival)
        events.append((
            "🥷",
            (f"{rival.name} launched '{rival.product_name}' — a {vertical} clone "
             f"crowding your turf. Sales pressure incoming."),
            "warn", date_str,
        ))

    # Subtle rival activity in the news feed for verticals the player is in.
    elif gs.rivals and random.random() < 0.10:
        rv = random.choice(gs.rivals)
        gs.news_feed.insert(0, {
            "icon": "📈",
            "headline": f"{rv.name} gaining ground in {rv.vertical} — '{rv.tagline}'.",
            "category": "Market",
            "date": date_str,
            "effect": None,
        })
        gs.news_feed = gs.news_feed[:20]

    return events
