"""
Phase 9 — Infrastructure and Compute tests.

Covers: hosting cost curve, outage trigger threshold, GPU cost-reduction +
obsolescence, datacenter token reduction, compute-sale revenue, and save
round-trip of the new company fields.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random

from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.models import Founder, Project
from vibe_coder_tycoon.engine.systems import infra
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(year=2025):
    f = Founder(username="Tester", background_idx=0, reputation=40, burnout=0,
                skill_prototyping=50, skill_sales=30, skill_tech=40, skill_management=30,
                total_tokens_used=0)
    gs = make_new_game(f, 3)
    gs.year = year
    return gs


def _add_launched(gs, users, cid=0):
    p = Project(name="App", ptype="SaaS Web App", model="X", stack="T3",
                niche="Productivity", company_id=cid, status="Launched", progress=100,
                revenue=1000, users=users, morale=80, tokens_used=0,
                active_users=users, revenue_model="Subscription")
    gs.projects.append(p)
    return p


# ─────────────────────── HOSTING ──────────────────────────────

def test_hosting_cost_scales_with_users():
    gs = _gs()
    c = gs.companies[0]
    dispatch(gs, "set_hosting", company_id=0, provider="Hobby Cloud")
    _add_launched(gs, 1000)
    cost = infra.hosting_monthly_cost(gs, c)
    # base 50 + 1000 * 0.05 = 100
    assert cost == 100


def test_set_hosting_action():
    gs = _gs()
    res = dispatch(gs, "set_hosting", company_id=0, provider="Pro Cloud")
    assert res.ok
    assert gs.companies[0].hosting_provider == "Pro Cloud"


def test_company_active_users_sums_launched_only():
    gs = _gs()
    _add_launched(gs, 500)
    p2 = _add_launched(gs, 999)
    p2.status = "In Dev"   # not counted
    assert infra.company_active_users(gs, gs.companies[0]) == 500


# ─────────────────────── OUTAGE ───────────────────────────────

def test_outage_triggers_over_capacity():
    gs = _gs()
    c = gs.companies[0]
    c.hosting_provider = "Free Tier"   # capacity 200
    p = _add_launched(gs, 5000)        # way over
    random.seed(1)
    fired = False
    for _ in range(20):
        before = p.active_users
        infra.monthly_infra_settlement(gs)
        if p.active_users < before:
            fired = True
            break
    assert fired


def test_no_outage_under_capacity():
    gs = _gs()
    c = gs.companies[0]
    c.hosting_provider = "Pro Cloud"   # capacity 25000
    p = _add_launched(gs, 100)
    users_before = p.active_users
    for _ in range(10):
        infra.monthly_infra_settlement(gs)
    assert p.active_users == users_before   # never churned by outage


# ─────────────────────── GPUs / DATACENTER ────────────────────

def test_buy_gpu_reduces_token_cost():
    gs = _gs(2025)
    c = gs.companies[0]
    c.cash = 100_000
    before = infra.get_token_cost_multiplier(gs, c)
    res = dispatch(gs, "buy_gpu", company_id=0, gpu_name="Blackwell B200")
    assert res.ok
    after = infra.get_token_cost_multiplier(gs, c)
    assert after < before


def test_buy_gpu_gated_by_year():
    gs = _gs(2025)
    gs.companies[0].cash = 200_000
    res = dispatch(gs, "buy_gpu", company_id=0, gpu_name="Rubin R300")  # 2027
    assert not res.ok


def test_gpu_obsolesces_over_time():
    gs = _gs(2025)
    c = gs.companies[0]
    c.gpu_inventory.append({"name": "Blackwell B200", "year_bought": 2025})
    fresh = infra.gpu_effective_reduction(gs, c.gpu_inventory[0])
    gs.year = 2035   # 10 years old
    aged = infra.gpu_effective_reduction(gs, c.gpu_inventory[0])
    assert aged < fresh


def test_datacenter_upgrade_and_token_cut():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 100_000
    before = infra.get_token_cost_multiplier(gs, c)
    res = dispatch(gs, "upgrade_datacenter", company_id=0)
    assert res.ok
    assert c.datacenter_tier == 1
    assert c.compute_capacity == 100
    assert infra.get_token_cost_multiplier(gs, c) < before


def test_token_multiplier_floored():
    gs = _gs(2030)
    c = gs.companies[0]
    c.datacenter_tier = 4
    for _ in range(20):
        c.gpu_inventory.append({"name": "Rubin R300", "year_bought": 2030})
    assert infra.get_token_cost_multiplier(gs, c) >= 0.30


# ─────────────────────── COMPUTE SALES ────────────────────────

def test_compute_sale_requires_datacenter():
    gs = _gs()
    res = dispatch(gs, "toggle_compute_sale", company_id=0)
    assert not res.ok   # no datacenter yet


def test_compute_sale_revenue_positive():
    gs = _gs()
    c = gs.companies[0]
    c.cash = 100_000
    dispatch(gs, "upgrade_datacenter", company_id=0)
    res = dispatch(gs, "toggle_compute_sale", company_id=0)
    assert res.ok and c.compute_for_sale
    random.seed(0)
    rev = infra.compute_sale_revenue(gs, c)
    assert rev > 0


def test_compute_sale_added_in_settlement():
    gs = _gs()
    c = gs.companies[0]
    c.compute_for_sale = True
    c.datacenter_tier = 2
    c.compute_capacity = 500
    c.hosting_provider = "Free Tier"
    cash_before = c.cash
    random.seed(0)
    infra.monthly_infra_settlement(gs)
    assert c.cash > cash_before   # compute revenue exceeded zero hosting cost


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_infra_round_trip():
    gs = _gs()
    c = gs.companies[0]
    c.hosting_provider = "Enterprise Cloud"
    c.datacenter_tier = 2
    c.compute_capacity = 500
    c.compute_for_sale = True
    c.gpu_inventory.append({"name": "Hopper H100", "year_bought": 2024})
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    c2 = gs2.companies[0]
    assert c2.hosting_provider == "Enterprise Cloud"
    assert c2.datacenter_tier == 2
    assert c2.compute_capacity == 500
    assert c2.compute_for_sale is True
    assert c2.gpu_inventory[0]["name"] == "Hopper H100"
