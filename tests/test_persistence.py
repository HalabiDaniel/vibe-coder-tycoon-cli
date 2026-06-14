"""
Phase 15 — Persistence, Save Migration, Cloud Sync tests.

Covers the finalization acceptance criteria:
- round-trip serialize/deserialize for a fully-populated GameState (every model),
- every schema migration path (v1 → current),
- checksum determinism + tamper detection,
- sync-queue behaviour (enqueue / replace / flush),
- run RNG-state restore (a loaded game continues the same deterministic stream),
- the previously-unsaved `demo_ended` flag.
"""

import sys
import os
import json
import random
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, dispatch, advance_month
from vibe_coder_tycoon.models import (
    Founder, Company, Project, Employee, Loan, DevSession,
    Template, AIModel, FundingDeal, RivalCompany, GameState,
)
from vibe_coder_tycoon.persistence import (
    _gs_to_dict, _dict_to_gs, _migrate, compute_checksum,
    get_sync_queue, save_sync_queue, add_to_sync_queue, flush_sync_queue,
    _serialize_rng_state, _restore_rng_state,
)
from vibe_coder_tycoon.constants import APP_CONFIG_DIR


# ─────────────────────── FIXTURES ─────────────────────────────

def _founder():
    return Founder(
        username="Tester", background_idx=2, reputation=64, burnout=12,
        skill_prototyping=55, skill_sales=40, skill_tech=48, skill_management=33,
        total_tokens_used=98765,
        achievements=["Incorporated", "First $1K"],
        career_history=[{"event": "founded"}],
        unlocked_research=["Cap Table Basics"],
        personal_cash=4242.5, vibe=73.0, sanity=61,
        conditions=["Founder Burnout"],
    )


def _full_gs():
    """Build a GameState that exercises every dataclass and most fields."""
    gs = make_new_game(_founder(), 3)
    gs.year = 2031
    gs.month = 7
    gs.months_elapsed = 18
    gs.demo_ended = True
    gs.current_era = "The Automation Era"
    gs.subscription_tier = "Max"
    gs.active_ide = "Replicity AI"
    gs.active_model = "Clodex Pro"
    gs.tokens_this_month = 1234
    gs.loan_default_count = 1
    gs.peak_net_worth = 9_000_000.0
    gs.victory = True
    gs.victory_type = "trillionaire"
    gs.endgame_continue = True
    gs.broke_months = 0
    gs.pending_offers = [{"offer_id": 1, "amount": 50000}]
    gs.event_cooldowns = {"market_crash": 12}
    gs.pending_event_cards = [{"card_id": "x", "choices": [{"label": "A"}]}]
    gs.graveyard = [{"name": "DeadCo", "cause": "Bankruptcy"}]
    gs.news_feed = [{"icon": "📈", "text": "news"}]
    gs.research_progress = {"Faster Deployment": 100}

    # Company with a loan
    c = gs.companies[0]
    c.is_public = True
    c.ipo_stage = "Trading"
    c.share_price = 42.5
    c.shares_outstanding = 1_000_000
    c.player_equity_pct = 0.62
    c.share_price_history = [40.0, 41.0, 42.5]
    c.gpu_inventory = [{"name": "H100", "year_bought": 2030}]
    c.datacenter_tier = 2
    c.compute_capacity = 64
    c.compute_for_sale = True
    c.history = [{"event": "incorporated"}]
    c.loans = [Loan(lender="VibeBank", principal=10000, balance=8000,
                    rate=0.08, term_months=12, company_id=c.id,
                    monthly_payment=900)]

    # Project with an active dev session
    p = Project(name="WidgetAI", ptype="SaaS Web App", model="Clodex Pro",
                stack="T3 Stack", niche="B2B Automation", company_id=c.id,
                status="In Dev", progress=40, revenue=120, users=3000, morale=80,
                tokens_used=4500, bug_count=3, hype=55, tech_debt=8,
                design_score=62.0, tech_score=58.0, quality_score=70)
    p.revenue_model = "Subscription"
    p.revenue_history = [100, 110, 120]
    p.faked_features = ["AI Magic"]
    p.dev_session = DevSession(
        terminal_log=["Compiling...", "Done."],
        pending_interruption={"id": "hallucination"},
        interruption_choice_idx=1,
        action_result="ok",
    )
    gs.projects.append(p)

    # Employee
    gs.employees.append(Employee(
        name="Ada Lovelace", role="Vibe Coder", level=3, salary=2500, mood=70,
        skill=66, hired_year=2030, company_id=c.id, trait="Deep Focus",
        coding=72, prompting=68, research=40, marketing=30, sanity=55, xp=240,
        assigned_project_id=0, state="active", backstory="ex-FAANG",
        condition="Burnout", condition_until=20,
    ))

    # Template
    gs.templates.append(Template(
        name="Auth Kit", template_type="Auth Boilerplate", version=2,
        company_id=c.id, design_bonus=5.0, tech_bonus=8.0,
        time_reduction=0.2, bug_reduction=0.3, built_year=2030,
    ))

    # Player AI model
    gs.player_models.append(AIModel(
        name="VibeLM-1", axes={"Coding": 8, "Reasoning": 6}, version=1,
        company_id=c.id, capability_rating=7.0, model_id=0, licensed=True,
        training_status="ready", trained_year=2031,
    ))
    gs._next_model_id = 1

    # Funding deal
    gs.funding_deals.append(FundingDeal(
        deal_id=1, round_type="Seed Round", amount=500000, equity_pct=0.12,
        requirement_desc="Hit 10K MRR", requirement_metric="mrr",
        requirement_target=10000, deadline_month=24, company_id=c.id,
        investor_name="AngelBridge", status="active", month_accepted=18,
    ))

    # Rival
    gs.rivals = []
    gs.rivals.append(RivalCompany(
        name="CloneCorp", focus="AI Tools", vertical="SaaS Web App",
        product_name="WidgetClone", market_presence=33.0, founded_year=2030,
        aggression=0.6, tagline="We copy fast.",
    ))
    return gs


# ─────────────────────── ROUND-TRIP ───────────────────────────

def test_round_trip_preserves_scalars_and_flags():
    gs = _full_gs()
    gs2 = _dict_to_gs(_gs_to_dict(gs, "Tester"))

    assert gs2.year == gs.year
    assert gs2.month == gs.month
    assert gs2.months_elapsed == gs.months_elapsed
    assert gs2.demo_ended is True
    assert gs2.current_era == "The Automation Era"
    assert gs2.subscription_tier == "Max"
    assert gs2.active_ide == "Replicity AI"
    assert gs2.active_model == "Clodex Pro"
    assert gs2.tokens_this_month == 1234
    assert gs2.loan_default_count == 1
    assert gs2.peak_net_worth == 9_000_000.0
    assert gs2.victory is True
    assert gs2.victory_type == "trillionaire"
    assert gs2.endgame_continue is True
    assert gs2._next_model_id == 1
    assert gs2.event_cooldowns == {"market_crash": 12}
    assert gs2.pending_offers == [{"offer_id": 1, "amount": 50000}]
    assert gs2.graveyard == [{"name": "DeadCo", "cause": "Bankruptcy"}]


def test_round_trip_preserves_founder():
    gs = _full_gs()
    f = _dict_to_gs(_gs_to_dict(gs, "Tester")).founder
    assert f.username == "Tester"
    assert f.reputation == 64
    assert f.personal_cash == 4242.5
    assert f.vibe == 73.0
    assert f.sanity == 61
    assert f.conditions == ["Founder Burnout"]
    assert f.total_tokens_used == 98765
    assert f.achievements == ["Incorporated", "First $1K"]


def test_round_trip_preserves_company_and_loans():
    gs = _full_gs()
    c = _dict_to_gs(_gs_to_dict(gs, "Tester")).companies[0]
    assert c.is_public is True
    assert c.ipo_stage == "Trading"
    assert c.share_price == 42.5
    assert c.shares_outstanding == 1_000_000
    assert c.player_equity_pct == 0.62
    assert c.share_price_history == [40.0, 41.0, 42.5]
    assert c.datacenter_tier == 2
    assert c.compute_capacity == 64
    assert c.compute_for_sale is True
    assert c.gpu_inventory == [{"name": "H100", "year_bought": 2030}]
    assert len(c.loans) == 1
    assert isinstance(c.loans[0], Loan)
    assert c.loans[0].lender == "VibeBank"
    assert c.loans[0].balance == 8000


def test_round_trip_preserves_project_and_dev_session():
    gs = _full_gs()
    p = _dict_to_gs(_gs_to_dict(gs, "Tester")).projects[0]
    assert p.name == "WidgetAI"
    assert p.status == "In Dev"
    assert p.design_score == 62.0
    assert p.tech_score == 58.0
    assert p.revenue_model == "Subscription"
    assert p.revenue_history == [100, 110, 120]
    assert p.faked_features == ["AI Magic"]
    assert isinstance(p.dev_session, DevSession)
    assert p.dev_session.terminal_log == ["Compiling...", "Done."]
    assert p.dev_session.pending_interruption == {"id": "hallucination"}
    assert p.dev_session.interruption_choice_idx == 1


def test_round_trip_preserves_employee():
    gs = _full_gs()
    e = _dict_to_gs(_gs_to_dict(gs, "Tester")).employees[0]
    assert e.name == "Ada Lovelace"
    assert e.coding == 72 and e.prompting == 68
    assert e.xp == 240
    assert e.condition == "Burnout"
    assert e.condition_until == 20
    assert e.backstory == "ex-FAANG"


def test_round_trip_preserves_secondary_models():
    gs = _full_gs()
    gs2 = _dict_to_gs(_gs_to_dict(gs, "Tester"))

    assert gs2.templates[0].name == "Auth Kit"
    assert gs2.templates[0].time_reduction == 0.2

    m = gs2.player_models[0]
    assert m.name == "VibeLM-1"
    assert m.axes == {"Coding": 8, "Reasoning": 6}
    assert m.licensed is True

    d = gs2.funding_deals[0]
    assert d.round_type == "Seed Round"
    assert d.requirement_target == 10000
    assert d.investor_name == "AngelBridge"

    r = gs2.rivals[0]
    assert r.name == "CloneCorp"
    assert r.market_presence == 33.0
    assert r.tagline == "We copy fast."


def test_round_trip_is_json_serializable():
    gs = _full_gs()
    data = _gs_to_dict(gs, "Tester")
    # Must survive a real JSON encode/decode (cloud upload path).
    reloaded = json.loads(json.dumps(data))
    gs2 = _dict_to_gs(reloaded)
    assert gs2.companies[0].loans[0].lender == "VibeBank"
    assert gs2.demo_ended is True


def test_schema_version_is_current():
    gs = _full_gs()
    data = _gs_to_dict(gs, "Tester")
    assert data["schema_version"] == GameState.__dataclass_fields__["schema_version"].default


# ─────────────────────── MIGRATIONS ───────────────────────────

def _legacy_v1_save():
    """A minimal v1 save, before any of the phase fields existed."""
    return {
        "schema_version": 1,
        "username": "Old",
        "year": 2025,
        "month": 1,
        "months_elapsed": 0,
        "active_ai_sub_idx": 0,
        "founder": {
            "username": "Old", "background_idx": 0, "reputation": 20,
            "burnout": 0, "skill_prototyping": 40, "skill_sales": 20,
            "skill_tech": 35, "skill_management": 20, "total_tokens_used": 0,
        },
        "companies": [{
            "id": 0, "name": "OldCo", "legal_style": "Sole Prop",
            "focus_area": "SaaS", "funding_style": "Bootstrapped",
            "risk_appetite": "Balanced", "cash": 1000, "monthly_revenue": 0,
            "monthly_expenses": 0, "debt": 0, "reputation": 10, "valuation": 0,
            "office_level": 1, "mood": 70, "founded_month": 1, "founded_year": 2025,
        }],
        "projects": [{
            "name": "P", "ptype": "SaaS Web App", "model": "ChatNPC Basic",
            "stack": "Next.js + Vercel", "niche": "Productivity", "company_id": 0,
            "status": "In Dev", "progress": 10, "revenue": 0, "users": 0,
            "morale": 80, "tokens_used": 0,
        }],
        "employees": [],
        "news_feed": [],
        "events": [],
        "research_progress": {},
        "settings": {},
    }


def test_migration_v1_to_current_fills_all_fields():
    data = _migrate(copy.deepcopy(_legacy_v1_save()))
    cur = GameState.__dataclass_fields__["schema_version"].default
    assert data["schema_version"] == cur
    # Phase 1 founder fields
    assert "personal_cash" in data["founder"]
    assert "vibe" in data["founder"]
    # Phase 3 project fields
    assert "revenue_model" in data["projects"][0]
    # Phase 9 company infra fields
    assert "hosting_provider" in data["companies"][0]
    # Phase 12 stock fields
    assert "is_public" in data["companies"][0]
    # later top-level collections
    assert "rivals" in data
    assert "graveyard" in data


def test_migration_v1_loads_into_gamestate():
    gs = _dict_to_gs(copy.deepcopy(_legacy_v1_save()))
    assert isinstance(gs, GameState)
    assert gs.founder.username == "Old"
    assert gs.companies[0].hosting_provider == "Free Tier"
    assert gs.projects[0].revenue_model == ""
    assert gs.victory is False


def test_each_migration_step_is_monotonic():
    """Migrating from every intermediate version reaches the current version."""
    cur = GameState.__dataclass_fields__["schema_version"].default
    for v in range(1, cur + 1):
        data = copy.deepcopy(_legacy_v1_save())
        data["schema_version"] = v
        migrated = _migrate(data)
        assert migrated["schema_version"] == cur


def test_migration_is_idempotent():
    once = _migrate(copy.deepcopy(_legacy_v1_save()))
    twice = _migrate(copy.deepcopy(once))
    assert once["schema_version"] == twice["schema_version"]


# ─────────────────────── CHECKSUM ─────────────────────────────

def test_checksum_is_deterministic():
    data = _gs_to_dict(_full_gs(), "Tester")
    assert compute_checksum(data) == compute_checksum(copy.deepcopy(data))


def test_checksum_is_order_independent():
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    assert compute_checksum(a) == compute_checksum(b)


def test_checksum_detects_tampering():
    data = _gs_to_dict(_full_gs(), "Tester")
    before = compute_checksum(data)
    data["year"] += 1
    assert compute_checksum(data) != before


# ─────────────────────── SYNC QUEUE ───────────────────────────

def test_sync_queue_enqueue_and_replace():
    save_sync_queue([])
    try:
        add_to_sync_queue("alice", {"v": 1})
        add_to_sync_queue("bob", {"v": 1})
        assert len(get_sync_queue()) == 2
        # Re-queuing the same user replaces, not appends.
        add_to_sync_queue("alice", {"v": 2})
        q = get_sync_queue()
        assert len(q) == 2
        alice = next(e for e in q if e["username"] == "alice")
        assert alice["save_data"] == {"v": 2}
    finally:
        save_sync_queue([])


class _FakeCloud:
    def __init__(self, fail=False):
        self.fail = fail
        self.uploads = []

    def upload_save(self, user_id, slot, save_data, checksum):
        self.uploads.append((user_id, slot, save_data, checksum))
        if self.fail:
            return None, "Network error."
        return {"id": "row"}, None


def test_flush_sync_queue_clears_on_success():
    save_sync_queue([])
    try:
        add_to_sync_queue("alice", {"v": 1})
        cloud = _FakeCloud(fail=False)
        flush_sync_queue(cloud, "user-123")
        assert get_sync_queue() == []
        assert len(cloud.uploads) == 1
    finally:
        save_sync_queue([])


def test_flush_sync_queue_keeps_on_failure():
    save_sync_queue([])
    try:
        add_to_sync_queue("alice", {"v": 1})
        cloud = _FakeCloud(fail=True)
        flush_sync_queue(cloud, "user-123")
        assert len(get_sync_queue()) == 1
    finally:
        save_sync_queue([])


# ─────────────────────── RNG STATE ────────────────────────────

def test_rng_state_round_trip_continues_sequence():
    random.seed(12345)
    # advance the stream a bit, then snapshot
    [random.random() for _ in range(7)]
    state = _serialize_rng_state()
    expected = [random.random() for _ in range(5)]

    # Perturb the global RNG, then restore from the serialized snapshot.
    random.seed(999)
    [random.random() for _ in range(3)]
    assert _restore_rng_state(state) is True
    restored = [random.random() for _ in range(5)]

    assert restored == expected


def test_rng_state_survives_json():
    random.seed(2024)
    state = _serialize_rng_state()
    expected = [random.random() for _ in range(4)]

    encoded = json.loads(json.dumps(state))
    random.seed(1)
    assert _restore_rng_state(encoded) is True
    assert [random.random() for _ in range(4)] == expected


def test_rng_restored_through_full_save_load():
    gs = make_new_game(_founder(), 3)
    random.seed(55555)
    data = _gs_to_dict(gs, "Tester")          # snapshots current RNG state
    expected = [random.random() for _ in range(6)]

    random.seed(0)                            # clobber the stream
    _dict_to_gs(data)                         # should restore the snapshot
    assert [random.random() for _ in range(6)] == expected


def test_restore_rng_state_ignores_missing():
    assert _restore_rng_state(None) is False
    assert _restore_rng_state([]) is False


def test_old_save_without_rng_state_still_loads():
    data = _gs_to_dict(_full_gs(), "Tester")
    data.pop("rng_state", None)
    gs = _dict_to_gs(data)        # must not raise
    assert isinstance(gs, GameState)


# ─────────────────────── ADVANCE + RESTORE ────────────────────

def test_save_after_advance_round_trips():
    gs = make_new_game(_founder(), 3)
    for _ in range(3):
        advance_month(gs)
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    assert gs2.months_elapsed == gs.months_elapsed
    assert gs2.year == gs.year
    assert gs2.month == gs.month
