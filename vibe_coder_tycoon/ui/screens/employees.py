import curses
from dataclasses import dataclass, field

from ..colors import *
from ..helpers import *
from ...constants import ROLE_CATALOG, TRAINING_ACTIONS, xp_threshold, CONDITIONS
from ...models import GameState
from ...engine.systems.companies import get_office_employee_cap, get_all_unlocked_roles


# ─────────────────────── EMPLOYEES TAB ────────────────────────

@dataclass
class EmployeesUIState:
    selected: int = 0
    filter_company: int = -1   # -1 = all
    view: str = "list"         # list | hire | assign | train
    candidates: list = field(default_factory=list)
    cand_sel: int = 0
    assign_sel: int = 0
    train_sel: int = 0
    hire_company_id: int = -1
    message: str = ""


def _stat_cell(win, y, x, label, val):
    p = PAIR_ACCENT if val >= 60 else PAIR_WARN if val >= 35 else PAIR_DANGER
    safe_addstr(win, y, x, f"{label}", curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y, x + 5, f"{val:>3}", curses.color_pair(p) | curses.A_BOLD)
    progress_bar(win, y, x + 9, 8, val, p, PAIR_MUTED)


def draw_employees(win, gs: GameState, ui: EmployeesUIState):
    if ui.view == "hire":
        _draw_hire(win, gs, ui)
        return
    if ui.view == "assign":
        _draw_assign(win, gs, ui)
        return
    if ui.view == "train":
        _draw_train(win, gs, ui)
        return
    _draw_list(win, gs, ui)


def _draw_list(win, gs: GameState, ui: EmployeesUIState):
    h, w = win.getmaxyx()
    y = 3

    safe_addstr(win, y, 2, " EMPLOYEES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, w - 22, "[ H: Hire Talent ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    header = f"  {'NAME':<18} {'ROLE':<17} {'LVL':>3} {'SALARY':>8} {'XP':>9} {'STATE':<11} {'ASSIGNED':<16}"
    hline(win, y, 1, w - 2, PAIR_BORDER)
    safe_addstr(win, y, 2, header, curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    hline(win, y, 1, w - 2, PAIR_BORDER)
    y += 1

    list_cap = max(3, h - y - 16)
    for i, emp in enumerate(gs.employees[:list_cap]):
        is_sel = (i == ui.selected)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        if emp.assigned_project_id >= 0 and emp.assigned_project_id < len(gs.projects):
            assigned = gs.projects[emp.assigned_project_id].name[:15]
        else:
            assigned = "—"
        if emp.state == "touch_grass":
            state = "🌴 grass"
        elif emp.condition:
            state = f"🧠 {emp.condition[:8]}"
        else:
            state = "active"
        xp_need = xp_threshold(emp.level)
        row = (f"  {emp.name:<18} {emp.role:<17} "
               f"{'★'*min(emp.level,3):<3} ${emp.salary:>7,} "
               f"{emp.xp:>4}/{xp_need:<4} {state:<11} {assigned:<16}")
        safe_addstr(win, y, 1, " " * (w - 2), curses.color_pair(rp))
        safe_addstr(win, y, 2, row, curses.color_pair(rp))
        y += 1

    y += 1
    hline(win, y, 1, w - 2, PAIR_BORDER)
    y += 1

    # Detail / actions for selected employee
    if gs.employees and 0 <= ui.selected < len(gs.employees):
        emp = gs.employees[ui.selected]
        mid = w // 2

        safe_addstr(win, y, 2, f" {emp.name} — {emp.role} ",
                    curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
        sy = y + 1
        _stat_cell(win, sy,     4, "CODE", emp.coding);     _stat_cell(win, sy,     mid - 24, "PROM", emp.prompting)
        _stat_cell(win, sy + 1, 4, "RSCH", emp.research);   _stat_cell(win, sy + 1, mid - 24, "MKTG", emp.marketing)
        _stat_cell(win, sy + 2, 4, "SANE", emp.sanity)
        safe_addstr(win, sy + 3, 4, f"Level {emp.level}   Mood {emp.mood}%   Trait: {emp.trait or 'None'}",
                    curses.color_pair(PAIR_MUTED))
        # Phase 6: condition + resolution hint
        if emp.condition:
            info = CONDITIONS.get(emp.condition, {})
            cp = PAIR_DANGER if info.get("stat_mult", 1) < 1 else PAIR_WARN
            safe_addstr(win, sy + 4, 4, f"🧠 {emp.condition}: {info.get('effect', '')}"[:mid - 6],
                        curses.color_pair(cp) | curses.A_BOLD)
            safe_addstr(win, sy + 5, 6, f"→ Fix: {info.get('resolution', '')}"[:mid - 8],
                        curses.color_pair(PAIR_MUTED))
        elif emp.backstory:
            safe_addstr(win, sy + 4, 4, emp.backstory[:mid - 8], curses.color_pair(PAIR_MUTED) | curses.A_DIM)

        # Right: actions
        actions = ["Enter: Assign to Project", "U: Unassign", "T: Train",
                   "R: Rest Day", "I: Inspire", "G: Distraction", "F: Lay Off"]
        rx = mid + 2
        ry = y + 1
        for a in actions:
            safe_addstr(win, ry, rx, f"[ {a} ]", curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
            ry += 1

    # Payroll / cap summary
    total_sal = sum(e.salary for e in gs.employees)
    safe_addstr(win, h - 5, 2, f"Total Payroll: ${total_sal:,}/mo",
                curses.color_pair(PAIR_WARN) | curses.A_BOLD)
    caps = []
    for c in gs.active_companies():
        cnt = len(gs.employees_for_company(c.id))
        caps.append(f"{c.name[:12]} {cnt}/{get_office_employee_cap(c)}")
    safe_addstr(win, h - 4, 2, "  ".join(caps)[:w - 4], curses.color_pair(PAIR_MUTED))
    if ui.message:
        safe_addstr(win, h - 6, 2, ui.message[:w - 4], curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2,
                "Up/Dn select | H hire | Enter assign | U unassign | T train | R rest | I inspire | G distract | F fire",
                curses.color_pair(PAIR_MUTED))


def _draw_hire(win, gs: GameState, ui: EmployeesUIState):
    h, w = win.getmaxyx()
    y = 3
    c = gs.company_by_id(ui.hire_company_id)
    cname = c.name if c else "—"
    safe_addstr(win, y, 2, f" HIRE TALENT — {cname} ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    if c:
        cnt = len(gs.employees_for_company(c.id))
        safe_addstr(win, y, w - 30, f"Capacity {cnt}/{get_office_employee_cap(c)}  Rep {gs.founder.reputation}",
                    curses.color_pair(PAIR_MUTED))
    y += 2
    safe_addstr(win, y, 2, "Candidates (R: reroll, Enter: hire, Esc: back):",
                curses.color_pair(PAIR_MUTED))
    y += 2

    unlocked = get_all_unlocked_roles(c) if c else []
    for i, cand in enumerate(ui.candidates):
        is_sel = (i == ui.cand_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        spec = ROLE_CATALOG.get(cand.role, {})
        locked = cand.role not in unlocked
        rep_block = gs.founder.reputation < spec.get("min_reputation", 0)
        tag = ""
        if locked:
            tag = "  🔒 office level"
        elif rep_block:
            tag = f"  🔒 needs rep {spec.get('min_reputation')}"
        safe_addstr(win, y, 2, " " * (w - 4), curses.color_pair(rp))
        safe_addstr(win, y, 3,
                    f"{cand.name:<18} {cand.role:<17} Lv{cand.level}  ${cand.salary:,}/mo{tag}",
                    curses.color_pair(rp) | curses.A_BOLD)
        safe_addstr(win, y + 1, 5,
                    f"CODE {cand.coding}  PROM {cand.prompting}  RSCH {cand.research}  "
                    f"MKTG {cand.marketing}  SANE {cand.sanity}",
                    curses.color_pair(rp))
        safe_addstr(win, y + 2, 5, cand.backstory[:w - 8], curses.color_pair(PAIR_MUTED) | curses.A_DIM)
        y += 4

    if ui.message:
        safe_addstr(win, h - 4, 2, ui.message[:w - 4], curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2, "Up/Down: select  |  Enter: hire  |  R: reroll  |  Esc: back",
                curses.color_pair(PAIR_MUTED))


def _draw_assign(win, gs: GameState, ui: EmployeesUIState):
    h, w = win.getmaxyx()
    y = 3
    emp = gs.employees[ui.selected] if 0 <= ui.selected < len(gs.employees) else None
    if emp is None:
        safe_addstr(win, y, 2, "No employee selected.", curses.color_pair(PAIR_WARN))
        return
    safe_addstr(win, y, 2, f" ASSIGN {emp.name} ({emp.role}) ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2
    options = _assignable_projects(gs, emp)
    safe_addstr(win, y, 2, "Select a project (Enter to assign, Esc to cancel):",
                curses.color_pair(PAIR_MUTED))
    y += 2
    if not options:
        safe_addstr(win, y, 4, "No in-dev / launched projects for this company.",
                    curses.color_pair(PAIR_WARN))
    for i, (pidx, label) in enumerate(options):
        is_sel = (i == ui.assign_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        safe_addstr(win, y, 2, " " * (w - 4), curses.color_pair(rp))
        safe_addstr(win, y, 4, label, curses.color_pair(rp) | curses.A_BOLD)
        y += 1
    safe_addstr(win, h - 3, 2, "Up/Down: select  |  Enter: assign  |  Esc: cancel",
                curses.color_pair(PAIR_MUTED))


def _assignable_projects(gs: GameState, emp):
    out = [(-1, "— Unassign —")]
    for pidx, p in enumerate(gs.projects):
        if p.company_id == emp.company_id and p.status in ("In Dev", "Dev Complete", "Launched", "Growing"):
            mark = "● " if emp.assigned_project_id == pidx else "  "
            out.append((pidx, f"{mark}{p.name}  [{p.status}]"))
    return out


def _draw_train(win, gs: GameState, ui: EmployeesUIState):
    h, w = win.getmaxyx()
    y = 3
    emp = gs.employees[ui.selected] if 0 <= ui.selected < len(gs.employees) else None
    if emp is None:
        safe_addstr(win, y, 2, "No employee selected.", curses.color_pair(PAIR_WARN))
        return
    c = gs.company_by_id(emp.company_id)
    cash = c.cash if c else 0
    safe_addstr(win, y, 2, f" TRAIN {emp.name} ({emp.role}) ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(win, y, w - 26, f"Company cash: ${cash:,}", curses.color_pair(PAIR_MUTED))
    y += 2
    for i, t in enumerate(TRAINING_ACTIONS):
        is_sel = (i == ui.train_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        eff = "  ".join(f"{k[:4].title()}{v:+d}" for k, v in t["effects"].items())
        afford = "" if cash >= t["cost"] else "  (can't afford)"
        safe_addstr(win, y, 2, " " * (w - 4), curses.color_pair(rp))
        safe_addstr(win, y, 4, f"{t['name']:<18} ${t['cost']:<5,}  {eff}{afford}",
                    curses.color_pair(rp) | curses.A_BOLD)
        safe_addstr(win, y + 1, 6, t["desc"], curses.color_pair(PAIR_MUTED) | curses.A_DIM)
        y += 3
    if ui.message:
        safe_addstr(win, h - 4, 2, ui.message[:w - 4], curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    safe_addstr(win, h - 3, 2, "Up/Down: select  |  Enter: train  |  Esc: back",
                curses.color_pair(PAIR_MUTED))
