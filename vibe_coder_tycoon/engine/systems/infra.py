"""
Phase 9 — Infrastructure and Compute

Hosting providers whose cost scales with a company's live user base (and whose
capacity, if exceeded, triggers outages); GPU purchases and datacenter tiers
that reduce per-token development cost; and a compute-selling side business
that turns spare datacenter capacity into passive monthly revenue.
"""

import random

from ...constants import (
    HOSTING_PROVIDERS, GPU_GENERATIONS, DATACENTER_TIERS,
    COMPUTE_UNIT_PRICE, MONTH_NAMES,
)
from ...models import GameState, Company
from ..actions import register, ActionResult
from .finance import adjust_reputation


# ─────────────────────── LOOKUP HELPERS ───────────────────────


def get_hosting(name: str) -> dict:
    for h in HOSTING_PROVIDERS:
        if h["name"] == name:
            return h
    return HOSTING_PROVIDERS[0]


def get_gpu_def(name: str) -> dict | None:
    for g in GPU_GENERATIONS:
        if g["name"] == name:
            return g
    return None


def available_gpus(gs: GameState) -> list:
    return [g for g in GPU_GENERATIONS if g["year"] <= gs.year]


def get_datacenter(tier: int) -> dict:
    for d in DATACENTER_TIERS:
        if d["tier"] == tier:
            return d
    return DATACENTER_TIERS[0]


def company_active_users(gs: GameState, c: Company) -> int:
    return sum(p.active_users for p in gs.projects
               if p.company_id == c.id and p.status in ("Launched", "Growing"))


# ─────────────────────── COST / BENEFIT MATH ──────────────────


def gpu_effective_reduction(gs: GameState, gpu: dict) -> float:
    """A GPU's token-cost reduction, decayed as it ages past ~4 years."""
    gdef = get_gpu_def(gpu.get("name", "")) if isinstance(gpu, dict) else None
    if gdef is None:
        return 0.0
    age = max(0, gs.year - gpu.get("year_bought", gdef["year"]))
    decay = max(0.3, 1.0 - max(0, age - 4) * 0.15)
    return gdef["token_reduction"] * decay


def get_token_cost_multiplier(gs: GameState, c: Company) -> float:
    """Multiplier (≤1.0) applied to dev token cost from owned GPUs + datacenter.
    Floored so infrastructure never makes tokens free."""
    reduction = sum(gpu_effective_reduction(gs, g) for g in c.gpu_inventory)
    reduction += get_datacenter(c.datacenter_tier)["per_token_reduction"]
    return max(0.30, 1.0 - reduction)


def hosting_monthly_cost(gs: GameState, c: Company) -> int:
    h = get_hosting(c.hosting_provider)
    users = company_active_users(gs, c)
    return int(h["base_cost"] + users * h["cost_per_user"])


def compute_sale_revenue(gs: GameState, c: Company) -> int:
    """Monthly passive revenue from selling spare compute. Scales with sold
    capacity, market demand (rng), and hardware quality (GPU count)."""
    if not c.compute_for_sale or c.compute_capacity <= 0:
        return 0
    demand = random.uniform(0.7, 1.25)
    quality = 1.0 + len(c.gpu_inventory) * 0.05
    return int(c.compute_capacity * COMPUTE_UNIT_PRICE * demand * quality)


# ─────────────────────── MONTHLY SETTLEMENT ───────────────────


def monthly_infra_settlement(gs: GameState) -> list:
    """Charge hosting, resolve outages, and pay out compute sales. Returns
    event tuples. Adjusts company cash directly (alongside finance settlement)."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    for c in gs.active_companies():
        users = company_active_users(gs, c)
        host = get_hosting(c.hosting_provider)

        cost = hosting_monthly_cost(gs, c)
        if cost > 0:
            c.cash -= cost
            events.append(("🖥️", f"{c.name} hosting: -${cost:,} ({users:,} users)", "warn", date_str))

        # Under-provisioning → probabilistic outage
        if users > host["capacity"] and host["capacity"] > 0:
            over = users / host["capacity"]
            outage_prob = min(0.9, (over - 1.0) * 0.6 + 0.1)
            if random.random() < outage_prob:
                lost_frac = random.uniform(0.10, 0.25)
                for p in gs.projects:
                    if p.company_id == c.id and p.status in ("Launched", "Growing"):
                        drop = int(p.active_users * lost_frac)
                        p.active_users = max(0, p.active_users - drop)
                        p.users = p.active_users
                        p.hype = max(0, p.hype - 10)
                adjust_reputation(gs, -3)
                events.append(
                    ("🔥", f"{c.name} OUTAGE! Over capacity ({users:,}/{host['capacity']:,}). "
                           f"Users churned, reputation hit.", "bad", date_str)
                )

        # Compute sales (passive)
        rev = compute_sale_revenue(gs, c)
        if rev > 0:
            c.cash += rev
            events.append(("⚡", f"{c.name} sold compute: +${rev:,}", "good", date_str))

    return events


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("set_hosting")
def _set_hosting(gs: GameState, company_id: int, provider: str) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    h = get_hosting(provider)
    if h["name"] != provider:
        return ActionResult(ok=False, message=f"Unknown provider: {provider}.")
    c.hosting_provider = provider
    return ActionResult(ok=True,
                        message=f"Hosting set to {provider} (cap {h['capacity']:,} users).")


@register("buy_gpu")
def _buy_gpu(gs: GameState, company_id: int, gpu_name: str) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    gdef = get_gpu_def(gpu_name)
    if gdef is None:
        return ActionResult(ok=False, message=f"Unknown GPU: {gpu_name}.")
    if gdef["year"] > gs.year:
        return ActionResult(ok=False, message=f"{gpu_name} isn't available until {gdef['year']}.")
    if c.cash < gdef["cost"]:
        return ActionResult(ok=False, message=f"Need ${gdef['cost']:,} (have ${c.cash:,}).")
    c.cash -= gdef["cost"]
    c.gpu_inventory.append({"name": gpu_name, "year_bought": gs.year})
    new_mult = get_token_cost_multiplier(gs, c)
    return ActionResult(ok=True,
                        message=f"Bought {gpu_name}. Dev token cost now {new_mult:.0%}.")


@register("upgrade_datacenter")
def _upgrade_datacenter(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    nxt = get_datacenter(c.datacenter_tier + 1)
    if nxt["tier"] <= c.datacenter_tier:
        return ActionResult(ok=False, message="Already at the maximum datacenter tier.")
    if c.cash < nxt["cost"]:
        return ActionResult(ok=False, message=f"Need ${nxt['cost']:,} (have ${c.cash:,}).")
    c.cash -= nxt["cost"]
    c.datacenter_tier = nxt["tier"]
    c.compute_capacity = nxt["compute_capacity"]
    c.history.append(f"Built datacenter: {nxt['name']}")
    return ActionResult(ok=True,
                        message=f"Built {nxt['name']}! Token cost down, {nxt['compute_capacity']:,} compute units.")


@register("toggle_compute_sale")
def _toggle_compute_sale(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if c.datacenter_tier <= 0 or c.compute_capacity <= 0:
        return ActionResult(ok=False, message="Build a datacenter before selling compute.")
    c.compute_for_sale = not c.compute_for_sale
    state = "ON" if c.compute_for_sale else "OFF"
    return ActionResult(ok=True, message=f"Compute selling {state} for {c.name}.")
