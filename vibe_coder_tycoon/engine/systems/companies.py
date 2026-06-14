"""
Phase 4 — Company System and Offices
Focus restrictions, office upgrades, legal structure upgrades, synergy bonuses.
"""

from ...constants import COMPANY_FOCUSES, COMPANY_LEGAL_STRUCTURES, OFFICE_LEVELS
from ...models import GameState, Company
from ..actions import register, ActionResult


# ─────────────────────── LOOKUP HELPERS ───────────────────────


def get_focus_data(focus_name: str) -> dict | None:
    for f in COMPANY_FOCUSES:
        if f["name"] == focus_name:
            return f
    return None


def get_legal_data(legal_name: str) -> dict | None:
    for s in COMPANY_LEGAL_STRUCTURES:
        if s["name"] == legal_name or s["short"] == legal_name:
            return s
    return None


def get_office_data(level: int) -> dict | None:
    for o in OFFICE_LEVELS:
        if o["level"] == level:
            return o
    if level > OFFICE_LEVELS[-1]["level"]:
        return OFFICE_LEVELS[-1]
    return OFFICE_LEVELS[0]


def can_build_project_type(c: Company, ptype: str) -> tuple:
    """Returns (allowed: bool, reason: str)."""
    focus = get_focus_data(c.focus_area)
    if focus is None:
        return True, ""  # unknown focus → no restrictions
    allowed_types = focus["can_build"]
    if not allowed_types:
        return False, f"{c.focus_area} companies cannot build products."
    if ptype not in allowed_types:
        return False, f"{c.focus_area} only allows: {', '.join(allowed_types[:3])}..."
    return True, ""


def get_office_employee_cap(c: Company) -> int:
    data = get_office_data(c.office_level)
    return data["max_employees"] if data else 2


def get_all_unlocked_roles(c: Company) -> list:
    roles = []
    for o in OFFICE_LEVELS:
        if o["level"] <= c.office_level:
            roles.extend(o["unlocked_roles"])
        else:
            break
    return roles


def next_legal_structure(current_name: str) -> dict | None:
    for i, s in enumerate(COMPANY_LEGAL_STRUCTURES):
        if s["name"] == current_name or s["short"] == current_name:
            if i < len(COMPANY_LEGAL_STRUCTURES) - 1:
                return COMPANY_LEGAL_STRUCTURES[i + 1]
            return None
    return None


def is_vc_eligible(c: Company) -> bool:
    """A company can raise VC only if its legal structure permits it."""
    legal = get_legal_data(c.legal_style)
    return bool(legal and legal.get("vc_eligible", False))


def is_ipo_eligible(c: Company) -> bool:
    """A company can IPO only if its legal structure permits it."""
    legal = get_legal_data(c.legal_style)
    return bool(legal and legal.get("ipo_eligible", False))


def get_synergy_bonus(gs: GameState, company: Company) -> float:
    """
    Returns a multiplier (0.9 = 10% token/cost reduction) if a synergy partner
    company exists anywhere in the portfolio.
    """
    focus = get_focus_data(company.focus_area)
    if focus is None:
        return 1.0
    synergy_target = focus.get("synergy_with")
    if not synergy_target:
        return 1.0
    for c in gs.companies:
        if c.id != company.id and c.active and c.focus_area == synergy_target:
            return 0.9
    return 1.0


# ─────────────────────── REGISTERED ACTIONS ───────────────────


@register("upgrade_office")
def _upgrade_office(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")

    current_data = get_office_data(c.office_level)
    if current_data is None:
        return ActionResult(ok=False, message="Office data not found.")

    upgrade_cost = current_data.get("upgrade_cost", 0)
    if upgrade_cost == 0:
        return ActionResult(ok=False, message="Already at maximum office level.")

    next_data = get_office_data(c.office_level + 1)
    if next_data is None or next_data["level"] <= c.office_level:
        return ActionResult(ok=False, message="Already at maximum office level.")

    if c.cash < upgrade_cost:
        return ActionResult(ok=False,
                            message=f"Need ${upgrade_cost:,} to upgrade. Company has ${c.cash:,}.")

    c.cash -= upgrade_cost
    c.office_level += 1
    new_roles = next_data.get("unlocked_roles", [])
    role_msg = f" Unlocked: {', '.join(new_roles)}." if new_roles else ""
    entry = f"Office upgraded to Lv{c.office_level}: {next_data['name']}"
    c.history.append(entry)
    return ActionResult(ok=True,
                        message=f"Upgraded to Level {c.office_level}: {next_data['name']}!{role_msg}")


@register("upgrade_legal")
def _upgrade_legal(gs: GameState, company_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")

    next_struct = next_legal_structure(c.legal_style)
    if next_struct is None:
        return ActionResult(ok=False, message="Already at maximum legal structure.")

    if c.cash < next_struct["unlock_cash"]:
        return ActionResult(ok=False,
                            message=f"Need ${next_struct['unlock_cash']:,} in company cash to upgrade.")

    req = next_struct.get("unlock_research")
    if req and req not in gs.founder.unlocked_research:
        return ActionResult(ok=False, message=f"Requires research: '{req}' first.")

    old = c.legal_style
    c.legal_style = next_struct["name"]
    c.history.append(f"Legal: {old} → {next_struct['name']}")
    return ActionResult(ok=True, message=f"Upgraded from {old} to {next_struct['name']}!")


@register("transfer_between_companies")
def _transfer_between_companies(gs: GameState, from_id: int, to_id: int,
                                amount: int) -> ActionResult:
    """
    Move cash from one company to another. Used for holding-company treasury
    management (e.g., sweeping subsidiary cash up to the parent, or funding a
    subsidiary from the parent).
    """
    if from_id == to_id:
        return ActionResult(ok=False, message="Source and destination must differ.")

    src = gs.company_by_id(from_id)
    dst = gs.company_by_id(to_id)
    if src is None or dst is None:
        return ActionResult(ok=False, message="Company not found.")
    if not src.active or not dst.active:
        return ActionResult(ok=False, message="Both companies must be active.")

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return ActionResult(ok=False, message="Invalid amount.")
    if amount <= 0:
        return ActionResult(ok=False, message="Enter a positive amount.")

    # Transfers are only allowed within the same holding group: the two companies
    # must be parent↔subsidiary or share the same parent.
    if not _same_holding_group(src, dst):
        return ActionResult(ok=False,
                            message="Companies must belong to the same holding group.")

    if src.cash < amount:
        return ActionResult(ok=False,
                            message=f"{src.name} has only ${src.cash:,}.")

    src.cash -= amount
    dst.cash += amount
    src.history.append(f"Transferred ${amount:,} → {dst.name}")
    dst.history.append(f"Received ${amount:,} ← {src.name}")
    return ActionResult(ok=True,
                        message=f"Transferred ${amount:,} from {src.name} to {dst.name}.")


def _same_holding_group(a: Company, b: Company) -> bool:
    """True if a and b are parent↔subsidiary or siblings under one holding."""
    if a.parent_company_id == b.id or b.parent_company_id == a.id:
        return True
    if (a.parent_company_id >= 0 and a.parent_company_id == b.parent_company_id):
        return True
    return False


@register("set_parent_company")
def _set_parent_company(gs: GameState, company_id: int, parent_id: int) -> ActionResult:
    c = gs.company_by_id(company_id)
    if c is None:
        return ActionResult(ok=False, message="Company not found.")
    if parent_id == company_id:
        return ActionResult(ok=False, message="A company cannot be its own parent.")

    if parent_id >= 0:
        parent = gs.company_by_id(parent_id)
        if parent is None:
            return ActionResult(ok=False, message="Parent company not found.")
        if parent.focus_area != "Holding Company":
            return ActionResult(ok=False, message=f"{parent.name} is not a Holding Company.")

    c.parent_company_id = parent_id
    if parent_id >= 0:
        parent = gs.company_by_id(parent_id)
        return ActionResult(ok=True, message=f"{c.name} is now a subsidiary of {parent.name}.")
    return ActionResult(ok=True, message=f"{c.name} is now independent.")
