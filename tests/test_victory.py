"""
Phase 14 — Victory, Bankruptcy, Endgame tests.

Covers: milestone triggers + persistence, company bankruptcy timer and its
consequences (close, discontinue, lose staff, default loans, graveyard log),
trillionaire and token-singularity victory thresholds, the game-over insolvency
timer, continue-after-win, and persistence round-trip of the new fields.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vibe_coder_tycoon.engine import make_new_game, dispatch
from vibe_coder_tycoon.models import Founder, Project, Employee, Loan
from vibe_coder_tycoon.engine.systems import victory
from vibe_coder_tycoon.constants import (
    TRILLIONAIRE_THRESHOLD, TOKEN_SINGULARITY_THRESHOLD,
    BANKRUPTCY_MONTHS, GAME_OVER_MONTHS,
)
from vibe_coder_tycoon.persistence import _gs_to_dict, _dict_to_gs


def _gs(reputation=50, year=2030):
    f = Founder(username="Tester", background_idx=0, reputation=reputation,
                burnout=0, skill_prototyping=50, skill_sales=30,
                skill_tech=40, skill_management=30, total_tokens_used=0)
    gs = make_new_game(f, 3)
    gs.year = year
    return gs


def _add_project(gs, company_id=0, status="Launched", lifetime_revenue=0):
    p = Project(name="Widget", ptype="SaaS Tool", model="GPT", stack="Py",
                niche="b2b", company_id=company_id, status=status, progress=100,
                revenue=0, users=0, morale=80, tokens_used=0)
    p.lifetime_revenue = lifetime_revenue
    gs.projects.append(p)
    return p


# ─────────────────────── MILESTONES ───────────────────────────

def test_milestone_first_company_fires():
    gs = _gs()
    events = victory.check_milestones(gs)
    titles = [e[1] for e in events]
    assert any("Incorporated" in t for t in titles)
    assert "Incorporated" in gs.founder.achievements


def test_milestone_fires_once_only():
    gs = _gs()
    victory.check_milestones(gs)
    count_before = gs.founder.achievements.count("Incorporated")
    victory.check_milestones(gs)
    assert gs.founder.achievements.count("Incorporated") == count_before == 1


def test_milestone_first_1k_revenue():
    gs = _gs()
    _add_project(gs, lifetime_revenue=1500)
    victory.check_milestones(gs)
    assert "First $1K" in gs.founder.achievements
    assert "Ship It!" in gs.founder.achievements  # launched product too


def test_milestone_net_worth_millionaire():
    gs = _gs()
    gs.founder.personal_cash = 2_000_000
    victory.check_milestones(gs)
    assert "Millionaire" in gs.founder.achievements


# ─────────────────────── BANKRUPTCY ───────────────────────────

def test_bankruptcy_timer_threshold():
    gs = _gs()
    c = gs.companies[0]
    c.months_negative = BANKRUPTCY_MONTHS - 1
    events = victory.process_bankruptcies(gs)
    assert c.active is True
    assert events == []
    c.months_negative = BANKRUPTCY_MONTHS
    events = victory.process_bankruptcies(gs)
    assert c.active is False
    assert any("bankrupt" in e[1].lower() for e in events)


def test_bankruptcy_consequences():
    gs = _gs()
    c = gs.companies[0]
    p = _add_project(gs, company_id=c.id, status="Launched")
    p.active_users = 500
    emp = Employee(name="Dev", role="Engineer", level=2, salary=4000, mood=70,
                   skill=60, hired_year=2030, company_id=c.id)
    gs.employees.append(emp)
    c.loans.append(Loan(lender="VibeBank", principal=10000, balance=8000,
                        rate=0.08, term_months=12, company_id=c.id,
                        monthly_payment=700))
    c.months_negative = BANKRUPTCY_MONTHS
    rep_before = gs.founder.reputation

    victory.process_bankruptcies(gs)

    assert c.active is False
    assert p.discontinued is True and p.status == "Sunset"
    assert p.active_users == 0
    assert len(gs.employees_for_company(c.id)) == 0
    assert c.loans[0].balance == 0
    assert gs.loan_default_count >= 1
    assert gs.founder.reputation < rep_before
    assert len(gs.graveyard) == 1
    assert gs.graveyard[0]["name"] == c.name


# ─────────────────────── VICTORY ──────────────────────────────

def test_trillionaire_victory():
    gs = _gs()
    gs.founder.personal_cash = float(TRILLIONAIRE_THRESHOLD)
    victory.check_endgame(gs)
    assert gs.victory is True
    assert gs.victory_type == "trillionaire"


def test_token_singularity_victory():
    gs = _gs()
    gs.founder.total_tokens_used = TOKEN_SINGULARITY_THRESHOLD
    victory.check_endgame(gs)
    assert gs.victory is True
    assert gs.victory_type == "token_singularity"


def test_peak_net_worth_tracked():
    gs = _gs()
    gs.founder.personal_cash = 50_000
    victory.check_endgame(gs)
    assert gs.peak_net_worth >= 50_000
    gs.founder.personal_cash = 10_000
    victory.check_endgame(gs)
    # peak should not drop
    assert gs.peak_net_worth >= 50_000


def test_continue_after_win_action():
    gs = _gs()
    gs.founder.personal_cash = float(TRILLIONAIRE_THRESHOLD)
    victory.check_endgame(gs)
    res = dispatch(gs, "continue_after_win")
    assert res.ok is True
    assert gs.endgame_continue is True


# ─────────────────────── GAME OVER ────────────────────────────

def test_game_over_insolvency_timer():
    gs = _gs()
    gs.founder.personal_cash = 0
    # Mark the only company underwater so the player is fully broke.
    gs.companies[0].months_negative = 3
    for _ in range(GAME_OVER_MONTHS - 1):
        victory.check_endgame(gs)
    assert gs.game_over is False
    victory.check_endgame(gs)
    assert gs.game_over is True
    assert "Insolvent" in gs.game_over_reason


def test_game_over_timer_resets_when_solvent():
    gs = _gs()
    gs.founder.personal_cash = 0
    gs.companies[0].months_negative = 3
    victory.check_endgame(gs)
    assert gs.broke_months == 1
    # Become solvent again
    gs.founder.personal_cash = 5000
    victory.check_endgame(gs)
    assert gs.broke_months == 0
    assert gs.game_over is False


# ─────────────────────── PERSISTENCE ──────────────────────────

def test_endgame_fields_round_trip():
    gs = _gs()
    gs.peak_net_worth = 12345.0
    gs.victory = True
    gs.victory_type = "trillionaire"
    gs.endgame_continue = True
    gs.game_over = False
    gs.broke_months = 4
    gs.graveyard = [{"name": "DeadCo", "founded_year": 2030, "closed_year": 2031,
                     "products": ["X"], "staff_lost": 2, "lifetime_revenue": 0,
                     "cause": "Bankruptcy"}]
    data = _gs_to_dict(gs, "Tester")
    gs2 = _dict_to_gs(data)
    assert gs2.peak_net_worth == 12345.0
    assert gs2.victory is True
    assert gs2.victory_type == "trillionaire"
    assert gs2.endgame_continue is True
    assert gs2.broke_months == 4
    assert gs2.graveyard[0]["name"] == "DeadCo"
    assert gs2.schema_version == 13


def test_endgame_tick_runs_clean():
    gs = _gs()
    # should not raise and returns a list
    events = victory.endgame_tick(gs)
    assert isinstance(events, list)
