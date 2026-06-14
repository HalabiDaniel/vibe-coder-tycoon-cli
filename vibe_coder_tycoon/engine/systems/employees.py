"""
Phase 5 — Employees, Stats, Roles, Training
Candidate generation, hiring (cap/role/reputation gated), assignment to
projects, five-stat contribution to development, XP/leveling, and training.
"""

import random

from ...constants import (
    ROLE_CATALOG, CANDIDATE_FIRST_NAMES, CANDIDATE_LAST_NAMES,
    CANDIDATE_BACKSTORIES, EMPLOYEE_TRAITS, TRAINING_ACTIONS, xp_threshold,
    MONTH_NAMES,
)
from ...models import GameState, Employee
from ..actions import register, ActionResult
from .companies import get_office_employee_cap, get_all_unlocked_roles, get_office_data


STAT_KEYS = ("coding", "prompting", "research", "marketing", "sanity")


# ─────────────────────── CANDIDATE GENERATION ─────────────────


def _roll_stat(is_primary: bool, level: int) -> int:
    base = random.randint(55, 85) if is_primary else random.randint(25, 55)
    base += (level - 1) * random.randint(2, 5)
    return max(1, min(100, base))


def generate_candidate(gs: GameState, company_id: int, role: str = None) -> Employee:
    """Build one (un-hired) candidate Employee for a company."""
    unlocked = [r for r in get_all_unlocked_roles_safe(gs, company_id)]
    if not unlocked:
        unlocked = ["Vibe Coder"]
    if role is None or role not in ROLE_CATALOG:
        role = random.choice(unlocked)
    spec = ROLE_CATALOG.get(role, ROLE_CATALOG["Vibe Coder"])
    level = random.randint(1, 3)
    primary = set(spec["primary"])
    stats = {k: _roll_stat(k in primary, level) for k in STAT_KEYS}
    stats["sanity"] = random.randint(70, 95)  # fresh hires start rested
    lo, hi = spec["salary"]
    salary = int(random.randint(lo, hi) * (1 + 0.08 * (level - 1)))
    skill = int((stats["coding"] + stats["prompting"] + stats["research"]
                 + stats["marketing"]) / 4)
    name = f"{random.choice(CANDIDATE_FIRST_NAMES)} {random.choice(CANDIDATE_LAST_NAMES)}"
    return Employee(
        name=name,
        role=role,
        level=level,
        salary=salary,
        mood=random.randint(70, 90),
        skill=skill,
        hired_year=gs.year,
        company_id=company_id,
        trait=random.choice(EMPLOYEE_TRAITS),
        coding=stats["coding"],
        prompting=stats["prompting"],
        research=stats["research"],
        marketing=stats["marketing"],
        sanity=stats["sanity"],
        backstory=random.choice(CANDIDATE_BACKSTORIES),
    )


def get_all_unlocked_roles_safe(gs: GameState, company_id: int) -> list:
    c = gs.company_by_id(company_id)
    if c is None:
        return ["Vibe Coder"]
    return get_all_unlocked_roles(c)


def generate_candidates(gs: GameState, company_id: int, n: int = 4) -> list:
    return [generate_candidate(gs, company_id) for _ in range(n)]


# ─────────────────────── ASSIGNMENT / CONTRIBUTION ────────────


def get_team_for_project(gs: GameState, project_idx: int) -> list:
    """Active employees assigned to the given project index."""
    return [
        e for e in gs.employees
        if e.assigned_project_id == project_idx and e.state == "active"
    ]


def get_project_team_bonus(gs: GameState, project_idx: int) -> dict:
    """
    Multipliers derived from assigned employees' stats, fed into the
    development tick (Phase 2). No team → neutral 1.0 multipliers.
    """
    team = get_team_for_project(gs, project_idx)
    if not team:
        return {"design_mult": 1.0, "tech_mult": 1.0, "bug_mult": 1.0}

    design_sum = 0.0
    tech_sum = 0.0
    qa_sum = 0.0
    for e in team:
        design_sum += (e.prompting * 0.5 + e.coding * 0.3 + e.marketing * 0.2) / 100.0
        tech_sum += (e.coding * 0.6 + e.research * 0.4) / 100.0
        # Bug-hunting power: research-heavy roles reduce bugs most
        qa_sum += (e.research * 0.6 + e.coding * 0.4) / 100.0

    return {
        "design_mult": 1.0 + design_sum * 0.25,
        "tech_mult": 1.0 + tech_sum * 0.25,
        "bug_mult": max(0.3, 1.0 - qa_sum * 0.20),
    }


def get_post_launch_bonus(gs: GameState, company_id: int) -> dict:
    """
    Company-wide post-launch effects (Phase 5 → Phase 3 hook):
    Community Wizards reduce churn; marketing-strong staff boost hype/growth.
    """
    churn_mult = 1.0
    hype_bonus = 0.0
    for e in gs.employees_for_company(company_id):
        if e.state != "active":
            continue
        if e.role == "Community Wizard":
            churn_mult *= 0.92
        if e.role in ("Growth Goblin", "Pixel Artist"):
            hype_bonus += e.marketing / 100.0 * 2.0
    return {"churn_mult": max(0.4, churn_mult), "hype_bonus": hype_bonus}


# ─────────────────────── XP / LEVELING ────────────────────────


def award_project_xp(gs: GameState, project_idx: int, amount: int = 60) -> list:
    """Grant XP to a project's team on dev completion. Returns event tuples."""
    events = []
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    for e in get_team_for_project(gs, project_idx):
        e.xp += amount
        while e.xp >= xp_threshold(e.level):
            e.xp -= xp_threshold(e.level)
            e.level += 1
            spec = ROLE_CATALOG.get(e.role)
            primary = set(spec["primary"]) if spec else set()
            for stat in ("coding", "prompting", "research", "marketing"):
                gain = 4 if stat in primary else 2
                setattr(e, stat, min(100, getattr(e, stat) + gain))
            e.salary = int(e.salary * 1.10)
            e.skill = min(100, e.skill + 3)
            events.append(("⭐", f"{e.name} leveled up to Lv{e.level}!", "good", date_str))
    return events


# ─────────────────────── PAYROLL ──────────────────────────────


def company_payroll(gs: GameState, company_id: int) -> int:
    return sum(e.salary for e in gs.employees_for_company(company_id))


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("hire_employee")
def _hire_employee(gs: GameState, company_id: int, candidate) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")

    cap = get_office_employee_cap(c)
    count = len(gs.employees_for_company(company_id))
    if count >= cap:
        return ActionResult(
            ok=False,
            message=f"Office full ({count}/{cap}). Upgrade office to hire more.",
        )

    role = candidate.role if isinstance(candidate, Employee) else candidate.get("role")
    spec = ROLE_CATALOG.get(role)
    if spec is None:
        return ActionResult(ok=False, message=f"Unknown role: {role}.")

    if role not in get_all_unlocked_roles(c):
        need = spec["office_level"]
        return ActionResult(
            ok=False,
            message=f"{role} unlocks at office level {need}. Upgrade the office first.",
        )

    if gs.founder.reputation < spec["min_reputation"]:
        return ActionResult(
            ok=False,
            message=f"{role} won't join — needs reputation ≥ {spec['min_reputation']} "
                    f"(you have {gs.founder.reputation}).",
        )

    if not isinstance(candidate, Employee):
        return ActionResult(ok=False, message="Invalid candidate.")

    candidate.company_id = company_id
    candidate.hired_year = gs.year
    candidate.assigned_project_id = -1
    candidate.state = "active"
    gs.employees.append(candidate)
    return ActionResult(
        ok=True,
        message=f"Hired {candidate.name} as {role} (${candidate.salary:,}/mo).",
    )


@register("assign_employee")
def _assign_employee(gs: GameState, emp_index: int, project_idx: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    e = gs.employees[emp_index]
    if project_idx < 0:
        e.assigned_project_id = -1
        return ActionResult(ok=True, message=f"{e.name} unassigned.")
    if project_idx >= len(gs.projects):
        return ActionResult(ok=False, message="Invalid project.")
    p = gs.projects[project_idx]
    if p.company_id != e.company_id:
        return ActionResult(ok=False, message=f"{e.name} can only work on their own company's projects.")
    e.assigned_project_id = project_idx
    return ActionResult(ok=True, message=f"{e.name} assigned to {p.name}.")


@register("unassign_employee")
def _unassign_employee(gs: GameState, emp_index: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    e = gs.employees[emp_index]
    e.assigned_project_id = -1
    return ActionResult(ok=True, message=f"{e.name} unassigned.")


@register("train_employee")
def _train_employee(gs: GameState, emp_index: int, training_idx: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    if training_idx < 0 or training_idx >= len(TRAINING_ACTIONS):
        return ActionResult(ok=False, message="Invalid training.")
    e = gs.employees[emp_index]
    t = TRAINING_ACTIONS[training_idx]
    c = gs.company_by_id(e.company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if c.cash < t["cost"]:
        return ActionResult(ok=False, message=f"Need ${t['cost']:,} (company has ${c.cash:,}).")

    c.cash -= t["cost"]
    msgs = []
    for stat, val in t["effects"].items():
        cur = getattr(e, stat)
        setattr(e, stat, max(0, min(100, cur + val)))
        msgs.append(f"{stat[:4].title()}{val:+d}")
    e.skill = int((e.coding + e.prompting + e.research + e.marketing) / 4)
    return ActionResult(ok=True, message=f"{e.name} — {t['name']}: {' '.join(msgs)}")


@register("fire_employee")
def _fire_employee(gs: GameState, emp_index: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    e = gs.employees.pop(emp_index)
    # Reassignment: indices into gs.projects are unaffected (no project removed),
    # but employee list indices shift — assignment ids are project ids, so fine.
    return ActionResult(ok=True, message=f"{e.name} laid off. ${e.salary:,}/mo payroll freed.")


@register("rest_employee")
def _rest_employee(gs: GameState, emp_index: int) -> ActionResult:
    if emp_index < 0 or emp_index >= len(gs.employees):
        return ActionResult(ok=False, message="Invalid employee.")
    e = gs.employees[emp_index]
    e.sanity = min(100, e.sanity + 15)
    e.mood = min(100, e.mood + 15)
    return ActionResult(ok=True, message=f"{e.name} took a rest day. Sanity & mood restored.")
