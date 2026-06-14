"""
Phase 13 — Procedural content string banks.

Plain string tables consumed by `engine/systems/content.py` combinators. Kept as
data (no logic) so flavor can be tuned without touching engine code. The content
engine seeds these with the run RNG so output is deterministic under a fixed seed.
"""

# ─────────────────────── COMPANY NAMES ────────────────────────

COMPANY_ADJECTIVES = [
    "Hyper", "Quantum", "Neural", "Vibe", "Turbo", "Synth", "Prompt", "Apex",
    "Nova", "Pixel", "Hyperscale", "Lambda", "Recursive", "Async", "Sentient",
]
COMPANY_NOUNS = [
    "Labs", "Works", "Systems", "Dynamics", "Forge", "Stack", "Loop", "Flux",
    "Mind", "Engine", "Grid", "Pulse", "Logic", "Core", "Foundry",
]
COMPANY_SUFFIXES = ["", "", "", " AI", " io", " HQ", " Inc", " Co"]


# ─────────────────────── PRODUCT NAMES ────────────────────────

# Vertical → flavored stem words. Falls back to PRODUCT_GENERIC.
PRODUCT_STEMS = {
    "SaaS Web App":      ["Dash", "Flow", "Hub", "Desk", "Suite", "Sync"],
    "Mobile App":        ["Tap", "Snap", "Pocket", "Go", "Buddy", "Mate"],
    "Browser Extension": ["Clip", "Tab", "Block", "Peek", "Lens"],
    "CLI Tool":          ["dash", "ctl", "kit", "run", "forge"],
    "API / Backend":     ["API", "Gate", "Bridge", "Relay", "Mesh"],
    "AI Wrapper":        ["GPT", "Mind", "Brain", "Oracle", "Muse"],
    "Discord Bot":       ["Bot", "Helper", "Mod", "Buddy", "Pal"],
    "No-Code Template":  ["Builder", "Blocks", "Canvas", "Studio", "Kit"],
    "Developer Tool":    ["Forge", "Lint", "Trace", "Debug", "Deploy"],
    "Content Platform":  ["Feed", "Scroll", "Post", "Stream", "Page"],
}
PRODUCT_GENERIC = ["Box", "Hub", "Flow", "Kit", "Lab", "Pro", "Cloud"]
PRODUCT_PREFIXES = ["", "", "Get", "Use", "Try", "My", "Open", "Smart", "Auto"]


# ─────────────────────── REVIEWS ──────────────────────────────

REVIEW_POSITIVE = [
    "Absolutely shipped. {product} replaced three tools for me.",
    "Can't believe {product} was built by a tiny team. Flawless.",
    "{product} just works. Rare these days. ⭐⭐⭐⭐⭐",
    "Switched our whole stack to {product}. No regrets.",
    "The vibes on {product} are immaculate. Daily driver now.",
]
REVIEW_MIXED = [
    "{product} is promising but the onboarding needs love.",
    "Solid idea, rough edges. {product} will get there.",
    "{product} works most of the time. Occasional jank.",
    "Decent. {product} is a 7/10 — fix the bugs and it's a 9.",
]
REVIEW_NEGATIVE = [
    "{product} crashed twice during my demo. Yikes.",
    "Felt over-hyped. {product} didn't live up to the launch thread.",
    "Uninstalled {product}. Too many bugs. ⭐⭐",
    "{product} is clearly vibe-coded and it shows.",
    "Refund please. {product} ate my data.",
]


# ─────────────────────── NEWS HEADLINES ───────────────────────

NEWS_TEMPLATES = [
    "{company} raises ${amount}M to {tagline}.",
    "{company} launches {product} — early users impressed.",
    "Analysts say {company} could redefine {niche}.",
    "{company} hits {users}K users on {product}.",
    "Drama: {company} accused of vibe-coding its entire stack.",
    "{company} open-sources {product}; devs rejoice.",
    "Token prices dip — good month to prototype, say builders.",
    "IndieScroll trend: solo founders out-shipping big labs again.",
]
NEWS_TAGLINES = [
    "reinvent developer tooling", "build AI-native software", "ship faster than ever",
    "automate the boring parts", "make coding feel like magic", "eat the SaaS world",
]
NEWS_CATEGORIES = ["Market", "Tools", "Community", "Drama", "Funding", "Research"]


# ─────────────────────── EMPLOYEE NAMES ───────────────────────

EMPLOYEE_FIRST_NAMES = [
    "Ada", "Linus", "Grace", "Dennis", "Margaret", "Alan", "Hedy", "Ken",
    "Radia", "Guido", "Bjarne", "Anita", "Tim", "Barbara", "Yann", "Fei",
    "Omar", "Priya", "Mateo", "Lena", "Kofi", "Sora", "Diego", "Nadia",
]
EMPLOYEE_LAST_NAMES = [
    "Nakamura", "Okonkwo", "Petrov", "Silva", "Kim", "Haddad", "Larsson",
    "Mbeki", "Costa", "Rahman", "Novak", "Tanaka", "Reyes", "Singh",
    "Abara", "Volkov", "Diallo", "Castro", "Yusuf", "Lindqvist",
]


# ─────────────────────── TERMINAL LOG LINES ───────────────────

TERMINAL_LINES = [
    "$ git commit -m 'it works on my machine'",
    "Compiling... 4 warnings, 0 errors (we don't talk about warnings)",
    "Refactoring spaghetti into slightly tidier spaghetti...",
    "$ npm install (downloading the entire internet)",
    "AI: 'I've also taken the liberty of rewriting your auth.'",
    "Resolving merge conflict in vibes.config.js...",
    "TODO: remove this before launch (added 3 versions ago)",
    "$ deploy --yolo --pray",
    "Tests passing! (the one test we wrote)",
    "AI suggested 200 lines. You accepted all of them. Bold.",
]
