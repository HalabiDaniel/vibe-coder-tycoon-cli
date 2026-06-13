import json
import os
import hashlib
from typing import Optional

from .constants import SAVE_FILE, MONTH_NAMES, APP_CONFIG_DIR
from .models import GameState, Founder, Company, Project, Employee, Loan


# ─────────────────────── CONFIG DIR ───────────────────────────

def get_config_dir() -> str:
    path = APP_CONFIG_DIR
    os.makedirs(os.path.join(path, "local_saves"), exist_ok=True)
    return path

def get_local_save_path(username: str) -> str:
    return os.path.join(get_config_dir(), "local_saves", f"{username}.json")

def _sync_queue_path() -> str:
    return os.path.join(get_config_dir(), "sync_queue.json")


# ─────────────────────── CHECKSUM ─────────────────────────────

def compute_checksum(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


# ─────────────────────── SYNC QUEUE ───────────────────────────

def get_sync_queue() -> list:
    path = _sync_queue_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []

def save_sync_queue(queue: list):
    try:
        with open(_sync_queue_path(), "w") as f:
            json.dump(queue, f, indent=2)
    except Exception:
        pass

def add_to_sync_queue(username: str, save_data: dict):
    queue = get_sync_queue()
    # Replace any existing entry for this username
    queue = [e for e in queue if e.get("username") != username]
    queue.append({"username": username, "save_data": save_data})
    save_sync_queue(queue)

def flush_sync_queue(cloud_service, user_id: str):
    """Try to upload any queued saves. Removes entries that succeed."""
    queue = get_sync_queue()
    if not queue:
        return
    remaining = []
    for entry in queue:
        save_data = entry.get("save_data", {})
        checksum = compute_checksum(save_data)
        result, err = cloud_service.upload_save(
            user_id, "autosave", save_data, checksum
        )
        if err:
            remaining.append(entry)
    save_sync_queue(remaining)


# ─────────────────────── SAVE / LOAD ──────────────────────────

def _gs_to_dict(gs: GameState, username: str) -> dict:
    def _company_dict(c: Company) -> dict:
        d = {k: v for k, v in c.__dict__.items() if k != "loans"}
        loans_out = []
        for loan in c.loans:
            loans_out.append(loan.__dict__ if isinstance(loan, Loan) else loan)
        d["loans"] = loans_out
        return d

    return {
        "schema_version": gs.schema_version,
        "username": username,
        "year": gs.year,
        "month": gs.month,
        "months_elapsed": gs.months_elapsed,
        "active_ai_sub_idx": gs.active_ai_sub_idx,
        "founder": gs.founder.__dict__ if gs.founder else None,
        "companies": [_company_dict(c) for c in gs.companies],
        "projects": [p.__dict__ for p in gs.projects],
        "employees": [e.__dict__ for e in gs.employees],
        "news_feed": gs.news_feed,
        "events": gs.events,
        "research_progress": gs.research_progress,
        "settings": gs.settings,
    }

def save_game(gs: GameState, username: str) -> dict:
    """Save to local file and return the save_data dict (for cloud upload)."""
    data = _gs_to_dict(gs, username)
    try:
        path = get_local_save_path(username)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
    return data

def load_game(username: str) -> Optional[GameState]:
    path = get_local_save_path(username)

    # One-time migration from legacy save file
    if not os.path.exists(path) and os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                legacy = json.load(f)
            if legacy.get("username") == username:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    json.dump(legacy, f, indent=2)
        except Exception:
            pass

    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if data.get("username") != username:
            return None
        return _dict_to_gs(data)
    except Exception:
        return None

def gs_from_cloud_data(save_data: dict) -> Optional[GameState]:
    """Deserialize a GameState from cloud save_data dict."""
    try:
        return _dict_to_gs(save_data)
    except Exception:
        return None

def save_game_from_cloud(username: str, save_data: dict):
    """Write cloud save_data to local disk (used after cloud download)."""
    if "username" not in save_data:
        save_data = dict(save_data)
        save_data["username"] = username
    try:
        path = get_local_save_path(username)
        with open(path, "w") as f:
            json.dump(save_data, f, indent=2)
    except Exception:
        pass

def _migrate(data: dict) -> dict:
    """Upgrade save data from older schema versions in place."""
    version = data.get("schema_version", 1)
    if version < 2:
        # Phase 1: add founder resource fields
        fd = data.get("founder") or {}
        fd.setdefault("personal_cash", 1000.0)
        fd.setdefault("vibe", 50.0)
        fd.setdefault("sanity", 100)
        data["founder"] = fd
        # Phase 1: add company finance fields
        for c in data.get("companies", []):
            c.setdefault("auto_deposit_pct", 0)
            c.setdefault("cover_from_personal", False)
            c.setdefault("months_negative", 0)
        data["schema_version"] = 2
    return data


def _dict_to_gs(data: dict) -> GameState:
    data = _migrate(data)

    fd = data.get("founder")
    if fd:
        founder = Founder(
            username=fd["username"],
            background_idx=fd["background_idx"],
            reputation=fd["reputation"],
            burnout=fd["burnout"],
            skill_prototyping=fd["skill_prototyping"],
            skill_sales=fd["skill_sales"],
            skill_tech=fd["skill_tech"],
            skill_management=fd["skill_management"],
            total_tokens_used=fd.get("total_tokens_used", 0),
            achievements=fd.get("achievements", []),
            career_history=fd.get("career_history", []),
            unlocked_research=fd.get("unlocked_research", []),
            personal_cash=float(fd.get("personal_cash", 1000.0)),
            vibe=float(fd.get("vibe", 50.0)),
            sanity=int(fd.get("sanity", 100)),
        )
    else:
        founder = None

    companies = []
    for c in data.get("companies", []):
        raw_loans = c.get("loans", [])
        loans = []
        for ln in raw_loans:
            if isinstance(ln, dict) and "principal" in ln:
                try:
                    loans.append(Loan(**ln))
                except TypeError:
                    pass  # skip malformed loan entries
        companies.append(Company(
            id=c["id"],
            name=c["name"],
            legal_style=c["legal_style"],
            focus_area=c["focus_area"],
            funding_style=c["funding_style"],
            risk_appetite=c["risk_appetite"],
            cash=c["cash"],
            monthly_revenue=c["monthly_revenue"],
            monthly_expenses=c["monthly_expenses"],
            debt=c["debt"],
            reputation=c["reputation"],
            valuation=c["valuation"],
            office_level=c["office_level"],
            mood=c["mood"],
            founded_month=c["founded_month"],
            founded_year=c["founded_year"],
            active=c.get("active", True),
            loans=loans,
            auto_deposit_pct=int(c.get("auto_deposit_pct", 0)),
            cover_from_personal=bool(c.get("cover_from_personal", False)),
            months_negative=int(c.get("months_negative", 0)),
        ))

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
        schema_version=data.get("schema_version", 2),
    )


# ─────────────────────── LOCAL ACCOUNTS (offline fallback) ────

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


# ─────────────────────── SETTINGS ─────────────────────────────

def default_settings():
    return {
        "theme": "Dark Terminal",
        "reduced_animations": False,
        "high_contrast": False,
        "ticker_speed": "normal",
        "audio": "off",
    }
