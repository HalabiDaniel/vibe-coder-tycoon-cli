"""
Phase 10 — Player-Built AI Models tests.

Covers: capability computation, unlock gating, training flow (tick),
licensing revenue, catalog bridge, and persistence round-trip.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.models import Founder, AIModel
from vibe_coder_tycoon.engine.systems import player_models as pm
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(year=2028):
    f = Founder(username="Tester", background_idx=0, reputation=70, burnout=0,
                skill_prototyping=50, skill_sales=30, skill_tech=40, skill_management=30,
                total_tokens_used=0)
    gs = make_new_game(f, 3)
    gs.year = year
    c = gs.companies[0]
    c.focus_area = "AI Tools"
    c.office_level = 6
    c.datacenter_tier = 2
    c.cash = 200_000
    return gs


def _add_researchers_trainers(gs):
    from vibe_coder_tycoon.models import Employee
    for i in range(2):
        gs.employees.append(Employee(
            name=f"Researcher{i}", role="AI Researcher", level=1,
            salary=4000, mood=80, skill=70, hired_year=2028,
            company_id=0,
        ))
    gs.employees.append(Employee(
        name="Trainer1", role="Model Trainer", level=1,
        salary=5000, mood=80, skill=70, hired_year=2028,
        company_id=0,
    ))


# ─────────────────────── CAPABILITY ───────────────────────────

def test_compute_capability_zero():
    axes = {ax["name"]: 0 for ax in __import__(
        "vibe_coder_tycoon.constants", fromlist=["AI_MODEL_AXES"]).AI_MODEL_AXES}
    assert pm.compute_capability(axes) == 0.0


def test_compute_capability_full_budget():
    from vibe_coder_tycoon.constants import AI_MODEL_AXES, AXIS_POINT_BUDGET
    # Spread all points proportionally
    axes = {ax["name"]: int(AXIS_POINT_BUDGET * ax["weight"]) for ax in AI_MODEL_AXES}
    cap = pm.compute_capability(axes)
    assert cap > 0.0
    assert cap <= 10.0


def test_compute_capability_returns_float():
    axes = {"Coding": 10, "Reasoning": 8, "Creativity": 5,
            "Speed": 4, "Context": 2, "Multimodal": 1}
    cap = pm.compute_capability(axes)
    assert isinstance(cap, float)


# ─────────────────────── UNLOCK CHECK ─────────────────────────

def test_unlock_requires_ai_tools():
    gs = _gs()
    gs.companies[0].focus_area = "SaaS"
    ok, reason = pm.check_unlock(gs, 0)
    assert not ok
    assert "AI Tools" in reason


def test_unlock_requires_year():
    gs = _gs(year=2026)
    gs.companies[0].focus_area = "AI Tools"
    ok, reason = pm.check_unlock(gs, 0)
    assert not ok
    assert "2028" in reason


def test_unlock_requires_datacenter():
    gs = _gs()
    _add_researchers_trainers(gs)
    gs.companies[0].datacenter_tier = 0
    ok, reason = pm.check_unlock(gs, 0)
    assert not ok
    assert "Datacenter" in reason


def test_unlock_passes_when_all_met():
    gs = _gs()
    _add_researchers_trainers(gs)
    ok, reason = pm.check_unlock(gs, 0)
    assert ok, reason


# ─────────────────────── TRAINING ACTIONS ─────────────────────

def test_start_training_locked():
    gs = _gs()
    result = dispatch(gs, "start_model_training",
                      company_id=0,
                      name="TestModel",
                      axes={"Coding": 10},
                      invest_points={"Coding": 10})
    assert not result.ok


def test_start_training_happy_path():
    gs = _gs()
    _add_researchers_trainers(gs)
    result = dispatch(gs, "start_model_training",
                      company_id=0,
                      name="AlphaModel",
                      axes={"Coding": 10, "Reasoning": 5},
                      invest_points={"Coding": 10, "Reasoning": 5})
    assert result.ok, result.message
    assert len(gs.player_models) == 1
    m = gs.player_models[0]
    assert m.name == "AlphaModel"
    assert m.training_status == "training"
    assert m.training_days_remaining > 0


def test_start_training_deducts_cash():
    from vibe_coder_tycoon.constants import AI_MODEL_TRAINING_COST_PER_POINT
    gs = _gs()
    _add_researchers_trainers(gs)
    cash_before = gs.companies[0].cash
    dispatch(gs, "start_model_training",
             company_id=0, name="X",
             axes={"Coding": 10}, invest_points={"Coding": 10})
    assert gs.companies[0].cash == cash_before - AI_MODEL_TRAINING_COST_PER_POINT * 10


def test_start_training_budget_exceeded():
    gs = _gs()
    _add_researchers_trainers(gs)
    result = dispatch(gs, "start_model_training",
                      company_id=0, name="X",
                      axes={"Coding": 31}, invest_points={"Coding": 31})
    assert not result.ok
    assert "budget" in result.message.lower()


# ─────────────────────── MONTHLY TICK ─────────────────────────

def test_training_tick_advances_days():
    gs = _gs()
    _add_researchers_trainers(gs)
    dispatch(gs, "start_model_training",
             company_id=0, name="X",
             axes={"Coding": 5}, invest_points={"Coding": 5})
    m = gs.player_models[0]
    days_before = m.training_days_remaining
    pm.monthly_player_models_tick(gs)
    assert m.training_days_remaining == max(0, days_before - 30)


def test_training_completes():
    gs = _gs()
    _add_researchers_trainers(gs)
    dispatch(gs, "start_model_training",
             company_id=0, name="X",
             axes={"Coding": 1}, invest_points={"Coding": 1})
    m = gs.player_models[0]
    m.training_days_remaining = 5   # force near-done
    events = pm.monthly_player_models_tick(gs)
    assert m.training_status == "ready"
    assert any("complete" in e[1].lower() for e in events)


def test_licensing_revenue():
    gs = _gs()
    m = AIModel(
        name="LicensedModel", axes={"Coding": 10}, version=1,
        company_id=0, capability_rating=5.0, model_id=0,
        licensed=True, training_status="ready",
    )
    gs.player_models.append(m)
    cash_before = gs.companies[0].cash
    pm.monthly_player_models_tick(gs)
    assert gs.companies[0].cash > cash_before


def test_no_revenue_when_not_licensed():
    gs = _gs()
    m = AIModel(
        name="Model", axes={"Coding": 10}, version=1,
        company_id=0, capability_rating=5.0, model_id=0,
        licensed=False, training_status="ready",
    )
    gs.player_models.append(m)
    cash_before = gs.companies[0].cash
    pm.monthly_player_models_tick(gs)
    assert gs.companies[0].cash == cash_before


# ─────────────────────── TOGGLE / RETIRE ──────────────────────

def test_toggle_licensing():
    gs = _gs()
    m = AIModel(name="X", axes={}, version=1, company_id=0,
                capability_rating=3.0, model_id=0, licensed=False,
                training_status="ready")
    gs.player_models.append(m)
    result = dispatch(gs, "toggle_model_licensing", model_id=0)
    assert result.ok
    assert m.licensed is True


def test_toggle_licensing_during_training_fails():
    gs = _gs()
    m = AIModel(name="X", axes={}, version=1, company_id=0,
                capability_rating=3.0, model_id=0, licensed=False,
                training_status="training", training_days_remaining=100)
    gs.player_models.append(m)
    result = dispatch(gs, "toggle_model_licensing", model_id=0)
    assert not result.ok


def test_retire_model():
    gs = _gs()
    m = AIModel(name="X", axes={}, version=1, company_id=0,
                capability_rating=3.0, model_id=0,
                training_status="ready")
    gs.player_models.append(m)
    result = dispatch(gs, "retire_player_model", model_id=0)
    assert result.ok
    assert len(gs.player_models) == 0


# ─────────────────────── CATALOG BRIDGE ───────────────────────

def test_player_models_as_catalog_only_ready():
    gs = _gs()
    gs.player_models.append(AIModel(
        name="Training", axes={"Coding": 5}, version=1, company_id=0,
        capability_rating=3.0, model_id=0,
        training_status="training", training_days_remaining=50,
    ))
    gs.player_models.append(AIModel(
        name="Done", axes={"Coding": 10}, version=1, company_id=0,
        capability_rating=5.0, model_id=1,
        training_status="ready",
    ))
    catalog = pm.player_models_as_catalog(gs)
    assert len(catalog) == 1
    assert catalog[0]["name"] == "Done"
    assert catalog[0]["is_player_model"] is True


def test_available_models_prepends_player():
    from vibe_coder_tycoon.engine.systems.models_ai import available_models
    gs = _gs()
    gs.player_models.append(AIModel(
        name="MyModel", axes={"Coding": 10}, version=1, company_id=0,
        capability_rating=6.0, model_id=0, training_status="ready",
    ))
    models = available_models(gs)
    assert models[0]["name"] == "MyModel"


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_player_models_round_trip():
    gs = _gs()
    gs.player_models.append(AIModel(
        name="Persisted", axes={"Coding": 8, "Reasoning": 5}, version=2,
        company_id=0, capability_rating=4.5, model_id=7,
        licensed=True, training_status="ready", trained_year=2029,
    ))
    gs._next_model_id = 8
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    assert len(gs2.player_models) == 1
    m2 = gs2.player_models[0]
    assert m2.name == "Persisted"
    assert m2.model_id == 7
    assert m2.licensed is True
    assert m2.axes["Coding"] == 8
    assert gs2._next_model_id == 8
