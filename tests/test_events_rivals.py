"""
Phase 13 — Random Events, Rivals, Procedural Content tests.

Covers: event weighting + cooldowns, vibe/sanity modulation, instant + choice
event effects, choice-card resolution, rival saturation effect, rival monthly
drift/spawn, content determinism under a fixed seed, and persistence round-trip.
"""

import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, advance_month, dispatch
from vibe_coder_tycoon.models import Founder, Project, RivalCompany
from vibe_coder_tycoon.engine.systems import events, rivals, content
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(year=2028, vibe=50.0, sanity=100, reputation=50):
    f = Founder(username="Tester", background_idx=0, reputation=reputation,
                burnout=0, skill_prototyping=50, skill_sales=30,
                skill_tech=40, skill_management=30, total_tokens_used=0,
                vibe=vibe, sanity=sanity)
    gs = make_new_game(f, 3)
    gs.year = year
    return gs


def _launched_product(gs, ptype="SaaS Web App", users=500, company_id=0):
    p = Project(
        name="TestApp", ptype=ptype, model="ChatNPC", stack="Next.js + Vercel",
        niche="Productivity", company_id=company_id, status="Launched",
        progress=100, revenue=2000, users=users, morale=80, tokens_used=10,
        quality_score=60, revenue_model="Subscription", active_users=users,
        obsolescence_months=36,
    )
    gs.projects.append(p)
    return p


# ─────────────────────── EVENT EFFECTS ────────────────────────

def test_apply_effects_all_keys():
    gs = _gs()
    _launched_product(gs)
    gs.founder.personal_cash = 1000.0
    gs.founder.sanity = 50
    gs.founder.vibe = 50.0
    rep0 = gs.founder.reputation
    tok0 = gs.founder.total_tokens_used

    events.apply_effects(gs, {
        "personal_cash": 500, "company_cash": -200, "reputation": 5,
        "vibe": 10, "sanity": -8, "tokens": 100, "hype": 15,
    })
    assert gs.founder.personal_cash == 1500.0
    assert gs.founder.reputation == rep0 + 5
    assert gs.founder.vibe == 60.0
    assert gs.founder.sanity == 42
    assert gs.founder.total_tokens_used == tok0 + 100


def test_sanity_and_vibe_clamped():
    gs = _gs(vibe=95.0, sanity=5)
    events.apply_effects(gs, {"vibe": 50, "sanity": -50})
    assert gs.founder.vibe == 100.0
    assert gs.founder.sanity == 0


# ─────────────────────── MODULATION ───────────────────────────

def test_hot_vibe_amplifies_negative_events():
    calm = _gs(vibe=50.0, sanity=100)
    chaotic = _gs(vibe=100.0, sanity=100)
    neg_calm = events._category_multiplier(calm, "negative")
    neg_chaos = events._category_multiplier(chaotic, "negative")
    assert neg_chaos > neg_calm


def test_low_sanity_amplifies_founder_events():
    healthy = _gs(sanity=100)
    struggling = _gs(sanity=0)
    assert (events._category_multiplier(struggling, "founder")
            > events._category_multiplier(healthy, "founder"))


def test_hot_vibe_suppresses_positive_events():
    calm = _gs(vibe=40.0, reputation=60)
    chaotic = _gs(vibe=100.0, reputation=60)
    assert (events._category_multiplier(chaotic, "positive")
            < events._category_multiplier(calm, "positive"))


def test_fire_chance_rises_with_chaos():
    calm = _gs(vibe=50.0, sanity=100)
    chaotic = _gs(vibe=100.0, sanity=0)
    assert events.event_fire_chance(chaotic) > events.event_fire_chance(calm)


# ─────────────────────── COOLDOWNS + GATES ────────────────────

def test_cooldown_excludes_recent_event():
    gs = _gs()
    evt = events.EVENT_CATALOG[0]   # hn_front_page, cooldown 4
    gs.event_cooldowns[evt["id"]] = gs.months_elapsed
    pool_ids = [e["id"] for e, _ in events.eligible_events(gs)]
    assert evt["id"] not in pool_ids
    # After the cooldown elapses it becomes eligible again
    gs.months_elapsed += evt["cooldown"]
    # hn_front_page requires a live product
    _launched_product(gs)
    pool_ids = [e["id"] for e, _ in events.eligible_events(gs)]
    assert evt["id"] in pool_ids


def test_requirement_gating():
    gs = _gs()
    # No products yet → has_product events excluded
    pool_ids = [e["id"] for e, _ in events.eligible_events(gs)]
    assert "hn_front_page" not in pool_ids
    _launched_product(gs)
    pool_ids = [e["id"] for e, _ in events.eligible_events(gs)]
    assert "hn_front_page" in pool_ids


def test_global_cooldown_blocks_back_to_back():
    gs = _gs()
    gs.event_cooldowns["_global"] = gs.months_elapsed
    # Force fire chance high; global cooldown should still block
    gs.founder.vibe = 100.0
    out = events.maybe_trigger_event(gs)
    assert out == []


# ─────────────────────── CHOICE CARDS ─────────────────────────

def test_choice_card_pushed_and_resolved():
    gs = _gs()
    # Find a choice event with no requirement gate
    evt = next(e for e in events.EVENT_CATALOG
               if e["kind"] == "choice" and not e.get("requires"))
    events._push_choice_card(gs, evt, "Jan 2028")
    assert len(gs.pending_event_cards) == 1
    card = gs.pending_event_cards[0]

    cash0 = gs.founder.personal_cash
    rep0 = gs.founder.reputation
    result = dispatch(gs, "resolve_event_choice",
                      card_id=card["card_id"], choice_idx=0)
    assert result.ok
    assert len(gs.pending_event_cards) == 0
    # Some effect was applied (cash or reputation or vibe changed somewhere)
    assert (gs.founder.personal_cash != cash0
            or gs.founder.reputation != rep0
            or gs.founder.vibe != 50.0)


def test_resolve_invalid_card():
    gs = _gs()
    result = dispatch(gs, "resolve_event_choice", card_id=999, choice_idx=0)
    assert not result.ok


# ─────────────────────── RIVALS ───────────────────────────────

def test_seed_initial_rivals():
    gs = _gs()
    assert len(gs.rivals) == 2
    for rv in gs.rivals:
        assert rv.vertical
        assert rv.product_name
        assert 0 <= rv.market_presence <= 100


def test_saturation_reduces_with_presence():
    gs = _gs()
    gs.rivals = []
    assert rivals.saturation_factor(gs, "SaaS Web App") == 1.0
    gs.rivals.append(RivalCompany(
        name="HyperLabs", focus="AI Tools", vertical="SaaS Web App",
        product_name="DashAI", market_presence=80.0, founded_year=2028))
    sat = rivals.saturation_factor(gs, "SaaS Web App")
    assert sat < 1.0
    # A different vertical is unaffected
    assert rivals.saturation_factor(gs, "Mobile App") == 1.0


def test_saturation_respects_floor():
    gs = _gs()
    gs.rivals = [RivalCompany(
        name="MegaRival", focus="AI Tools", vertical="SaaS Web App",
        product_name="X", market_presence=100.0, founded_year=2028)
        for _ in range(6)]
    sat = rivals.saturation_factor(gs, "SaaS Web App")
    from vibe_coder_tycoon.constants import RIVAL_SATURATION_FLOOR
    assert sat == RIVAL_SATURATION_FLOOR


def test_rival_saturation_dents_product_revenue():
    from vibe_coder_tycoon.engine.systems.products import monthly_product_tick
    # Baseline with no rivals
    gs1 = _gs()
    gs1.rivals = []
    p1 = _launched_product(gs1, users=1000)
    monthly_product_tick(gs1, p1, "Jan 2028")
    rev_no_rivals = p1.revenue

    # Same setup but heavy rival saturation in the vertical
    gs2 = _gs()
    gs2.rivals = [RivalCompany(
        name="Crowd", focus="AI Tools", vertical="SaaS Web App",
        product_name="Y", market_presence=100.0, founded_year=2028)]
    p2 = _launched_product(gs2, users=1000)
    monthly_product_tick(gs2, p2, "Jan 2028")
    rev_saturated = p2.revenue

    assert rev_saturated < rev_no_rivals


def test_rival_monthly_drift_changes_presence():
    gs = _gs()
    random.seed(7)
    before = [rv.market_presence for rv in gs.rivals]
    rivals.monthly_rivals_tick(gs)
    after = [rv.market_presence for rv in gs.rivals]
    assert before != after


# ─────────────────────── CONTENT DETERMINISM ──────────────────

def test_content_deterministic_under_fixed_seed():
    r1 = random.Random(42)
    r2 = random.Random(42)
    names1 = [content.gen_company_name(r1) for _ in range(5)]
    names2 = [content.gen_company_name(r2) for _ in range(5)]
    assert names1 == names2

    r1 = random.Random(99)
    r2 = random.Random(99)
    assert ([content.gen_product_name("SaaS Web App", r1) for _ in range(5)]
            == [content.gen_product_name("SaaS Web App", r2) for _ in range(5)])


def test_review_tone_tracks_quality():
    r = random.Random(1)
    # High quality should never pull from the negative bank
    from vibe_coder_tycoon.data import strings as S
    review = content.gen_review(90, "Foo", r)
    assert any(review == t.format(product="Foo") for t in S.REVIEW_POSITIVE)


def test_news_item_shape():
    r = random.Random(3)
    item = content.gen_news_item(r)
    assert set(["icon", "headline", "category", "date", "effect"]).issubset(item.keys())
    assert item["headline"]


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_persistence_round_trip_phase13():
    gs = _gs()
    gs.event_cooldowns = {"hn_front_page": 3, "_global": 4}
    gs.pending_event_cards = [{
        "card_id": 0, "event_id": "burnout_warning", "icon": "🪫",
        "title": "Tired", "body": "rest?", "category": "founder",
        "choices": [{"label": "Rest", "effects": {"sanity": 10}, "result": "ok"}],
    }]
    gs.rivals.append(RivalCompany(
        name="ZTest", focus="AI Tools", vertical="Mobile App",
        product_name="Zap", market_presence=33.0, founded_year=2027,
        aggression=0.6, tagline="ship it"))

    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)

    assert gs2.schema_version == 12
    assert gs2.event_cooldowns == {"hn_front_page": 3, "_global": 4}
    assert len(gs2.pending_event_cards) == 1
    assert gs2.pending_event_cards[0]["event_id"] == "burnout_warning"
    assert any(r.name == "ZTest" and r.vertical == "Mobile App" for r in gs2.rivals)


def test_old_save_migrates_to_v12():
    gs = _gs()
    data = _gs_to_dict(gs, "Tester")
    # Simulate a pre-Phase-13 save
    data["schema_version"] = 11
    data.pop("rivals", None)
    data.pop("event_cooldowns", None)
    data.pop("pending_event_cards", None)
    gs2 = _dict_to_gs(data)
    assert gs2.schema_version == 12
    assert gs2.rivals == []
    assert gs2.event_cooldowns == {}
    assert gs2.pending_event_cards == []
