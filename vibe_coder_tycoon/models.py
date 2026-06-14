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
class Template:
    """Phase 8 — a company-scoped internal asset that boosts future builds."""
    name: str
    template_type: str
    version: int
    company_id: int
    design_bonus: float = 0.0      # starting Design score granted to a project
    tech_bonus: float = 0.0        # starting Tech score granted to a project
    time_reduction: float = 0.0    # 0–0.3 fraction off dev_total_days
    bug_reduction: float = 0.0     # 0–0.5 fraction off bug generation
    built_year: int = 2025


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
    # Phase 8 — templates
    template_id: int = -1           # index into gs.templates, -1 = none used
    is_template: bool = False       # True while this project is a template build
    template_type: str = ""         # which TEMPLATE_TYPES entry (when is_template)


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
    # Phase 5 — five-stat model, XP, assignment, state
    coding: int = 50
    prompting: int = 50
    research: int = 50
    marketing: int = 50
    sanity: int = 80
    xp: int = 0
    assigned_project_id: int = -1   # index into gs.projects, -1 = unassigned
    state: str = "active"           # "active" | "touch_grass"
    state_until: int = 0            # months_elapsed when they return to active
    backstory: str = ""
    # Phase 6 — mental health
    condition: str = ""             # active named condition, "" if none
    condition_until: int = 0        # months_elapsed when a timed condition clears


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
    # Phase 4
    parent_company_id: int = -1
    history: list = field(default_factory=list)
    # Phase 9 — infrastructure & compute
    hosting_provider: str = "Free Tier"
    gpu_inventory: list = field(default_factory=list)   # [{"name", "year_bought"}]
    datacenter_tier: int = 0
    compute_capacity: int = 0       # mirrors datacenter tier capacity
    compute_for_sale: bool = False


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
    # Phase 6 — mental health
    conditions: list = field(default_factory=list)


@dataclass
class AIModel:
    name: str
    axes: dict                   # {"Coding": 8, "Reasoning": 5, ...}
    version: int
    company_id: int
    capability_rating: float     # weighted sum of axes / 10.0 (0–10 scale)
    model_id: int                # unique int, assigned at creation
    licensed: bool = False
    training_status: str = "ready"       # "training" | "ready"
    training_days_remaining: int = 0
    trained_year: int = 2025


@dataclass
class FundingDeal:
    deal_id: int
    round_type: str           # e.g. "Angel Round"
    amount: int
    equity_pct: float         # fraction 0–1 (e.g. 0.10 = 10%)
    requirement_desc: str     # human readable
    requirement_metric: str   # "mrr" | "users" | "revenue"
    requirement_target: int   # numeric target to hit
    deadline_month: int       # gs.months_elapsed value at deadline
    company_id: int
    investor_name: str
    status: str = "active"    # "active" | "met" | "failed"
    month_accepted: int = 0


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
    schema_version: int = 10
    # Phase 8 — templates (company-scoped internal assets)
    templates: list = field(default_factory=list)
    # Phase 7 — tech timeline / tools
    current_era: str = "The Discovery Era"
    subscription_tier: str = "Pro"
    active_ide: str = "CodeBox"
    active_model: str = ""          # selected default AI model (parody name)
    tokens_this_month: int = 0      # token consumption since last settlement
    # Phase 10 — player-built AI models
    player_models: list = field(default_factory=list)   # list of AIModel
    _next_model_id: int = 0
    # Phase 11 — loans, investors, funding
    funding_deals: list = field(default_factory=list)     # list of FundingDeal
    pending_offers: list = field(default_factory=list)    # list of dicts (not yet accepted)
    loan_default_count: int = 0

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
