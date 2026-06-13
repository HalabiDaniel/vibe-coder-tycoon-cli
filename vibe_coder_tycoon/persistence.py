import json
import os
import hashlib
from typing import Optional

from .constants import SAVE_FILE, MONTH_NAMES
from .models import GameState, Founder, Company, Project, Employee


# ─────────────────────── SAVE / LOAD ──────────────────────────

ACCOUNTS_FILE = os.path.expanduser("~/.vibe_coder_accounts.json")

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_accounts(accounts):
    try:
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)
    except Exception:
        pass

def accounts_sign_in(username_or_email, password):
    accounts = load_accounts()
    ph = hash_password(password)
    for uname, data in accounts.items():
        if (uname == username_or_email or data.get("email") == username_or_email):
            if data.get("password_hash") == ph:
                return uname, data
    return None, None

def accounts_create(username, email, password):
    accounts = load_accounts()
    if username in accounts:
        return False, "Username already exists."
    for data in accounts.values():
        if data.get("email") == email:
            return False, "Email already registered."
    accounts[username] = {
        "email": email,
        "password_hash": hash_password(password),
        "last_played": f"{MONTH_NAMES[0]} 2025",
        "founder_status": "Rookie Founder",
    }
    save_accounts(accounts)
    return True, "Account created."

def save_game(gs: GameState, username: str):
    try:
        data = {
            "username": username,
            "year": gs.year,
            "month": gs.month,
            "months_elapsed": gs.months_elapsed,
            "active_ai_sub_idx": gs.active_ai_sub_idx,
            "founder": gs.founder.__dict__ if gs.founder else None,
            "companies": [c.__dict__ for c in gs.companies],
            "projects": [p.__dict__ for p in gs.projects],
            "employees": [e.__dict__ for e in gs.employees],
            "news_feed": gs.news_feed,
            "events": gs.events,
            "research_progress": gs.research_progress,
            "settings": gs.settings,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_game(username: str) -> Optional[GameState]:
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
        if data.get("username") != username:
            return None
        fd = data.get("founder")
        founder = Founder(**fd) if fd else None
        companies = [Company(**c) for c in data.get("companies", [])]
        projects  = [Project(**p) for p in data.get("projects", [])]
        employees = [Employee(**e) for e in data.get("employees", [])]
        return GameState(
            founder=founder,
            year=data["year"],
            month=data["month"],
            months_elapsed=data.get("months_elapsed", 0),
            active_ai_sub_idx=data.get("active_ai_sub_idx", 0),
            companies=companies,
            projects=projects,
            employees=employees,
            news_feed=data.get("news_feed", []),
            events=data.get("events", []),
            research_progress=data.get("research_progress", {}),
            settings=data.get("settings", default_settings()),
        )
    except Exception:
        return None

def default_settings():
    return {
        "theme": "Dark Terminal",
        "reduced_animations": False,
        "high_contrast": False,
        "ticker_speed": "normal",
        "audio": "off",
    }

