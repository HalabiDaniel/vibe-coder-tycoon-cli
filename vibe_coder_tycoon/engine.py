import random

from .constants import AI_SUBS, BACKGROUNDS, MONTH_NAMES
from .models import GameState, Founder, Company, Project, Employee
from .persistence import default_settings


def make_new_game(founder: Founder, ai_sub_idx: int) -> GameState:
    bg = BACKGROUNDS[founder.background_idx]
    starting_cash = 5000
    c = Company(
        id=0,
        name=f"{founder.username}'s First Venture",
        legal_style="Solo Hustle",
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
    events_this_month = []

    # Apply company financials
    for c in gs.active_companies():
        c.cash += c.monthly_revenue - c.monthly_expenses
        c.cash = max(0, c.cash)
        c.valuation = c.cash + c.monthly_revenue * 12
        if c.cash == 0:
            events_this_month.append(
                ("💸", f"{c.name} ran out of cash!", "bad",
                 f"{MONTH_NAMES[gs.month-1]} {gs.year}"))

    # Progress in-dev projects
    for p in gs.projects:
        if p.status == "In Dev":
            speed = sub["speed"]
            p.progress = min(100, p.progress + random.randint(8, 12) + speed * 2)
            p.tokens_used += sub["tokens"] * random.randint(100, 300)
            gs.founder.total_tokens_used += sub["tokens"] * random.randint(1, 3)
            if p.progress >= 100:
                p.status = "Launched"
                p.launch_date = f"{MONTH_NAMES[gs.month-1]} {gs.year}"
                events_this_month.append(
                    ("🚀", f"{p.name} launched!", "good",
                     f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
        elif p.status in ("Launched", "Growing"):
            growth = random.randint(2, 8)
            p.revenue = max(0, p.revenue + growth * 10)
            p.users   = max(0, p.users + random.randint(10, 80))
            p.lifetime_revenue += p.revenue
            c = gs.company_by_id(p.company_id)
            if c:
                c.monthly_revenue = sum(proj.revenue for proj in gs.projects
                                        if proj.company_id == c.id)
            if p.revenue > 1000 and p.status == "Launched":
                p.status = "Growing"

    # Founder burnout
    burnout_delta = random.randint(-2, 5) - gs.founder.skill_management // 20
    gs.founder.burnout = max(0, min(100, gs.founder.burnout + burnout_delta))
    if gs.founder.burnout > 80:
        events_this_month.append(
            ("⚠️", "Founder burnout critical! Take a rest.", "bad",
             f"{MONTH_NAMES[gs.month-1]} {gs.year}"))

    # Reputation drift
    gs.founder.reputation = max(0, min(100, gs.founder.reputation + random.randint(-1, 3)))

    # Employee mood drift
    for emp in gs.employees:
        emp.mood = max(0, min(100, emp.mood + random.randint(-4, 4)))
        emp.productivity = max(0, min(100, emp.productivity + random.randint(-3, 3)))

    # Random news event
    random_news = [
        {"icon": "📰", "headline": "AI token costs drop 15% — good time to prototype",
         "category": "Market", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "⚠️",  "headline": "Market sentiment sours on consumer AI tools",
         "category": "Market", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "🔥",  "headline": "IndieScroll trending: solo builders hit 10K MRR",
         "category": "Community", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "💡",  "headline": "New open-source stack released — consider switching",
         "category": "Tools", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
        {"icon": "💸",  "headline": "Angel round closed: $500K into micro-SaaS",
         "category": "Funding", "date": f"{MONTH_NAMES[gs.month-1]} {gs.year}", "effect": None},
    ]
    gs.news_feed.insert(0, random.choice(random_news))
    gs.news_feed = gs.news_feed[:20]

    gs.events = events_this_month + gs.events
    gs.events = gs.events[:20]

    date_str = f"{MONTH_NAMES[gs.month-1]} {gs.year}"
    return f"Month advanced to {date_str}. Cash: ${gs.total_cash():,}  Burnout: {gs.founder.burnout}%"

