import os


# ─────────────────────── CONSTANTS ────────────────────────────

GAME_VERSION = "v0.9.0-alpha"
DEMO_MONTH_LIMIT = 12

SAVE_FILE = os.path.expanduser("~/.vibe_coder_save.json")

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

