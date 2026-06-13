"""
Phase 2 — Active Development Phase
Per-tick dev progression, interruption events, QA, and dev panel actions.
"""

import random

from ...constants import (
    AI_SUBS, MONTH_NAMES, FEATURE_SCOPES, QA_OPTIONS,
    DEV_INTERRUPTION_EVENTS, DEV_ACTIONS, TERMINAL_LOG_LINES,
)
from ...models import GameState, DevSession
from ..actions import register, ActionResult
from .finance import consume_tokens, adjust_reputation, add_vibe, get_vibe_multiplier


# ─────────────────────── SESSION LIFECYCLE ────────────────────


def start_dev_session(gs: GameState, project_idx: int) -> None:
    """Initialize a dev session on a project and set its dev parameters."""
    p = gs.projects[project_idx]
    scope_data = FEATURE_SCOPES.get(p.scope, FEATURE_SCOPES["Standard"])
    p.dev_total_days = scope_data["base_days"]
    p.dev_day = 0
    p.design_score = 0.0
    p.tech_score = 0.0
    p.bug_count = 0
    p.hype = 30
    p.faked_features = []
    p.paused_dev = False
    p.dev_session = DevSession(
        terminal_log=[f"[Init] Starting dev on {p.name!r} — Scope: {p.scope}, Days: {p.dev_total_days}"],
    )


# ─────────────────────── TICK (called from advance_month) ─────


def tick_dev_project(gs: GameState, p) -> list:
    """
    Advance one project's development by ~30 dev days.
    Returns events list. Non-session projects use simple auto-progress.
    """
    events = []
    if p.status != "In Dev" or p.paused_dev:
        return events

    if p.dev_session is None:
        # Legacy / background project: simple fallback progression
        sub = AI_SUBS[gs.active_ai_sub_idx]
        p.progress = min(100, p.progress + random.randint(5, 10) + sub["speed"])
        if p.progress >= 100:
            p.status = "Launched"
            date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
            p.launch_date = date_str
            events.append(("🚀", f"{p.name} launched!", "good", date_str))
        return events

    ds = p.dev_session

    if ds.pending_interruption:
        _add_log(ds, "⏸  Dev blocked — resolve the interruption to continue.")
        return events

    sub = AI_SUBS[gs.active_ai_sub_idx]
    vibe_mult = get_vibe_multiplier(gs)
    scope_data = FEATURE_SCOPES.get(p.scope, FEATURE_SCOPES["Standard"])

    days_this_month = 28 + random.randint(-3, 5)
    interrupted = False

    for _ in range(days_this_month):
        if p.dev_day >= p.dev_total_days or interrupted:
            break

        p.dev_day += 1

        # Design + tech score gain per day
        design_gain = (sub["quality"] * 15.0 / p.dev_total_days) * vibe_mult * random.uniform(0.7, 1.3)
        tech_gain   = (sub["quality"] * 14.0 / p.dev_total_days)               * random.uniform(0.7, 1.3)
        p.design_score = min(100.0, p.design_score + design_gain)
        p.tech_score   = min(100.0, p.tech_score   + tech_gain)

        # Bug generation: vibe multiplies chaos
        if random.random() < sub["bug_risk"] * vibe_mult * 0.03:
            p.bug_count += 1

        # Token consumption per day
        token_day = max(1, int(scope_data["token_mult"] * sub["tokens"] * random.uniform(0.5, 1.5)))
        consume_tokens(gs, token_day)
        p.tokens_used += token_day

        # Interruption check every ~10 days
        if p.dev_day % 10 == 0:
            _check_interruption(gs, p)
            if ds.pending_interruption:
                interrupted = True
                break

        # Occasional terminal log line
        if random.random() < 0.15:
            _add_log(ds, random.choice(TERMINAL_LOG_LINES))

    p.progress = int(100 * p.dev_day / max(1, p.dev_total_days))
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"

    _add_log(
        ds,
        f"[{date_str}] Day {p.dev_day}/{p.dev_total_days} — "
        f"Design {p.design_score:.0f}  Tech {p.tech_score:.0f}  Bugs {p.bug_count}",
    )

    if p.dev_day >= p.dev_total_days and not ds.pending_interruption:
        _finalize_dev(gs, p)
        events.append(("💻", f"{p.name} dev complete! Ready for QA/Launch.", "good", date_str))

    return events


# ─────────────────────── INTERNAL HELPERS ─────────────────────


def _check_interruption(gs: GameState, p) -> None:
    ds = p.dev_session
    vibe_mult = get_vibe_multiplier(gs)
    for evt in DEV_INTERRUPTION_EVENTS:
        if random.random() < evt["prob"] * vibe_mult:
            ds.pending_interruption = evt
            ds.interruption_choice_idx = 0
            _add_log(ds, f"⚠️  INTERRUPTION: {evt['title']}")
            return


def _apply_effects(gs: GameState, p, effects: dict) -> str:
    msgs = []
    for key, val in effects.items():
        if key == "design_score":
            p.design_score = max(0.0, min(100.0, p.design_score + val))
            msgs.append(f"Design{val:+.0f}")
        elif key == "tech_score":
            p.tech_score = max(0.0, min(100.0, p.tech_score + val))
            msgs.append(f"Tech{val:+.0f}")
        elif key == "bug_count":
            p.bug_count = max(0, p.bug_count + val)
            msgs.append(f"Bugs{val:+d}")
        elif key == "hype":
            p.hype = max(0, min(100, p.hype + val))
            msgs.append(f"Hype{val:+d}")
        elif key == "vibe":
            add_vibe(gs, float(val))
            msgs.append(f"Vibe{val:+.0f}")
        elif key == "sanity":
            gs.founder.sanity = max(0, min(100, gs.founder.sanity + val))
            msgs.append(f"Sanity{val:+d}")
        elif key == "reputation":
            adjust_reputation(gs, val)
            msgs.append(f"Rep{val:+d}")
        elif key == "tokens_used":
            consume_tokens(gs, val)
            p.tokens_used += val
            msgs.append(f"+{val}K tokens")
        elif key == "dev_day":
            p.dev_day = max(0, p.dev_day + val)
            p.progress = int(100 * p.dev_day / max(1, p.dev_total_days))
            msgs.append(f"Days{val:+d}")
        elif key == "faked":
            feat_name = f"Feature {len(p.faked_features) + 1}"
            p.faked_features.append(feat_name)
            msgs.append("faked feature added")
    return " | ".join(msgs) if msgs else "no effect"


def _finalize_dev(gs: GameState, p) -> None:
    """Apply QA and derive quality_score. Sets status to 'Dev Complete'."""
    qa = next((q for q in QA_OPTIONS if q["name"] == p.qa_level), QA_OPTIONS[0])

    p.bug_count = max(0, int(p.bug_count * qa["bug_mult"]))

    if qa["critical_risk"] > 0 and random.random() < qa["critical_risk"]:
        p.bug_count += 5
        _add_log(p.dev_session, "⚠️  Full QA surfaced a critical flaw! +5 bugs.")

    c = gs.company_by_id(p.company_id)
    if c and qa["cost"] > 0:
        c.cash = max(0, c.cash - qa["cost"])

    bug_penalty = max(0, 50 - p.bug_count * 5)
    p.quality_score = int(p.design_score * 0.4 + p.tech_score * 0.4 + bug_penalty * 0.2)

    p.status = "Dev Complete"
    _add_log(
        p.dev_session,
        f"[Complete] Quality: {p.quality_score}/100  Hype: {p.hype}  "
        f"Bugs: {p.bug_count}  Faked: {len(p.faked_features)}",
    )


def _add_log(ds: DevSession, line: str) -> None:
    ds.terminal_log.append(line)
    if len(ds.terminal_log) > 20:
        ds.terminal_log = ds.terminal_log[-20:]


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("dev_start")
def _dev_start(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status != "In Dev":
        return ActionResult(ok=False, message=f"Project is not In Dev (status: {p.status}).")
    start_dev_session(gs, project_idx)
    return ActionResult(ok=True, message=f"Dev session started for {p.name}.")


@register("dev_do_action")
def _dev_do_action(gs: GameState, project_idx: int, action_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.dev_session is None:
        return ActionResult(ok=False, message="No active dev session.")
    if action_idx < 0 or action_idx >= len(DEV_ACTIONS):
        return ActionResult(ok=False, message="Invalid action.")

    action = DEV_ACTIONS[action_idx]
    c = gs.company_by_id(p.company_id)

    if action["cost"] > 0:
        avail = c.cash if c else 0
        if avail < action["cost"]:
            return ActionResult(ok=False, message=f"Need ${action['cost']:,} (have ${avail:,}).")
        c.cash -= action["cost"]

    msg = _apply_effects(gs, p, action["effects"])
    full_msg = f"{action['name']}: {msg}"
    _add_log(p.dev_session, f"> {full_msg}")
    p.dev_session.action_result = f"✓ {full_msg}"
    return ActionResult(ok=True, message=p.dev_session.action_result)


@register("dev_resolve_interruption")
def _dev_resolve_interruption(gs: GameState, project_idx: int, choice_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    ds = p.dev_session
    if ds is None or not ds.pending_interruption:
        return ActionResult(ok=False, message="No pending interruption.")
    choices = ds.pending_interruption.get("choices", [])
    if choice_idx < 0 or choice_idx >= len(choices):
        return ActionResult(ok=False, message="Invalid choice.")

    choice = choices[choice_idx]
    msg = _apply_effects(gs, p, choice["effects"])
    _add_log(ds, f"Resolved: {choice['label']} → {msg}")
    ds.pending_interruption = {}
    ds.interruption_choice_idx = 0
    ds.action_result = f"Resolved: {choice['label']}"
    return ActionResult(ok=True, message=ds.action_result)


@register("dev_set_qa")
def _dev_set_qa(gs: GameState, project_idx: int, qa_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    if qa_idx < 0 or qa_idx >= len(QA_OPTIONS):
        return ActionResult(ok=False, message="Invalid QA index.")
    p = gs.projects[project_idx]
    p.qa_level = QA_OPTIONS[qa_idx]["name"]
    return ActionResult(ok=True, message=f"QA set to: {p.qa_level}")


@register("dev_toggle_pause")
def _dev_toggle_pause(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    p.paused_dev = not p.paused_dev
    state = "paused" if p.paused_dev else "resumed"
    if p.dev_session:
        _add_log(p.dev_session, f"Development {state}.")
    return ActionResult(ok=True, message=f"Development {state}.")


@register("dev_launch")
def _dev_launch(gs: GameState, project_idx: int) -> ActionResult:
    if project_idx < 0 or project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project index.")
    p = gs.projects[project_idx]
    if p.status != "Dev Complete":
        return ActionResult(ok=False, message=f"Project not ready (status: {p.status}).")

    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    p.status = "Launched"
    p.launch_date = date_str

    # Initial MRR driven by hype × quality
    p.revenue = int((p.hype * 0.4 + p.quality_score * 0.6) * 4)

    adjust_reputation(gs, 3 + p.quality_score // 20)
    add_vibe(gs, 10.0)

    if p.faked_features:
        adjust_reputation(gs, -len(p.faked_features) * 2)

    return ActionResult(
        ok=True,
        message=f"{p.name} launched! Quality {p.quality_score}/100. Starting MRR: ${p.revenue:,}",
    )
