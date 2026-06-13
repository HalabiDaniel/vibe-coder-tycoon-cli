from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────── DATA MODELS ──────────────────────────

@dataclass
class DevSession:
    """Transient state for an active development run on a Project."""
    terminal_log: list = field(default_factory=list)       # last 20 log lines
    pending_interruption: dict = field(default_factory=dict)  # {} if none active
    interruption_choice_idx: int = 0
    action_result: str = ""     # feedback from last dev action


@dataclass
class Loan:
    lender: str
    principal: int
    balance: int
    rate: float       # annual interest rate (e.g. 0.08 = 8%)
    term_months: int
    company_id: int
    monthly_payment: int


@dataclass
class Project:
    name: str
    ptype: str
    model: str
    stack: str
    niche: str
    company_id: int
    status: str
    progress: int
    revenue: int
    users: int
    morale: int
    tokens_used: int
    bug_count: int = 0
    hype: int = 30
    tech_debt: int = 0
    launch_date: str = ""
    lifetime_revenue: int = 0
    # Phase 2 — active development fields
    design_score: float = 0.0
    tech_score: float = 0.0
    quality_score: int = 0
    qa_level: str = "Skip QA"
    scope: str = "Standard"
    budget: int = 500
    dev_weeks: int = 4
    dev_day: int = 0
    dev_total_days: int = 60
    faked_features: list = field(default_factory=list)
    paused_dev: bool = False
    dev_session: Optional[DevSession] = None
    # Phase 3 — product lifecycle fields
    revenue_model: str = ""
    obsolescence_months: int = 0
    age_months: int = 0
    active_users: int = 0
    churn_rate: float = 0.05
    version: int = 1
    parent_product_id: int = -1
    auto_update_interval: int = 0
    auto_update_countdown: int = 0
    discontinued: bool = False
    revenue_history: list = field(default_factory=list)


@dataclass
class Employee:
    name: str
    role: str
    level: int
    salary: int
    mood: int
    skill: int
    hired_year: int
    company_id: int
    trait: str = ""
    loyalty: int = 75
    productivity: int = 75


@dataclass
class Company:
    id: int
    name: str
    legal_style: str
    focus_area: str
    funding_style: str
    risk_appetite: str
    cash: int
    monthly_revenue: int
    monthly_expenses: int
    debt: int
    reputation: int
    valuation: int
    office_level: int
    mood: int
    founded_month: int
    founded_year: int
    active: bool = True
    loans: list = field(default_factory=list)
    # Phase 1
    auto_deposit_pct: int = 0
    cover_from_personal: bool = False
    months_negative: int = 0


@dataclass
class Founder:
    username: str
    background_idx: int
    reputation: int
    burnout: int
    skill_prototyping: int
    skill_sales: int
    skill_tech: int
    skill_management: int
    total_tokens_used: int
    achievements: list = field(default_factory=list)
    career_history: list = field(default_factory=list)
    unlocked_research: list = field(default_factory=list)
    # Phase 1
    personal_cash: float = 1000.0
    vibe: float = 50.0
    sanity: int = 100


@dataclass
class GameState:
    founder: Optional[Founder]
    year: int
    month: int
    months_elapsed: int
    active_ai_sub_idx: int
    companies: list
    projects: list
    employees: list
    news_feed: list
    events: list
    research_progress: dict
    settings: dict
    demo_ended: bool = False
    schema_version: int = 4

    def total_cash(self):
        return sum(c.cash for c in self.companies if c.active)

    def active_companies(self):
        return [c for c in self.companies if c.active]

    def company_by_id(self, cid):
        for c in self.companies:
            if c.id == cid:
                return c
        return None

    def projects_for_company(self, cid):
        return [p for p in self.projects if p.company_id == cid]

    def employees_for_company(self, cid):
        return [e for e in self.employees if e.company_id == cid]
