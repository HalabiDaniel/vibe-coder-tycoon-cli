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

COMPANY_LEGAL_STYLES = [
    "Solo Hustle", "Tiny Studio", "Indie Lab",
    "Garage Startup", "Growth Startup", "Holding Company", "Mega Corp",
]

COMPANY_FOCUS_AREAS = [
    "AI Tools", "SaaS", "Mobile Apps", "Games", "Developer Tools",
    "Automation", "Education", "Content Tools", "Weird Internet Products",
]

FUNDING_STYLES = [
    "Bootstrapped", "Friends & Family", "Angel Round",
    "Seed Round", "Revenue-Based", "VC-Backed",
]

RISK_APPETITES = ["Cautious", "Balanced", "Aggressive", "Reckless"]

EMPLOYEE_ROLES = [
    "Vibe Coder", "Prompt Engineer", "Frontend Dev", "Backend Dev",
    "Pixel Artist", "Growth Goblin", "Bug Hunter", "Community Wizard",
    "Finance Gremlin", "Operations Goblin",
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

