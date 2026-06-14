"""
Phase 13 — Procedural content engine.

Templated string combinators backed by the banks in `data/strings.py`. Every
generator accepts an optional `rng` (a `random.Random`); when omitted it falls
back to the module-level `random`. Passing a seeded RNG makes output fully
deterministic, which the Phase 13 tests rely on.

These helpers produce unique-feeling company names, product names, reviews,
news headlines, employee names, and terminal-log lines without any live LLM
calls (GDD §27).
"""

import random as _random

from ...data import strings as S


def _rng(rng):
    return rng if rng is not None else _random


# ─────────────────────── NAMES ────────────────────────────────


def gen_company_name(rng=None) -> str:
    r = _rng(rng)
    adj = r.choice(S.COMPANY_ADJECTIVES)
    noun = r.choice(S.COMPANY_NOUNS)
    suffix = r.choice(S.COMPANY_SUFFIXES)
    return f"{adj}{noun}{suffix}"


def gen_product_name(vertical: str = "", rng=None) -> str:
    r = _rng(rng)
    stems = S.PRODUCT_STEMS.get(vertical, S.PRODUCT_GENERIC)
    prefix = r.choice(S.PRODUCT_PREFIXES)
    stem = r.choice(stems)
    tail = r.choice(["", "", "ly", "ify", "AI", "HQ"])
    name = f"{prefix}{stem}{tail}".strip()
    return name[0].upper() + name[1:] if name else stem


def gen_employee_name(rng=None) -> str:
    r = _rng(rng)
    return f"{r.choice(S.EMPLOYEE_FIRST_NAMES)} {r.choice(S.EMPLOYEE_LAST_NAMES)}"


# ─────────────────────── REVIEWS ──────────────────────────────


def gen_review(quality: int, product: str = "this product", rng=None) -> str:
    """Pick a review tone weighted by a 0–100 quality score."""
    r = _rng(rng)
    if quality >= 70:
        bank = S.REVIEW_POSITIVE
    elif quality >= 40:
        bank = S.REVIEW_MIXED
    else:
        bank = S.REVIEW_NEGATIVE
    return r.choice(bank).format(product=product)


# ─────────────────────── NEWS ─────────────────────────────────


def gen_news_item(rng=None) -> dict:
    """A procedural news-feed entry: {icon, headline, category, date, effect}."""
    r = _rng(rng)
    template = r.choice(S.NEWS_TEMPLATES)
    headline = template.format(
        company=gen_company_name(r),
        product=gen_product_name(r.choice(list(S.PRODUCT_STEMS.keys())), r),
        amount=r.choice([2, 5, 8, 12, 20, 40, 100]),
        tagline=r.choice(S.NEWS_TAGLINES),
        niche=r.choice(["fintech", "devtools", "edtech", "gaming", "B2B SaaS"]),
        users=r.choice([5, 10, 25, 50, 120]),
    )
    icon = r.choice(["📰", "📡", "💸", "🔥", "💡", "📣", "⚠️"])
    return {
        "icon": icon,
        "headline": headline,
        "category": r.choice(S.NEWS_CATEGORIES),
        "date": "",
        "effect": None,
    }


# ─────────────────────── TERMINAL ─────────────────────────────


def gen_terminal_line(rng=None) -> str:
    return _rng(rng).choice(S.TERMINAL_LINES)
