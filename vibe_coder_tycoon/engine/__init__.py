"""
Engine package — public API: make_new_game, advance_month, dispatch.

Import paths that existed before (from .engine import ...) still work because
this package's __init__.py re-exports the same names.
"""

import random

from ..constants import AI_SUBS, BACKGROUNDS, MONTH_NAMES
from ..models import GameState, Founder, Company, Project, Employee
from ..persistence import default_settings
from .actions import dispatch, ActionResult  # noqa: F401 — re-exported
from .systems import finance        # registers finance actions as a side-effect
from .systems import development    # registers dev actions as a side-effect
from .systems import products       # registers product actions as a side-effect
from .systems import companies      # registers company/office actions as a side-effect
from .systems import employees       # registers employee actions as a side-effect


def make_new_game(founder: Founder, ai_sub_idx: int) -> GameState:
    starting_cash = 5000
    c = Company(
        id=0,
        name=f"{founder.username}'s First Venture",
        legal_style="Sole Proprietorship",
        focus_area="AI Tools",
        funding_style="Bootstrapped",
        risk_appetite="Balanced",
        cash=starting_cash,
        monthly_revenue=0,
        monthly_expenses=200,
        debt=0,
        reputation=20,
        valuation=starting_cash,
        office_level=1,
        mood=80,
        founded_month=1,
        founded_year=2025,
        loans=[],
    )
    gs = GameState(
        founder=founder,
        year=2025,
        month=1,
        months_elapsed=0,
        active_ai_sub_idx=ai_sub_idx,
        companies=[c],
        projects=[],
        employees=[],
        news_feed=make_initial_news(),
        events=[("🚀", f"Welcome, {founder.username}! Your journey begins.", "good", "Jan 2025")],
        research_progress={},
        settings=default_settings(),
    )
    return gs


def make_initial_news():
    return [
        {"icon": "📡", "headline": "AI funding hits record high — $40B deployed in Q4 2024",
         "category": "Market", "date": "Jan 2025", "effect": None},
        {"icon": "🔥", "headline": "ChatNPC announces major pricing restructure — check your subs",
         "category": "Tools", "date": "Jan 2025", "effect": None},
        {"icon": "📣", "headline": "IndieScroll trending: solo devs shipping faster than ever",
         "category": "Community", "date": "Jan 2025", "effect": None},
        {"icon": "⚠️",  "headline": "SnapStack suffers 6-hour outage — Vercel alternatives spike",
         "category": "Drama", "date": "Jan 2025", "effect": None},
        {"icon": "💡", "headline": "New open-source LLM from DeepVault matches frontier quality",
         "category": "Research", "date": "Dec 2024", "effect": None},
    ]


def advance_month(gs: GameState) -> str:
    gs.month += 1
    if gs.month > 12:
        gs.month = 1
        gs.year += 1
    gs.months_elapsed += 1

    sub = AI_SUBS[gs.active_ai_sub_idx]
    date_str = f"{MONTH_NAMES[gs.month - 1]} {gs.year}"
    events_this_month = []

    # Finance settlement (Phase 1): replaces the old inline cash loop
    finance_events = finance.monthly_settlement(gs)
    events_this_month.extend(finance_events)

    # Progress in-dev projects via development system; tick launched products
    for p in gs.projects:
        if p.status == "In Dev":
            dev_events = development.tick_dev_project(gs, p)
            events_this_month.extend(dev_events)
        elif p.status in ("Launched", "Growing"):
            prod_events = products.monthly_product_tick(gs, p, date_str)
            events_this_month.extend(prod_events)

    # Founder burnout
    burnout_delta = random.randint(-2, 5) - gs.founder.skill_management // 20
    gs.founder.burnout = max(0, min(100, gs.founder.burnout + burnout_delta))
    if gs.founder.burnout > 80:
        events_this_month.append(
            ("⚠️", "Founder burnout critical! Take a rest.", "bad", date_str)
        )

    # Reputation drift
    finance.adjust_reputation(gs, random.randint(-1, 3))

    # Employee mood drift
    for emp in gs.employees:
        emp.mood = max(0, min(100, emp.mood + random.randint(-4, 4)))
        emp.productivity = max(0, min(100, emp.productivity + random.randint(-3, 3)))

    # Random news
    random_news = [
        {"icon": "📰", "headline": "AI token costs drop 15% — good time to prototype",
         "category": "Market", "date": date_str, "effect": None},
        {"icon": "⚠️",  "headline": "Market sentiment sours on consumer AI tools",
         "category": "Market", "date": date_str, "effect": None},
        {"icon": "🔥",  "headline": "IndieScroll trending: solo builders hit 10K MRR",
         "category": "Community", "date": date_str, "effect": None},
        {"icon": "💡",  "headline": "New open-source stack released — consider switching",
         "category": "Tools", "date": date_str, "effect": None},
        {"icon": "💸",  "headline": "Angel round closed: $500K into micro-SaaS",
         "category": "Funding", "date": date_str, "effect": None},
    ]
    gs.news_feed.insert(0, random.choice(random_news))
    gs.news_feed = gs.news_feed[:20]

    gs.events = events_this_month + gs.events
    gs.events = gs.events[:20]

    return (
        f"Month advanced to {date_str}. "
        f"Personal: ${gs.founder.personal_cash:,.0f}  "
        f"Tokens: {gs.founder.total_tokens_used:,}K  "
        f"Vibe: {gs.founder.vibe:.0f}"
    )
