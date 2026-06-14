import os
import sys

# Load .env file if present (no-op if python-dotenv not installed or file absent)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─────────────────────── CONSTANTS ────────────────────────────

GAME_VERSION = "v0.9.0-alpha"
DEMO_MONTH_LIMIT = 12

# Legacy save path — only used for one-time migration
SAVE_FILE = os.path.expanduser("~/.vibe_coder_save.json")

# Platform-aware app config directory
def _get_config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "vibe-coder-tycoon")

APP_CONFIG_DIR = _get_config_dir()

# Supabase credentials — set via .env or environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

TABS = [
    "Dashboard", "Founder", "Companies", "Projects",
    "Employees", "Market", "Research", "News", "Settings", "Help"
]

# Parody AI subscription names
AI_SUBS = [
    {"name": "ChatNPC Basic",   "cost": 0,   "speed": 2, "quality": 2, "bug_risk": 4,
     "tokens": 1, "chaos": 3, "desc": "Free tier. Slow, unreliable, chaotic."},
    {"name": "Clodex Lite",     "cost": 10,  "speed": 3, "quality": 4, "bug_risk": 3,
     "tokens": 2, "chaos": 2, "desc": "Budget model. Balanced but limited context."},
    {"name": "Gemino Mini",     "cost": 15,  "speed": 4, "quality": 3, "bug_risk": 3,
     "tokens": 2, "chaos": 2, "desc": "Fast and cheap. Weak at complex logic."},
    {"name": "Llamurai 70B",    "cost": 5,   "speed": 3, "quality": 3, "bug_risk": 3,
     "tokens": 1, "chaos": 1, "desc": "Open-source warrior. Self-hostable. GDPR-safe."},
    {"name": "Clodex Pro",      "cost": 40,  "speed": 4, "quality": 5, "bug_risk": 2,
     "tokens": 4, "chaos": 1, "desc": "Premium reasoning. Low bug risk. Expensive."},
    {"name": "ChatNPC Turbo",   "cost": 30,  "speed": 5, "quality": 4, "bug_risk": 2,
     "tokens": 3, "chaos": 2, "desc": "Fast and capable. Token-hungry."},
    {"name": "Mistralix Large", "cost": 25,  "speed": 4, "quality": 4, "bug_risk": 2,
     "tokens": 3, "chaos": 1, "desc": "EU-based. GDPR-friendly. Solid coder."},
    {"name": "DeepVault Coder", "cost": 20,  "speed": 3, "quality": 5, "bug_risk": 1,
     "tokens": 2, "chaos": 1, "desc": "Specialist coding model. Low chaos, high craft."},
]

BACKGROUNDS = [
    {"name": "Solo Hacker",
     "desc": "You work alone, move fast, and break things. Sometimes on purpose.",
     "bonuses": {"prototyping": +15, "burnout_resist": -5, "sales": 0,  "tech_skill": +10}},
    {"name": "Student Builder",
     "desc": "Broke but resourceful. You have time, no money, and strong opinions.",
     "bonuses": {"prototyping": +10, "burnout_resist": +10, "sales": -5, "tech_skill": +5}},
    {"name": "Agency Freelancer",
     "desc": "You know how to sell, scope, and deliver. Slightly burned out already.",
     "bonuses": {"prototyping": 0,  "burnout_resist": -10, "sales": +20, "tech_skill": 0}},
    {"name": "Corporate Escapee",
     "desc": "You left the salary. Now you hustle. You understand processes and politics.",
     "bonuses": {"prototyping": -5, "burnout_resist": +5,  "sales": +10, "tech_skill": +5}},
    {"name": "Indie Game Dev",
     "desc": "You shipped a game once. It made $47. You will not stop trying.",
     "bonuses": {"prototyping": +10, "burnout_resist": +5, "sales": +5, "tech_skill": +5}},
    {"name": "Open-Source Tinkerer",
     "desc": "You contribute to everything and own nothing. Community loves you.",
     "bonuses": {"prototyping": +5, "burnout_resist": +10, "sales": -10, "tech_skill": +20}},
]

PROJECT_TYPES = [
    "SaaS Web App", "Mobile App", "Browser Extension", "CLI Tool",
    "API / Backend", "AI Wrapper", "Discord Bot", "No-Code Template",
    "Developer Tool", "Content Platform",
]

TECH_STACKS = [
    "Next.js + Vercel", "React Native + Expo", "Python + FastAPI",
    "Node.js + Express", "Svelte + Cloudflare", "Electron Desktop",
    "Bubble.io", "Replit + Nix", "T3 Stack", "Django + Railway",
]

NICHES = [
    "Productivity", "Fintech", "Healthcare", "EdTech", "E-Commerce",
    "Social / Community", "Gaming Tools", "Developer Tools",
    "Content Creation", "B2B Automation",
]

# Phase 4 — Legal structures (GDD-aligned with unlock conditions and effects)
COMPANY_LEGAL_STRUCTURES = [
    {
        "name": "Sole Proprietorship", "short": "Sole Prop",
        "desc": "Just you and a dream. Zero overhead, total control.",
        "unlock_cash": 0, "unlock_research": None,
        "expense_mult": 0.9, "revenue_mult": 1.0,
        "vc_eligible": False, "ipo_eligible": False,
    },
    {
        "name": "LLC", "short": "LLC",
        "desc": "Limited liability. Credible enough for angel investors.",
        "unlock_cash": 2000, "unlock_research": None,
        "expense_mult": 1.0, "revenue_mult": 1.0,
        "vc_eligible": False, "ipo_eligible": False,
    },
    {
        "name": "Partnership", "short": "Partnership",
        "desc": "Co-founder structure. Shared risk, shared glory.",
        "unlock_cash": 1000, "unlock_research": None,
        "expense_mult": 1.0, "revenue_mult": 1.05,
        "vc_eligible": False, "ipo_eligible": False,
    },
    {
        "name": "C-Corporation", "short": "C-Corp",
        "desc": "Investment-grade. Can take VC money and issue shares.",
        "unlock_cash": 15000, "unlock_research": "Cap Table Basics",
        "expense_mult": 1.15, "revenue_mult": 1.1,
        "vc_eligible": True, "ipo_eligible": True,
    },
    {
        "name": "Public Company", "short": "Public",
        "desc": "Listed on the exchange. Shareholders, earnings calls, chaos.",
        "unlock_cash": 100000, "unlock_research": "Cap Table Basics",
        "expense_mult": 1.3, "revenue_mult": 1.25,
        "vc_eligible": True, "ipo_eligible": True,
    },
]

# Derived list for backward-compat wizard display
COMPANY_LEGAL_STYLES = [s["name"] for s in COMPANY_LEGAL_STRUCTURES]

# Phase 4 — Company focuses (GDD-aligned with can-build sets and bonuses)
COMPANY_FOCUSES = [
    {
        "name": "AI Tools",
        "desc": "AI-powered products. Token cost bonus, faster iteration.",
        "can_build": ["AI Wrapper", "SaaS Web App", "Developer Tool", "API / Backend", "Browser Extension"],
        "dev_speed_mult": 1.1, "token_cost_mult": 0.85,
        "revenue_mult": 1.0, "hype_mult": 1.0,
        "synergy_with": "Infrastructure",
    },
    {
        "name": "SaaS",
        "desc": "Subscription software. Recurring revenue focus.",
        "can_build": ["SaaS Web App", "API / Backend", "Developer Tool", "Browser Extension", "Discord Bot"],
        "dev_speed_mult": 1.0, "token_cost_mult": 1.0,
        "revenue_mult": 1.1, "hype_mult": 1.0,
        "synergy_with": None,
    },
    {
        "name": "Games",
        "desc": "Ship games. High hype potential, volatile revenue.",
        "can_build": ["Mobile App", "Browser Extension", "Discord Bot", "No-Code Template"],
        "dev_speed_mult": 0.9, "token_cost_mult": 1.0,
        "revenue_mult": 0.95, "hype_mult": 1.25,
        "synergy_with": None,
    },
    {
        "name": "Agency",
        "desc": "Client work and templates. Steady cash, less glory.",
        "can_build": ["No-Code Template", "SaaS Web App", "Mobile App", "Browser Extension", "Content Platform"],
        "dev_speed_mult": 1.05, "token_cost_mult": 1.0,
        "revenue_mult": 1.05, "hype_mult": 0.85,
        "synergy_with": None,
    },
    {
        "name": "Enterprise",
        "desc": "B2B software. Long sales cycles, large contracts.",
        "can_build": ["SaaS Web App", "API / Backend", "Developer Tool", "CLI Tool"],
        "dev_speed_mult": 0.85, "token_cost_mult": 1.1,
        "revenue_mult": 1.2, "hype_mult": 0.8,
        "synergy_with": None,
    },
    {
        "name": "Infrastructure",
        "desc": "DevTools, APIs, and platform services. Unglamorous but profitable.",
        "can_build": ["CLI Tool", "API / Backend", "Developer Tool", "SaaS Web App"],
        "dev_speed_mult": 1.0, "token_cost_mult": 0.9,
        "revenue_mult": 1.0, "hype_mult": 0.8,
        "synergy_with": "AI Tools",
    },
    {
        "name": "Holding Company",
        "desc": "Owns other companies. No products — pure control and synergies.",
        "can_build": [],
        "dev_speed_mult": 1.0, "token_cost_mult": 1.0,
        "revenue_mult": 1.0, "hype_mult": 1.0,
        "synergy_with": None,
    },
    {
        "name": "Content Tools",
        "desc": "Creator economy. High hype, ad-based revenue.",
        "can_build": ["Content Platform", "Mobile App", "Browser Extension", "Discord Bot", "No-Code Template"],
        "dev_speed_mult": 1.0, "token_cost_mult": 1.0,
        "revenue_mult": 1.0, "hype_mult": 1.15,
        "synergy_with": None,
    },
]

# Derived list for backward-compat wizard display
COMPANY_FOCUS_AREAS = [f["name"] for f in COMPANY_FOCUSES]

# Phase 4 — Office levels with employee caps and role unlocks
OFFICE_LEVELS = [
    {
        "level": 1, "name": "Home Office",
        "max_employees": 2,
        "upgrade_cost": 3000,
        "unlocked_roles": ["Vibe Coder", "Prompt Engineer"],
    },
    {
        "level": 2, "name": "Shared Desk",
        "max_employees": 4,
        "upgrade_cost": 8000,
        "unlocked_roles": ["Frontend Dev", "Backend Dev"],
    },
    {
        "level": 3, "name": "Small Office",
        "max_employees": 6,
        "upgrade_cost": 20000,
        "unlocked_roles": ["Bug Hunter", "Growth Goblin"],
    },
    {
        "level": 4, "name": "Real Office",
        "max_employees": 10,
        "upgrade_cost": 50000,
        "unlocked_roles": ["Pixel Artist", "Community Wizard"],
    },
    {
        "level": 5, "name": "Open-Plan HQ",
        "max_employees": 15,
        "upgrade_cost": 120000,
        "unlocked_roles": ["Finance Gremlin"],
    },
    {
        "level": 6, "name": "Mid-Size HQ",
        "max_employees": 20,
        "upgrade_cost": 300000,
        "unlocked_roles": ["Operations Goblin", "AI Researcher", "Model Trainer"],
    },
    {
        "level": 7, "name": "Campus",
        "max_employees": 40,
        "upgrade_cost": 800000,
        "unlocked_roles": [],
    },
    {
        "level": 8, "name": "Mega HQ",
        "max_employees": 100,
        "upgrade_cost": 0,
        "unlocked_roles": [],
    },
]

FUNDING_STYLES = [
    "Bootstrapped", "Friends & Family", "Angel Round",
    "Seed Round", "Revenue-Based", "VC-Backed",
]

RISK_APPETITES = ["Cautious", "Balanced", "Aggressive", "Reckless"]

EMPLOYEE_ROLES = [
    "Vibe Coder", "Prompt Engineer", "Frontend Dev", "Backend Dev",
    "Pixel Artist", "Growth Goblin", "Bug Hunter", "Community Wizard",
    "Finance Gremlin", "Operations Goblin", "AI Researcher", "Model Trainer",
]

EMPLOYEE_TRAITS = [
    "Night Owl", "Burnout Resistant", "Token Efficient", "Bug Magnet",
    "Viral Touch", "Revenue Focused", "Community Legend", "Deep Focus",
    "Chaos Agent", "Silent Genius",
]

RESEARCH_CATEGORIES = [
    ("Infrastructure",  ["Faster Deployment", "Auto-Scaling", "CDN Mastery", "Zero-Downtime Deploys"]),
    ("AI / Prompting",  ["Better System Prompts", "Token Compression", "Multi-Agent Chains", "Fine-Tuning Basics"]),
    ("Marketing",       ["Viral Launch Tactics", "SEO Foundations", "Cold Email Engine", "Community Flywheel"]),
    ("Hiring",          ["Better Job Posts", "Culture Fit Screening", "Async Team Setup", "Contractor Network"]),
    ("Automation",      ["Auto Customer Support", "Revenue Reconciliation", "CI/CD Pipeline", "A/B Testing Rig"]),
    ("Funding",         ["Pitch Deck Template", "Angel Network Access", "Revenue Forecasting", "Cap Table Basics"]),
    ("Management",      ["Async Stand-Ups", "OKR Framework", "1-on-1 Cadence", "Team Rituals"]),
    ("Founder Health",  ["Burnout Shield", "Deep Work Blocks", "Boundary Setting", "Sleep Optimization"]),
]

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Phase 1 — token milestone table (thresholds in same units as total_tokens_used)
TOKEN_MILESTONES = [
    (10,            "Prompt Apprentice"),
    (100,           "Token Hustler"),
    (1_000,         "Context Warrior"),
    (10_000,        "Inference Engine"),
    (100_000,       "Token God"),
    (1_000_000_000, "Token Singularity"),
]

# Phase 1 — lender table
LENDERS = [
    {
        "name": "VibeBank",
        "desc": "No collateral required. Just vibes and a dream.",
        "rate": 0.08,
        "term_months": 12,
        "max_amount": 10_000,
        "min_reputation": 15,
    },
    {
        "name": "StartupVault",
        "desc": "Seed-stage friendly. High rate but closes in 48h.",
        "rate": 0.15,
        "term_months": 24,
        "max_amount": 50_000,
        "min_reputation": 30,
    },
    {
        "name": "CryptoCapital",
        "desc": "Volatile terms. Accepts meme-backed collateral. DYOR.",
        "rate": 0.20,
        "term_months": 6,
        "max_amount": 25_000,
        "min_reputation": 10,
    },
    {
        "name": "FriendFund",
        "desc": "Your friend Kyle. Low rate, awkward holiday dinners.",
        "rate": 0.05,
        "term_months": 6,
        "max_amount": 5_000,
        "min_reputation": 0,
    },
]

# Cycling auto-deposit percentages (used by toggle in Companies tab)
AUTO_DEPOSIT_CYCLE = [0, 10, 25, 50]

# ─────────────────────── PHASE 2 DATA ─────────────────────────

FEATURE_SCOPES = {
    "Lean MVP":       {"features": 3,  "base_days": 30,  "token_mult": 0.5},
    "Standard":       {"features": 6,  "base_days": 60,  "token_mult": 1.0},
    "Feature-Rich":   {"features": 10, "base_days": 90,  "token_mult": 1.8},
    "Overengineered": {"features": 15, "base_days": 150, "token_mult": 3.0},
}

QA_OPTIONS = [
    {"name": "Skip QA",  "cost": 0,   "days": 0, "bug_mult": 1.0, "critical_risk": 0.0,
     "desc": "Ship it and pray."},
    {"name": "Light QA", "cost": 200, "days": 3, "bug_mult": 0.6, "critical_risk": 0.05,
     "desc": "Quick smoke test. Cuts bugs by 40%."},
    {"name": "Full QA",  "cost": 800, "days": 7, "bug_mult": 0.2, "critical_risk": 0.15,
     "desc": "Deep coverage. Risk of surfacing a critical flaw."},
]

DEV_INTERRUPTION_EVENTS = [
    {
        "id": "hallucination",
        "title": "AI Hallucination",
        "body": "Your AI confidently wrote an entire auth system using an API that doesn't exist.",
        "prob": 0.12,
        "choices": [
            {"label": "Rewrite manually",    "effects": {"tech_score": 8,  "dev_day": -5, "vibe": -5}},
            {"label": "Ship it anyway",      "effects": {"bug_count": 3,   "hype": 5,     "sanity": -5}},
        ],
    },
    {
        "id": "api_outage",
        "title": "API Outage",
        "body": "Your AI provider is down. Status page says 'investigating.' It's been 4 hours.",
        "prob": 0.08,
        "choices": [
            {"label": "Switch to backup model", "effects": {"tokens_used": 100, "dev_day": -2}},
            {"label": "Take a forced break",    "effects": {"sanity": 10,       "vibe": 5}},
        ],
    },
    {
        "id": "context_window",
        "title": "Context Window Exceeded",
        "body": "Your codebase is too large for the AI to comprehend. It keeps forgetting things.",
        "prob": 0.10,
        "choices": [
            {"label": "Refactor into modules", "effects": {"tech_score": 10, "dev_day": -7}},
            {"label": "Summarize and continue","effects": {"tech_score": -5, "bug_count": 2}},
        ],
    },
    {
        "id": "vibe_overflow",
        "title": "Vibe Overflow",
        "body": "16 hours deep. The code looks great. Is it great? Impossible to say.",
        "prob": 0.15,
        "choices": [
            {"label": "Push through (CHAOS MODE)", "effects": {"design_score": 10, "bug_count": 4, "sanity": -10}},
            {"label": "Sleep on it",               "effects": {"sanity": 15, "vibe": -10, "dev_day": -2}},
        ],
    },
]

DEV_ACTIONS = [
    {
        "key": "1", "name": "Honest Devlog",
        "desc": "Write an honest update. Builds rep and modest hype.",
        "cost": 0,
        "effects": {"reputation": 2, "hype": 5, "sanity": 2},
    },
    {
        "key": "2", "name": "Vibe-Coding Thread",
        "desc": "Post your build journey. Big hype boost but burns vibe.",
        "cost": 0,
        "effects": {"hype": 15, "vibe": -10, "reputation": 1},
    },
    {
        "key": "3", "name": "Fake a Feature",
        "desc": "Announce a feature that barely works. Big hype, reputation risk at launch.",
        "cost": 0,
        "effects": {"hype": 20, "reputation": -3, "faked": True},
    },
    {
        "key": "4", "name": "Buy Ads",
        "desc": "Spend $200 on targeted ads. Solid hype boost.",
        "cost": 200,
        "effects": {"hype": 12, "reputation": 1},
    },
    {
        "key": "5", "name": "Bribe Influencer",
        "desc": "Pay $500 to an influencer. Massive hype but sketchy reputation.",
        "cost": 500,
        "effects": {"hype": 30, "reputation": -5},
    },
]

TERMINAL_LOG_LINES = [
    "Compiling components... done.",
    "npm warn deprecated package@1.0.0",
    "AI generated 400 lines of suspiciously clean code.",
    "Bug detected in auth module. Again.",
    "Token usage: nominal.",
    "Design system: 70% complete.",
    "Running tests... 3 passing, 12 failing.",
    "Pushed to main. CI is green.",
    "Context window: 87% full.",
    "Hallucination detected in route handler.",
    "Successfully refactored for the third time today.",
    "Tech debt increasing.",
    "Hype building from community post...",
    "Feature complete: user dashboard.",
    "Deploying to staging...",
    "Memory leak identified and patched.",
    "Rate limited by AI provider. Throttling.",
    "Code review: 'looks good to me'",
    "Merge conflict resolved (sort of).",
    "AI suggests renaming everything. Again.",
    "Build time: 4m 23s. Too long.",
    "Wrote tests. AI wrote the tests. AI passed the tests.",
    "Dependency audit: 3 critical vulnerabilities.",
    "Refactoring hour three. Still no progress.",
    "The AI is writing poetry in the comments.",
    "Shipped a fix. Introduced two new bugs.",
    "Type errors: 47. Ship it anyway.",
    "User story complete: undefined requirements met.",
]

# ─────────────────────── PHASE 3 DATA ─────────────────────────

# Revenue model behaviors — revenue_per_user is base $ per active user per month
REVENUE_MODELS = {
    "Subscription": {
        "desc": "Monthly recurring revenue. Grows with users, decays with churn.",
        "revenue_per_user": 8.0,
    },
    "One-Time": {
        "desc": "Pay-once purchase. Big launch spike, residual new buyers over time.",
        "revenue_per_user": 1.5,
    },
    "Ads": {
        "desc": "Ad-supported. Revenue scales with daily active user count.",
        "revenue_per_user": 0.6,
    },
    "Commission": {
        "desc": "Usage/commission-based. Revenue scales with transaction volume.",
        "revenue_per_user": 3.5,
    },
}

# Default revenue model per project type
PRODUCT_REVENUE_MODELS = {
    "SaaS Web App":       "Subscription",
    "Mobile App":         "Ads",
    "Browser Extension":  "One-Time",
    "CLI Tool":           "One-Time",
    "API / Backend":      "Commission",
    "AI Wrapper":         "Subscription",
    "Discord Bot":        "Subscription",
    "No-Code Template":   "One-Time",
    "Developer Tool":     "Subscription",
    "Content Platform":   "Ads",
}

# Obsolescence windows (min, max months) per product type — silent revenue decay
OBSOLESCENCE_WINDOWS = {
    "SaaS Web App":       (18, 36),
    "Mobile App":         (12, 24),
    "Browser Extension":  (24, 48),
    "CLI Tool":           (36, 60),
    "API / Backend":      (24, 48),
    "AI Wrapper":         (6,  18),
    "Discord Bot":        (12, 24),
    "No-Code Template":   (12, 30),
    "Developer Tool":     (24, 48),
    "Content Platform":   (12, 24),
}

# Auto-update interval options (months; 0 = disabled)
AUTO_UPDATE_CYCLES = [0, 1, 2, 3, 6]


# ─────────────────────── PHASE 5 — EMPLOYEES ──────────────────
#
# Five-stat model: coding, prompting, research, marketing, sanity (0–100).
# Each role has a stat profile (which stats are emphasised), a salary range,
# the office level at which it unlocks, and a reputation gate (top talent
# refuses to work for low-reputation founders).

ROLE_CATALOG = {
    "Vibe Coder": {
        "primary": ["coding", "prompting"],
        "salary": (1500, 2800),
        "office_level": 1,
        "min_reputation": 0,
        "blurb": "Ships features at 2am fuelled by energy drinks and vibes.",
    },
    "Prompt Engineer": {
        "primary": ["prompting", "research"],
        "salary": (1800, 3200),
        "office_level": 1,
        "min_reputation": 0,
        "blurb": "Whisperer of language models. Knows the magic words.",
    },
    "Frontend Dev": {
        "primary": ["coding", "marketing"],
        "salary": (2000, 3500),
        "office_level": 2,
        "min_reputation": 10,
        "blurb": "Pixel-perfect UIs and a suspicious love of CSS.",
    },
    "Backend Dev": {
        "primary": ["coding", "research"],
        "salary": (2200, 3800),
        "office_level": 2,
        "min_reputation": 10,
        "blurb": "Keeps the servers warm and the migrations terrifying.",
    },
    "Bug Hunter": {
        "primary": ["research", "coding"],
        "salary": (2000, 3500),
        "office_level": 3,
        "min_reputation": 20,
        "blurb": "Finds the bug you swore wasn't there. QA wizardry.",
    },
    "Growth Goblin": {
        "primary": ["marketing", "prompting"],
        "salary": (1800, 3200),
        "office_level": 3,
        "min_reputation": 20,
        "blurb": "Turns launches viral. Possibly unhinged. Definitely effective.",
    },
    "Pixel Artist": {
        "primary": ["marketing", "coding"],
        "salary": (1800, 3000),
        "office_level": 4,
        "min_reputation": 35,
        "blurb": "Makes things beautiful. Refuses to use Comic Sans.",
    },
    "Community Wizard": {
        "primary": ["marketing", "sanity"],
        "salary": (1600, 2800),
        "office_level": 4,
        "min_reputation": 35,
        "blurb": "Keeps users happy and churn low. Discord moderator energy.",
    },
    "Finance Gremlin": {
        "primary": ["research", "marketing"],
        "salary": (2500, 4500),
        "office_level": 5,
        "min_reputation": 50,
        "blurb": "Hoards spreadsheets. Knows where every token went.",
    },
    "Operations Goblin": {
        "primary": ["research", "sanity"],
        "salary": (2500, 4500),
        "office_level": 6,
        "min_reputation": 60,
        "blurb": "Makes the chaos run on time. The glue of the company.",
    },
    "AI Researcher": {
        "primary": ["research", "prompting"],
        "salary": (3500, 6000),
        "office_level": 6,
        "min_reputation": 60,
        "blurb": "Trains models and runs experiments nobody else understands.",
    },
    "Model Trainer": {
        "primary": ["coding", "research"],
        "salary": (4000, 7000),
        "office_level": 6,
        "min_reputation": 60,
        "blurb": "Wrangles datasets and GPU clusters. Knows what OOM means.",
    },
}

# Candidate name banks (procedural generation)
CANDIDATE_FIRST_NAMES = [
    "Ama", "Taro", "Zara", "Ivan", "Lena", "Rafi", "Suki", "Omar", "Nina",
    "Kojo", "Mei", "Diego", "Priya", "Yuki", "Sam", "Aria", "Bilal", "Noa",
    "Kai", "Esme", "Tariq", "Vera", "Liam", "Sana", "Oleg", "Fatima",
]
CANDIDATE_LAST_NAMES = [
    "Kwei", "Naka", "Malik", "Petrov", "Chen", "Hassan", "Park", "Ali",
    "Okafor", "Sato", "Rossi", "Nguyen", "Cohen", "Santos", "Ahmed", "Singh",
    "Volkov", "Haddad", "Murphy", "Bauer", "Costa", "Reyes",
]
CANDIDATE_BACKSTORIES = [
    "Ex-FAANG, quit to 'find meaning'. Found mostly bugs.",
    "Self-taught from YouTube at 2x speed. Surprisingly competent.",
    "Built 14 side projects, shipped 1. That one went viral.",
    "Recovering crypto founder. Talks about 'product-market fit' a lot.",
    "Bootcamp grad with terrifying levels of energy.",
    "Former game modder. Optimises everything obsessively.",
    "Open-source maintainer with 9,000 GitHub stars and no sleep.",
    "Career-switcher from accounting. Reads docs for fun.",
    "Hackathon legend. Allergic to meetings.",
    "Indie hacker who 'just wants a stable paycheck for once'.",
]

# Training actions — applied to one employee, paid from their company's cash
TRAINING_ACTIONS = [
    {
        "name": "Pair Prompting",
        "cost": 150,
        "effects": {"prompting": 6, "coding": 2, "sanity": -2},
        "desc": "A focused pairing session. Cheap, reliable prompting boost.",
    },
    {
        "name": "Skill Workshop",
        "cost": 300,
        "effects": {"coding": 5, "research": 3, "sanity": -3},
        "desc": "Hands-on workshop. Solid engineering gains, mildly draining.",
    },
    {
        "name": "Conference Ticket",
        "cost": 600,
        "effects": {"research": 8, "marketing": 4, "sanity": 6},
        "desc": "Send them to a conference. Pricey, but inspiring and restful.",
    },
]

# XP required to advance from level L to L+1
def xp_threshold(level: int) -> int:
    return 100 * max(1, level)


# ─────────────────────── PHASE 6 — MENTAL HEALTH ──────────────
#
# Named conditions applied when sanity / vibe thresholds are crossed. Each has a
# stat multiplier applied to the employee's development contribution, plus a
# human-readable resolution hint surfaced in the UI. "Touch Grass" is handled
# specially (the employee leaves for ~1 month then auto-returns).

CONDITIONS = {
    "Burnout": {
        "trigger": "Sanity under 20%",
        "effect": "-50% to all work output",
        "resolution": "Rest day or Team Recharge",
        "stat_mult": 0.5,
        "resolve_action": "rest",
    },
    "Existential Crisis": {
        "trigger": "Sanity under 10%",
        "effect": "Questions whether vibe coding is real coding. -70% output",
        "resolution": "Inspirational Talk (costs founder Vibe)",
        "stat_mult": 0.3,
        "resolve_action": "inspire",
    },
    "Framework Fatigue": {
        "trigger": "Company pivoted focus recently",
        "effect": "-30% output, grumbles about the new stack",
        "resolution": "Give it time (fades on its own)",
        "stat_mult": 0.7,
        "resolve_action": "wait",
    },
    "Startup Mania": {
        "trigger": "Founder Vibe over 90",
        "effect": "+40% speed but Sanity drains fast",
        "resolution": "Fades after the current project ships",
        "stat_mult": 1.4,
        "resolve_action": "wait",
    },
    "AI Doom Spiral": {
        "trigger": "Read too many AI-doom forum threads",
        "effect": "-80% output for a while",
        "resolution": "Distraction action",
        "stat_mult": 0.2,
        "resolve_action": "distract",
    },
}

# Founder-only conditions (mirror the employee model at the player level)
FOUNDER_CONDITIONS = {
    "Founder Burnout": {
        "trigger": "Sanity under 25%",
        "effect": "Global negative-event chance rises",
        "resolution": "Take a Break (Founder action)",
    },
    "Doom Scrolling": {
        "trigger": "Sanity under 15%",
        "effect": "Productivity and judgement suffer",
        "resolution": "Take a Break (Founder action)",
    },
}

# Mental-health action costs/effects
TEAM_RECHARGE_COST = 1000      # per company, restores team sanity
INSPIRE_VIBE_COST = 15.0       # founder vibe spent on an Inspirational Talk
DISTRACTION_COST = 250         # cash cost of a Distraction action


# ─────────────────────── PHASE 7 — TECH TIMELINE ──────────────
#
# Eras gate the "feel" of the run and unlock new content over time (GDD §20).
# Each entry is (start_year, name, blurb). The current era is the last whose
# start_year <= current in-game year.

ERAS = [
    (2022, "The Discovery Era",
     "The world just realised AI can write code. Everyone is shocked. Tools are limited."),
    (2024, "The Builder Era",
     "AI coding assistants go mainstream. Everyone is shipping SaaS. Quality starts to matter."),
    (2027, "The Agent Era",
     "Autonomous agents handle real workloads. Teams shrink. Infra costs explode."),
    (2031, "The Automation Era",
     "AI companies dominate. Foundation models are the new platform. Build or depend."),
    (2036, "The God Complex Era",
     "AGI-class products become thinkable. Your net worth nears the trillionaire line."),
]

# IDE catalog (parody names, release year, development bonuses). dev_speed_mult
# scales Design/Tech gain; bug_mult < 1.0 reduces bugs; token_mult < 1.0 saves
# tokens. CodeBox is the free neutral baseline (always available).
IDE_CATALOG = [
    {"name": "CodeBox", "company": "Open Source", "year": 2022,
     "desc": "The free, neutral baseline editor. Reliable, unremarkable.",
     "dev_speed_mult": 1.0, "bug_mult": 1.0, "token_mult": 1.0},
    {"name": "Replicity AI", "company": "Replicity AI", "year": 2022,
     "desc": "Browser IDE where beginners accidentally ship a SaaS.",
     "dev_speed_mult": 1.05, "bug_mult": 1.05, "token_mult": 1.0},
    {"name": "GitHub CoPilotter", "company": "Macrosoft", "year": 2022,
     "desc": "Finishes your function, then asks you to check the imports.",
     "dev_speed_mult": 1.1, "bug_mult": 1.0, "token_mult": 1.0},
    {"name": "MousePointer", "company": "MousePointer AI", "year": 2023,
     "desc": "Makes you feel like a CEO until it rewrites the auth system.",
     "dev_speed_mult": 1.15, "bug_mult": 1.0, "token_mult": 1.0},
    {"name": "Windserve", "company": "Incognito AI", "year": 2023,
     "desc": "Rides the vibe-coding wave so hard it's basically a surfboard.",
     "dev_speed_mult": 1.1, "bug_mult": 0.95, "token_mult": 1.0},
    {"name": "FastBrainsy AI", "company": "FastBrainsy AI", "year": 2024,
     "desc": "Powerful once you find it behind 47 enterprise menus.",
     "dev_speed_mult": 1.12, "bug_mult": 0.92, "token_mult": 0.95},
    {"name": "Clod Code", "company": "Anthrowpick", "year": 2025,
     "desc": "Polite terminal wizard. Writes a 19-step plan to rename a variable.",
     "dev_speed_mult": 1.18, "bug_mult": 0.85, "token_mult": 0.9},
    {"name": "Codecks", "company": "OpenAy", "year": 2025,
     "desc": "Opens six branches, fixes one bug, leaves a mysterious helper file.",
     "dev_speed_mult": 1.2, "bug_mult": 0.9, "token_mult": 0.95},
    {"name": "Keero", "company": "Rainforest", "year": 2025,
     "desc": "Turns 'make me an app' into specs, diagrams, tasks, and a meeting.",
     "dev_speed_mult": 1.2, "bug_mult": 0.8, "token_mult": 1.0},
    {"name": "Tray AI", "company": "Byron ByteDance", "year": 2025,
     "desc": "Promises 10x productivity, 3x confusion, one dramatic sidebar.",
     "dev_speed_mult": 1.15, "bug_mult": 0.95, "token_mult": 0.95},
    {"name": "Googol AntiGravity", "company": "Googol DeepMine", "year": 2025,
     "desc": "Agents float around your project while Google adds a dashboard.",
     "dev_speed_mult": 1.22, "bug_mult": 0.85, "token_mult": 0.9},
]

# Subscription tiers (GDD §15). monthly is a flat founder-level cost; the API
# tier instead bills per token consumed during development. speed_mult nudges
# development; open_only restricts to open-weight models (self-hosting).
SUBSCRIPTION_TIERS = [
    {"name": "Free", "monthly": 0, "per_token": 0.0, "speed_mult": 0.85,
     "open_only": False, "desc": "Basic access. Slow, rate-limited, humbling."},
    {"name": "Pro", "monthly": 20, "per_token": 0.0, "speed_mult": 1.0,
     "open_only": False, "desc": "Better models, fewer limits. The default."},
    {"name": "Pro+", "monthly": 200, "per_token": 0.0, "speed_mult": 1.1,
     "open_only": False, "desc": "Top current models, priority speed."},
    {"name": "API Usage", "monthly": 0, "per_token": 0.03, "speed_mult": 1.15,
     "open_only": False, "desc": "Uncapped speed. You pay per token you burn."},
    {"name": "Self-Hosted", "monthly": 60, "per_token": 0.0, "speed_mult": 0.95,
     "open_only": True, "desc": "Run open-weight models on your own hardware."},
]


# ─────────────────────── PHASE 8 — TEMPLATES ──────────────────
#
# Templates are company-scoped internal assets built through the development
# phase (a Lean-MVP-style build with no market launch). Their bonuses are
# derived from the Design/Tech scores achieved during the build, so a template
# built later with better models/IDEs/teams comes out stronger (versioning).
# `base_days` is the build length; `build_cost` is the up-front cash to start.

TEMPLATE_TYPES = [
    {"name": "SaaS Boilerplate", "base_days": 20, "build_cost": 400,
     "desc": "Auth, billing, and dashboard scaffold. Jump-starts SaaS builds."},
    {"name": "Mobile Starter", "base_days": 18, "build_cost": 350,
     "desc": "Cross-platform shell with navigation and state baked in."},
    {"name": "Auth Framework", "base_days": 15, "build_cost": 300,
     "desc": "Battle-tested login, sessions, and permissions."},
    {"name": "AI Agent Scaffold", "base_days": 26, "build_cost": 650,
     "desc": "Prompt routing, tool calls, and memory plumbing."},
    {"name": "API Gateway Kit", "base_days": 20, "build_cost": 450,
     "desc": "Rate limiting, keys, and usage metering out of the box."},
    {"name": "Payments Module", "base_days": 16, "build_cost": 400,
     "desc": "Checkout, subscriptions, and webhooks pre-wired."},
]


# ─────────────────────── PHASE 9 — INFRASTRUCTURE ─────────────
#
# Hosting scales cost with a company's live user base and caps capacity (over
# it, outages strike). GPUs and datacenters reduce per-token dev cost; a
# datacenter also unlocks selling excess compute for passive revenue.

HOSTING_PROVIDERS = [
    {"name": "Free Tier", "base_cost": 0, "cost_per_user": 0.0, "capacity": 200,
     "desc": "Generous until it isn't. Falls over under real load."},
    {"name": "Hobby Cloud", "base_cost": 50, "cost_per_user": 0.05, "capacity": 2_000,
     "desc": "Cheap and cheerful. Fine for early traction."},
    {"name": "Pro Cloud", "base_cost": 300, "cost_per_user": 0.03, "capacity": 25_000,
     "desc": "Autoscaling, real SLAs, real invoices."},
    {"name": "Enterprise Cloud", "base_cost": 1_500, "cost_per_user": 0.02, "capacity": 250_000,
     "desc": "Multi-region, six-figure logos, near-infinite scale."},
    {"name": "Self-Hosted Rack", "base_cost": 800, "cost_per_user": 0.01, "capacity": 1_000_000,
     "desc": "Your hardware, your rules, your pager at 3am."},
]

# GPU generations — each owned GPU reduces dev token cost. `token_reduction` is
# the per-unit reduction when new; benefit decays as the card ages past 4 years.
GPU_GENERATIONS = [
    {"name": "Vivid V100", "year": 2022, "cost": 8_000, "token_reduction": 0.04,
     "desc": "Workhorse of the early boom. Slow by today's standards."},
    {"name": "Ampere A100", "year": 2023, "cost": 15_000, "token_reduction": 0.06,
     "desc": "The datacenter standard. Still pricey on the resale market."},
    {"name": "Hopper H100", "year": 2024, "cost": 30_000, "token_reduction": 0.09,
     "desc": "The one everyone fought over. Liquid-cooled bragging rights."},
    {"name": "Blackwell B200", "year": 2025, "cost": 45_000, "token_reduction": 0.12,
     "desc": "Frontier-class. Melts power budgets and competitors."},
    {"name": "Rubin R300", "year": 2027, "cost": 70_000, "token_reduction": 0.16,
     "desc": "Next-gen accelerator. If you can get an allocation."},
]

# Datacenter tiers — large capital unlock. Tier 0 = none. Higher tiers cut
# per-token cost further and add `compute_capacity` units that can be sold.
DATACENTER_TIERS = [
    {"tier": 0, "name": "No Datacenter", "cost": 0, "per_token_reduction": 0.0,
     "compute_capacity": 0, "desc": "Renting compute like everyone else."},
    {"tier": 1, "name": "Server Closet", "cost": 50_000, "per_token_reduction": 0.08,
     "compute_capacity": 100, "desc": "A rack and a prayer. Trims token costs a bit."},
    {"tier": 2, "name": "Colo Cage", "cost": 200_000, "per_token_reduction": 0.16,
     "compute_capacity": 500, "desc": "Leased cage in a real facility."},
    {"tier": 3, "name": "Regional DC", "cost": 1_000_000, "per_token_reduction": 0.24,
     "compute_capacity": 2_500, "desc": "Your own building. Can host player models."},
    {"tier": 4, "name": "Hyperscale DC", "cost": 5_000_000, "per_token_reduction": 0.32,
     "compute_capacity": 12_000, "desc": "Foundation-model grade. Sell the excess."},
]

# Passive revenue per sold compute unit per month (before demand/quality mods).
COMPUTE_UNIT_PRICE = 9.0


# ─────────────────────── PHASE 10 — PLAYER AI MODELS ──────────

AI_MODEL_AXES = [
    {"name": "Coding",      "weight": 0.30, "desc": "Code generation quality"},
    {"name": "Reasoning",   "weight": 0.25, "desc": "Multi-step problem solving"},
    {"name": "Creativity",  "weight": 0.15, "desc": "Novel solution generation"},
    {"name": "Speed",       "weight": 0.15, "desc": "Response latency"},
    {"name": "Context",     "weight": 0.10, "desc": "Long-context handling"},
    {"name": "Multimodal",  "weight": 0.05, "desc": "Image/document processing"},
]
AXIS_POINT_BUDGET = 30   # total slider points to distribute across axes

PLAYER_MODEL_UNLOCK = {
    "min_office_level": 6,
    "min_year": 2028,
    "min_datacenter_tier": 2,
    "min_researchers": 2,
    "min_trainers": 1,
    "min_cash": 50_000,
}

AI_MODEL_TRAINING_COST_PER_POINT = 5_000   # $ per axis point
AI_MODEL_TRAINING_DAYS_PER_POINT = 6       # training days per axis point
AI_MODEL_TOKEN_COST_PER_POINT    = 8_000   # tokens consumed per axis point

AI_MODEL_LICENSE_BASE_REVENUE = 500   # $ per capability point per month


# ─────────────────────── PHASE 11 — FUNDING ROUNDS ────────────

FUNDING_ROUNDS = [
    {
        "name": "Friends & Family",
        "min_year": 2025,
        "amount_range": (5_000, 25_000),
        "equity_range": (0.02, 0.08),
        "req_months": 6,
        "req_metric": "mrr",
        "req_multiplier": 0.5,
        "min_reputation": 0,
        "min_mrr": 0,
        "desc": "Your network. Low bar, high awkwardness at family dinner.",
    },
    {
        "name": "Angel Round",
        "min_year": 2025,
        "amount_range": (25_000, 150_000),
        "equity_range": (0.05, 0.15),
        "req_months": 9,
        "req_metric": "mrr",
        "req_multiplier": 0.3,
        "min_reputation": 30,
        "min_mrr": 500,
        "desc": "Individual investor. Writes a check, gives advice you didn't ask for.",
    },
    {
        "name": "Seed Round",
        "min_year": 2026,
        "amount_range": (200_000, 1_000_000),
        "equity_range": (0.10, 0.20),
        "req_months": 12,
        "req_metric": "mrr",
        "req_multiplier": 0.25,
        "min_reputation": 50,
        "min_mrr": 5_000,
        "desc": "Early-stage VC. Needs a compelling growth story.",
    },
    {
        "name": "Series A",
        "min_year": 2027,
        "amount_range": (2_000_000, 10_000_000),
        "equity_range": (0.15, 0.25),
        "req_months": 18,
        "req_metric": "revenue",
        "req_multiplier": 0.20,
        "min_reputation": 65,
        "min_mrr": 50_000,
        "desc": "Growth-stage. Requires serious metrics and a credible team.",
    },
]

INVESTOR_NAMES = [
    "Beacon Ventures", "YCombinator Parody", "VibeFund Capital",
    "Andreessen Morality", "Sequoia Clone", "Tiger Global Lite",
    "SoftBank of Vibes", "a16crypto", "Founders Fund Parody",
    "Accel Parody", "Benchmark Clone", "Index Ventures Parody",
]


# ─────────────────────── PHASE 12 — STOCK MARKET / IPO ────────
#
# Parody public companies that trade on the in-game exchange. The player can
# NOT buy these — they exist as market context / flavour and to anchor a parody
# index. Each carries a ticker, a base share price, and a volatility factor that
# scales its daily random walk.

PARODY_PUBLIC_COMPANIES = [
    {"name": "OpenAy",         "ticker": "OPAY", "base_price": 312.0, "volatility": 0.045,
     "founder": "Sam Altmannish", "drift": 0.010},
    {"name": "Anthrowpick",    "ticker": "ANPK", "base_price": 188.0, "volatility": 0.035,
     "founder": "Dario Amodai", "drift": 0.009},
    {"name": "Googol DeepMine","ticker": "GDM",  "base_price": 174.0, "volatility": 0.028,
     "founder": "Demis Hasabits", "drift": 0.006},
    {"name": "Mehta",          "ticker": "MEH",  "base_price": 506.0, "volatility": 0.030,
     "founder": "Mark Zuckerbyte", "drift": 0.005},
    {"name": "Macrosoft",      "ticker": "MCSF", "base_price": 421.0, "volatility": 0.022,
     "founder": "Bill Gaits", "drift": 0.004},
    {"name": "DeepPeek",       "ticker": "DPK",  "base_price": 92.0,  "volatility": 0.075,
     "founder": "Liang WenPing", "drift": 0.014},
    {"name": "yAI",            "ticker": "YAI",  "base_price": 64.0,  "volatility": 0.090,
     "founder": "Elong Mask", "drift": 0.012},
    {"name": "Aliblabla Cloud","ticker": "ALBC", "base_price": 118.0, "volatility": 0.033,
     "founder": "Wang Serverman", "drift": 0.005},
]

# IPO pipeline tuning
IPO_MIN_POSITIVE_MRR_MONTHS = 12      # consecutive months of positive MRR required
IPO_BANK_COST_PCT          = 0.04     # investment bank fee, % of company valuation
IPO_BANK_COST_MIN          = 25_000   # floor on the bank fee
IPO_PUBLIC_FLOAT_PCT       = 0.20     # fraction of shares sold to the public at IPO
IPO_DUE_DILIGENCE_CHANCE   = 0.45     # chance the due-diligence event surfaces an issue

# Net-worth / victory
TRILLIONAIRE_THRESHOLD = 1_000_000_000_000


# ─────────────────────── PHASE 13 — EVENTS / RIVALS ──────────
#
# Weighted random-event catalog (GDD §21). Each event has a category that
# affects how Vibe / founder-sanity / reputation modulate its likelihood:
#   positive  — good fortune; suppressed when Vibe runs hot / sanity is low
#   negative  — setbacks; amplified by hot Vibe and low founder sanity
#   meme       — internet chaos; mildly amplified by hot Vibe
#   founder    — personal / wellbeing beats; gated on founder sanity
#
# "kind" is either "instant" (effects applied immediately) or "choice" (a card
# is pushed to gs.pending_event_cards and the player picks an option). Effects
# are a flat dict resolved by events.apply_effects:
#   personal_cash, company_cash, reputation, vibe, sanity, tokens, hype
#
# Optional gates: min_year, requires ∈
#   {"has_company","has_product","has_employees","is_public"}.
# "cooldown" is the minimum months before the same event may fire again.

EVENT_BASE_MONTHLY_CHANCE = 0.45      # baseline chance an event fires in a month
EVENT_GLOBAL_COOLDOWN     = 1         # min months between any two fired events

EVENT_CATALOG = [
    # ── POSITIVE ──────────────────────────────────────────────
    {
        "id": "hn_front_page", "category": "positive", "icon": "🚀", "weight": 10,
        "kind": "instant", "cooldown": 4, "requires": "has_product",
        "headline": "Your launch hit the front page of Hacker Mews!",
        "effects": {"hype": 25, "reputation": 4, "vibe": 8},
    },
    {
        "id": "angel_cold_email", "category": "positive", "icon": "💌", "weight": 7,
        "kind": "choice", "cooldown": 8, "requires": "has_company",
        "headline": "A friendly angel slid into your DMs.",
        "body": ("An angel investor loved your vibe and offers a small no-strings "
                 "grant — or a coffee chat that could build a longer relationship."),
        "choices": [
            {"label": "Take the $8,000 grant", "effects": {"personal_cash": 8000},
             "result": "Grant wired to your personal account. Easy money."},
            {"label": "Build the relationship (+rep, +vibe)",
             "effects": {"reputation": 6, "vibe": 10},
             "result": "You skip the cash but earn a reputation boost and good vibes."},
        ],
    },
    {
        "id": "open_source_love", "category": "positive", "icon": "⭐", "weight": 8,
        "kind": "instant", "cooldown": 6,
        "headline": "An open-source side project of yours is trending on GitHive.",
        "effects": {"reputation": 3, "vibe": 6},
    },
    {
        "id": "token_credits", "category": "positive", "icon": "🎟️", "weight": 6,
        "kind": "instant", "cooldown": 6, "requires": "has_company",
        "headline": "Your AI provider comped you free token credits.",
        "effects": {"company_cash": 1500, "vibe": 4},
    },

    # ── NEGATIVE ──────────────────────────────────────────────
    {
        "id": "data_breach", "category": "negative", "icon": "🔓", "weight": 9,
        "kind": "choice", "cooldown": 10, "requires": "has_product",
        "headline": "Security researcher reports a leak in your product.",
        "body": ("A whitehat found exposed user data. You can pay for a proper "
                 "remediation, or quietly patch it and hope nobody notices."),
        "choices": [
            {"label": "Pay for full remediation (-$4,000, +rep)",
             "effects": {"company_cash": -4000, "reputation": 2},
             "result": "Transparent fix. Users respect the honesty."},
            {"label": "Quietly patch it (gamble)",
             "effects": {"reputation": -8, "vibe": -6},
             "result": "It leaked anyway. The internet is not pleased."},
        ],
    },
    {
        "id": "api_price_hike", "category": "negative", "icon": "💸", "weight": 8,
        "kind": "instant", "cooldown": 8, "requires": "has_company",
        "headline": "Your model provider jacked up API prices overnight.",
        "effects": {"company_cash": -2000, "sanity": -4},
    },
    {
        "id": "framework_deprecation", "category": "negative", "icon": "⚠️", "weight": 7,
        "kind": "instant", "cooldown": 8,
        "headline": "A framework you depend on was deprecated. Migration looms.",
        "effects": {"sanity": -6, "vibe": -5},
    },
    {
        "id": "viral_outage", "category": "negative", "icon": "🔥", "weight": 6,
        "kind": "instant", "cooldown": 10, "requires": "has_product",
        "headline": "Your app went down during peak traffic. Screenshots everywhere.",
        "effects": {"reputation": -5, "hype": -15, "sanity": -5},
    },

    # ── MEME ──────────────────────────────────────────────────
    {
        "id": "vibe_coding_thread", "category": "meme", "icon": "🧵", "weight": 8,
        "kind": "instant", "cooldown": 5,
        "headline": "Your 'I vibe-coded a unicorn in a weekend' thread went viral.",
        "effects": {"reputation": 2, "vibe": 12, "hype": 10},
    },
    {
        "id": "ai_doom_discourse", "category": "meme", "icon": "🤖", "weight": 6,
        "kind": "instant", "cooldown": 6,
        "headline": "AI doom discourse is melting timelines again.",
        "effects": {"vibe": -4, "sanity": -3},
    },
    {
        "id": "founder_meme_account", "category": "meme", "icon": "😹", "weight": 5,
        "kind": "choice", "cooldown": 9,
        "headline": "A meme account is dunking on a screenshot of your code.",
        "body": ("Your spaghetti code is the main character today. Lean into the "
                 "joke, or log off and touch grass?"),
        "choices": [
            {"label": "Lean in, post the cursed code yourself",
             "effects": {"reputation": -2, "vibe": 9, "hype": 8},
             "result": "Self-aware shitposting wins the day. Vibes immaculate."},
            {"label": "Log off and recover",
             "effects": {"sanity": 8, "vibe": -2},
             "result": "You close the laptop. Sanity restored."},
        ],
    },

    # ── FOUNDER ───────────────────────────────────────────────
    {
        "id": "burnout_warning", "category": "founder", "icon": "🪫", "weight": 8,
        "kind": "choice", "cooldown": 6,
        "headline": "You haven't slept properly in weeks.",
        "body": ("The grind is catching up. Take a real break to recover, or push "
                 "through on caffeine and spite."),
        "choices": [
            {"label": "Take a proper break (+sanity, -vibe)",
             "effects": {"sanity": 15, "vibe": -6},
             "result": "You rest. Your brain thanks you."},
            {"label": "Push through (gamble)",
             "effects": {"sanity": -10, "vibe": 6},
             "result": "You ship more, but you're running on fumes."},
        ],
    },
    {
        "id": "inspiration_strike", "category": "founder", "icon": "💡", "weight": 7,
        "kind": "instant", "cooldown": 5,
        "headline": "A shower thought just unlocked your next big idea.",
        "effects": {"vibe": 10, "sanity": 4},
    },
    {
        "id": "impostor_syndrome", "category": "founder", "icon": "🌀", "weight": 6,
        "kind": "instant", "cooldown": 6,
        "headline": "Impostor syndrome is hitting hard today.",
        "effects": {"sanity": -7, "vibe": -3},
    },
    {
        "id": "mentor_call", "category": "founder", "icon": "🧙", "weight": 5,
        "kind": "instant", "cooldown": 8,
        "headline": "An old mentor checked in and gave you perspective.",
        "effects": {"sanity": 8, "reputation": 1},
    },
]

# Background rival system (GDD §22). Rivals operate in the player's verticals and
# create market saturation that gently suppresses sales — no micro-management.
RIVAL_NAME_PREFIXES = [
    "Hyper", "Quantum", "Neural", "Vibe", "Turbo", "Synth", "Prompt", "Apex",
    "Nova", "Pixel", "Cloud", "Forge", "Stack", "Loop", "Flux",
]
RIVAL_NAME_SUFFIXES = [
    "Labs", "AI", "Soft", "Works", "Systems", "Dynamics", "Forge", "Stack",
    "ly", "io", "HQ", "Collective", "Studio",
]
RIVAL_TAGLINES = [
    "the future of building", "AI-native everything", "shipping at the speed of thought",
    "your unfair advantage", "code that codes itself", "the last tool you'll ever need",
]

# How strongly cumulative rival presence in a vertical suppresses player sales.
RIVAL_SATURATION_FLOOR = 0.45         # sales never drop below 45% from rivals alone
RIVAL_MAX_ACTIVE       = 6            # cap on simultaneous background rivals
