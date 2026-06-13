from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────── DATA MODELS ──────────────────────────

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
    hype: int = 50
    tech_debt: int = 0
    launch_date: str = ""
    lifetime_revenue: int = 0

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
    schema_version: int = 1

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

