"""
Phase 3 — Product Lifecycle, Revenue, and Updates
Launch resolution, monthly revenue ticks, obsolescence, update actions, versioning.
"""

import random

from ...constants import (
    MONTH_NAMES, PRODUCT_REVENUE_MODELS, OBSOLESCENCE_WINDOWS,
    REVENUE_MODELS, FEATURE_SCOPES, AUTO_UPDATE_CYCLES,
)
from ...models import GameState, Project
from ..actions import register, ActionResult
from .finance import adjust_reputation, add_vibe, consume_tokens
from .companies import get_focus_data


# ─────────────────────── LAUNCH RESOLUTION ────────────────────


def launch_product(gs: GameState, p: Project) -> str:
    """
    Full launch resolution. Sets initial users, revenue, churn, obsolescence window.
    Called by dev_launch action. Returns a summary string.
    """
    from .employees import get_post_launch_bonus  # lazy
    quality = p.quality_score
    hype = min(100, p.hype + int(get_post_launch_bonus(gs, p.company_id)["hype_bonus"]))
    p.hype = hype
    rep = gs.founder.reputation

    if not p.revenue_model:
        p.revenue_model = PRODUCT_REVENUE_MODELS.get(p.ptype, "Subscription")

    if p.obsolescence_months == 0:
        lo, hi = OBSOLESCENCE_WINDOWS.get(p.ptype, (18, 36))
        p.obsolescence_months = random.randint(lo, hi)

    # Day-1 user base: hype drives spike, quality drives retention
    overhype = max(0.0, (hype - quality) / 100.0)
    scope_data = FEATURE_SCOPES.get(p.scope, FEATURE_SCOPES["Standard"])
    scope_mult = scope_data["features"] / 6.0      # lean=0.5, std=1.0, rich=1.67, over=2.5
    rep_mult = 0.5 + rep / 100.0                   # 0.5 – 1.5

    base = quality * 0.4 + hype * 0.6             # 0–100
    p.active_users = max(5, int(base * scope_mult * rep_mult * 0.6))
    p.users = p.active_users

    # Churn: over-hype and bugs push it up
    p.churn_rate = round(0.03 + overhype * 0.12 + p.bug_count * 0.004, 4)

    p.revenue = _calc_revenue_from_users(p)
    p.lifetime_revenue += p.revenue
    p.revenue_history = [p.revenue]

    # Reputation: quality gains, faked features and bugs hurt
    rep_gain = 2 + quality // 20
    if p.faked_features:
        rep_gain -= len(p.faked_features) * 3
        p.churn_rate = min(0.5, p.churn_rate + len(p.faked_features) * 0.04)
    adjust_reputation(gs, rep_gain)
    add_vibe(gs, 10.0)

    _update_company_revenue(gs, p)

    overhype_tag = "  ⚠ Over-hyped — expect churn" if overhype > 0.3 else ""
    return (
        f"{p.name} launched! {p.revenue_model} | "
        f"{p.active_users} users | ${p.revenue:,}/mo | "
        f"Quality {quality}/100{overhype_tag}"
    )


# ─────────────────────── MONTHLY TICK ─────────────────────────


def monthly_product_tick(gs: GameState, p: Project, date_str: str) -> list:
    """
    Monthly tick for a launched product: age, auto-update, growth/churn,
    obsolescence, revenue recompute. Returns events list.
    """
    if p.status not in ("Launched", "Growing") or p.discontinued:
        return []

    events = []
    p.age_months += 1

    # Auto-update
    if p.auto_update_interval > 0:
        p.auto_update_countdown = max(0, p.auto_update_countdown - 1)
        if p.auto_update_countdown == 0:
            _do_minor_update(gs, p)
            p.auto_update_countdown = p.auto_update_interval
            events.append(("🔄", f"Auto-updated {p.name} (v{p.version})", "good", date_str))

    # Obsolescence factor — silent per GDD
    obso = _obsolescence_factor(p)

    # User growth / churn (Phase 5: Community Wizards reduce effective churn)
    from .employees import get_post_launch_bonus  # lazy
    team = get_post_launch_bonus(gs, p.company_id)
    quality = p.quality_score
    growth_rate = 0.04 + quality / 2500.0           # 4 – 8% per month
    eff_churn = p.churn_rate * team["churn_mult"]
    net_pct = (growth_rate - eff_churn) * obso
    if p.active_users > 0:
        p.active_users = max(0, p.active_users + int(p.active_users * net_pct))
    p.users = p.active_users

    # Phase 4: focus revenue bonus for the project's company
    company = gs.company_by_id(p.company_id)
    focus = get_focus_data(company.focus_area) if company else None
    focus_rev_mult = focus["revenue_mult"] if focus else 1.0

    # Revenue from current user base × obsolescence × focus bonus
    base_rev = _calc_revenue_from_users(p)
    p.revenue = max(0, int(base_rev * obso * focus_rev_mult))
    p.lifetime_revenue += p.revenue

    p.revenue_history.append(p.revenue)
    if len(p.revenue_history) > 12:
        p.revenue_history = p.revenue_history[-12:]

    # Status transitions
    if p.revenue > 1000 and p.status == "Launched":
        p.status = "Growing"
    elif p.revenue < 100 and p.status == "Growing":
        p.status = "Launched"

    _update_company_revenue(gs, p)
    return events


# ─────────────────────── INTERNAL HELPERS ─────────────────────


def _calc_revenue_from_users(p: Project) -> int:
    """Derive monthly revenue from active_users and revenue_model."""
    model_data = REVENUE_MODELS.get(p.revenue_model or "Subscription", REVENUE_MODELS["Subscription"])
    rate = model_data["revenue_per_user"]
    users = p.active_users
    q = max(1, p.quality_score)

    if p.revenue_model == "Subscription":
        # Quality scales rate ×1.0–×2.0
        return int(users * rate * (1.0 + q / 100.0))
    elif p.revenue_model == "One-Time":
        # Residual new-buyer rate decays over time but quality sustains word-of-mouth
        residual = max(0.3, rate - p.age_months * 0.05 + q / 200.0)
        return int(users * residual)
    elif p.revenue_model == "Ads":
        return int(users * rate * (0.8 + q / 500.0))
    elif p.revenue_model == "Commission":
        return int(users * rate * (0.9 + q / 200.0))
    return int(users * rate)


def _obsolescence_factor(p: Project) -> float:
    """Silent factor 1.0 while fresh; decays toward 0.1 past 50% of window."""
    if p.obsolescence_months <= 0:
        return 1.0
    pct = p.age_months / p.obsolescence_months
    if pct < 0.5:
        return 1.0
    return max(0.1, 1.0 - (pct - 0.5) * 1.8)


def _do_minor_update(gs: GameState, p: Project) -> None:
    """Apply a minor update: reset some obsolescence, small churn improvement."""
    p.age_months = max(0, p.age_months - 6)
    p.churn_rate = max(0.01, p.churn_rate - 0.01)
    cost = 150
    c = gs.company_by_id(p.company_id)
    if c:
        c.cash = max(0, c.cash - cost)
    consume_tokens(gs, 5)


def _update_company_revenue(gs: GameState, p: Project) -> None:
    c = gs.company_by_id(p.company_id)
    if c:
        c.monthly_revenue = sum(
            proj.revenue for proj in gs.projects
            if proj.company_id == c.id and proj.status in ("Launched", "Growing")
        )


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("product_launch")
def _product_launch(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status != "Dev Complete":
        return ActionResult(ok=False, message=f"Not ready to launch (status: {p.status}).")

    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    p.status = "Launched"
    p.launch_date = date_str
    p.age_months = 0
    p.revenue_history = []
    msg = launch_product(gs, p)
    return ActionResult(ok=True, message=msg)


@register("product_minor_update")
def _product_minor_update(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status not in ("Launched", "Growing"):
        return ActionResult(ok=False, message="Can only update a launched product.")
    c = gs.company_by_id(p.company_id)
    if c and c.cash < 150:
        return ActionResult(ok=False, message=f"Need $150 for update (have ${c.cash:,}).")
    _do_minor_update(gs, p)
    return ActionResult(ok=True, message=f"Minor update shipped! Age reset -6mo. Churn -{0.01:.0%}.")


@register("product_major_revision")
def _product_major_revision(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status not in ("Launched", "Growing"):
        return ActionResult(ok=False, message="Can only revise a launched product.")

    from .development import start_dev_session  # lazy to avoid init-time cycle
    legacy_design = round(p.design_score * 0.4, 1)
    legacy_tech   = round(p.tech_score   * 0.4, 1)
    p.status = "In Dev"
    p.version += 1
    p.dev_day = 0
    p.progress = 0
    p.bug_count = 0
    p.paused_dev = False
    p.age_months = 0
    start_dev_session(gs, project_idx)
    # Restore carry-forward quality after start_dev_session resets scores
    p.design_score = legacy_design
    p.tech_score   = legacy_tech
    return ActionResult(ok=True, message=f"{p.name} v{p.version} — major revision started!")


@register("product_discontinue")
def _product_discontinue(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status in ("Sunset", "Archived"):
        return ActionResult(ok=False, message="Already discontinued.")

    old_rev = p.revenue
    p.discontinued = True
    p.status = "Sunset"
    p.revenue = 0
    p.active_users = 0
    p.users = 0
    _update_company_revenue(gs, p)
    return ActionResult(ok=True, message=f"{p.name} discontinued. ${old_rev:,}/mo revenue stream closed.")


@register("product_new_version")
def _product_new_version(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status not in ("Launched", "Growing"):
        return ActionResult(ok=False, message="Can only version a launched product.")

    from .development import start_dev_session  # lazy
    new_ver = p.version + 1
    transferred = int(p.active_users * 0.2)
    p.active_users = max(0, p.active_users - transferred)
    p.users = p.active_users

    scope_data = FEATURE_SCOPES.get(p.scope, FEATURE_SCOPES["Standard"])
    new_p = Project(
        name=f"{p.name} v{new_ver}",
        ptype=p.ptype,
        model=p.model,
        stack=p.stack,
        niche=p.niche,
        company_id=p.company_id,
        status="In Dev",
        progress=0,
        revenue=0,
        users=0,
        morale=p.morale,
        tokens_used=0,
        scope=p.scope,
        dev_total_days=scope_data["base_days"],
        version=new_ver,
        parent_product_id=project_idx,
        active_users=transferred,
        revenue_model=p.revenue_model,
        obsolescence_months=p.obsolescence_months,
    )
    gs.projects.append(new_p)
    new_idx = len(gs.projects) - 1
    start_dev_session(gs, new_idx)
    return ActionResult(
        ok=True,
        message=f"{new_p.name} created — dev started. {transferred} users migrated.",
    )


@register("product_set_auto_update")
def _product_set_auto_update(gs: GameState, project_idx: int, interval: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status not in ("Launched", "Growing"):
        return ActionResult(ok=False, message="Can only auto-update a launched product.")
    p.auto_update_interval = interval
    p.auto_update_countdown = interval
    if interval == 0:
        return ActionResult(ok=True, message=f"Auto-update disabled for {p.name}.")
    return ActionResult(ok=True, message=f"Auto-update every {interval} month(s) — $150/update.")
