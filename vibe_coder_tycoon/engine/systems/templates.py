"""
Phase 8 — Templates

Company-scoped internal assets that boost future development. A template is
*built* through the normal development phase (a small, no-launch build); on
completion its bonuses are derived from the Design/Tech scores achieved, so a
template built later with better models/IDEs/teams comes out stronger. A
project may then opt into one template (company-filtered) for a head start on
its Design/Tech scores, a shorter timeline, and fewer bugs.
"""

from ...constants import TEMPLATE_TYPES, MONTH_NAMES
from ...models import GameState, Project, Template
from ..actions import register, ActionResult


# ─────────────────────── LOOKUP HELPERS ───────────────────────


def get_template_def(template_type: str) -> dict | None:
    for t in TEMPLATE_TYPES:
        if t["name"] == template_type:
            return t
    return None


def get_template(gs: GameState, template_id: int) -> Template | None:
    if 0 <= template_id < len(gs.templates):
        return gs.templates[template_id]
    return None


def templates_for_company(gs: GameState, company_id: int) -> list:
    return [t for t in gs.templates if t.company_id == company_id]


def next_template_version(gs: GameState, company_id: int, template_type: str) -> int:
    existing = [t.version for t in gs.templates
                if t.company_id == company_id and t.template_type == template_type]
    return (max(existing) + 1) if existing else 1


def apply_template_to_project(gs: GameState, p: Project) -> None:
    """Apply a chosen template's head-start bonuses at dev-session start.
    Safe to call when the project uses no template (no-op)."""
    t = get_template(gs, getattr(p, "template_id", -1))
    if t is None:
        return
    if t.company_id != p.company_id:
        return  # company-scope guard: never apply another company's template
    p.dev_total_days = max(5, int(round(p.dev_total_days * (1.0 - t.time_reduction))))
    p.design_score = max(p.design_score, t.design_bonus)
    p.tech_score = max(p.tech_score, t.tech_bonus)


def template_bug_multiplier(gs: GameState, p: Project) -> float:
    """Per-tick bug-generation multiplier from a project's template (1.0 = none)."""
    t = get_template(gs, getattr(p, "template_id", -1))
    if t is None or t.company_id != p.company_id:
        return 1.0
    return max(0.0, 1.0 - t.bug_reduction)


# ─────────────────────── BUILD COMPLETION ─────────────────────


def finalize_template(gs: GameState, p: Project) -> Template:
    """Convert a completed template-build project into a Template asset.
    Bonus strength scales with the Design/Tech scores reached during the build
    (and is dragged down by leftover bugs), so better tools → stronger template.
    """
    ttype = p.template_type or "SaaS Boilerplate"
    version = next_template_version(gs, p.company_id, ttype)

    bug_drag = max(0.0, 1.0 - p.bug_count * 0.03)   # bugs sap the template's polish
    design_bonus = round(p.design_score * 0.15 * bug_drag, 1)
    tech_bonus = round(p.tech_score * 0.15 * bug_drag, 1)
    time_reduction = round(min(0.30, p.tech_score / 400.0) * bug_drag, 3)
    bug_reduction = round(min(0.50, (p.design_score + p.tech_score) / 400.0) * bug_drag, 3)

    t = Template(
        name=f"{ttype} v{version}",
        template_type=ttype,
        version=version,
        company_id=p.company_id,
        design_bonus=design_bonus,
        tech_bonus=tech_bonus,
        time_reduction=time_reduction,
        bug_reduction=bug_reduction,
        built_year=gs.year,
    )
    gs.templates.append(t)
    p.status = "Template"
    p.template_id = len(gs.templates) - 1
    p.revenue = 0
    p.users = 0
    return t


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("build_template")
def _build_template(gs: GameState, company_id: int, template_type: str) -> ActionResult:
    from .development import start_dev_session  # lazy to avoid init-time cycle

    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    tdef = get_template_def(template_type)
    if tdef is None:
        return ActionResult(ok=False, message=f"Unknown template type: {template_type}.")
    if c.cash < tdef["build_cost"]:
        return ActionResult(ok=False,
                            message=f"Need ${tdef['build_cost']:,} to build (have ${c.cash:,}).")

    c.cash -= tdef["build_cost"]
    p = Project(
        name=f"{template_type} (build)",
        ptype="Developer Tool",
        model=gs.active_model or "",
        stack="Internal",
        niche="Internal Tooling",
        company_id=company_id,
        status="In Dev",
        progress=0,
        revenue=0, users=0, morale=80, tokens_used=0,
        scope="Lean MVP",
        is_template=True,
        template_type=template_type,
        dev_total_days=tdef["base_days"],
    )
    gs.projects.append(p)
    p_idx = len(gs.projects) - 1
    start_dev_session(gs, p_idx)
    # start_dev_session resets dev_total_days from the scope table; restore the
    # template build length.
    p.dev_total_days = tdef["base_days"]

    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    gs.events.insert(0, ("🧩", f"Template build started: {template_type}", "good", date_str))
    return ActionResult(
        ok=True,
        message=f"Building {template_type} ({tdef['base_days']} days). Manage it in the dev dashboard.",
    )
