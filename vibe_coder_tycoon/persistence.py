import json
import os
import hashlib
from typing import Optional

from .constants import SAVE_FILE, MONTH_NAMES, APP_CONFIG_DIR
from .models import GameState, Founder, Company, Project, Employee, Loan, DevSession


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

    def _project_dict(p: Project) -> dict:
        d = {k: v for k, v in p.__dict__.items() if k != "dev_session"}
        ds = p.dev_session
        if ds is not None:
            d["dev_session"] = ds.__dict__.copy()
        else:
            d["dev_session"] = None
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
        "projects": [_project_dict(p) for p in gs.projects],
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
    if version < 3:
        # Phase 2: add project dev fields
        for p in data.get("projects", []):
            p.setdefault("design_score", 0.0)
            p.setdefault("tech_score", 0.0)
            p.setdefault("quality_score", 0)
            p.setdefault("qa_level", "Skip QA")
            p.setdefault("scope", "Standard")
            p.setdefault("budget", 500)
            p.setdefault("dev_weeks", 4)
            p.setdefault("dev_day", 0)
            p.setdefault("dev_total_days", 60)
            p.setdefault("faked_features", [])
            p.setdefault("paused_dev", False)
            p.setdefault("dev_session", None)
            p.setdefault("hype", 30)
        data["schema_version"] = 3
    if version < 4:
        # Phase 3: add product lifecycle fields
        for p in data.get("projects", []):
            p.setdefault("revenue_model", "")
            p.setdefault("obsolescence_months", 0)
            p.setdefault("age_months", 0)
            p.setdefault("active_users", p.get("users", 0))
            p.setdefault("churn_rate", 0.05)
            p.setdefault("version", 1)
            p.setdefault("parent_product_id", -1)
            p.setdefault("auto_update_interval", 0)
            p.setdefault("auto_update_countdown", 0)
            p.setdefault("discontinued", False)
            p.setdefault("revenue_history", [])
        data["schema_version"] = 4
    if version < 5:
        # Phase 4: add company system fields
        for c in data.get("companies", []):
            c.setdefault("parent_company_id", -1)
            c.setdefault("history", [])
        data["schema_version"] = 5
    if version < 6:
        # Phase 5: payroll moves to finance settlement; un-bake salaries that the
        # old hire path had added directly into company monthly_expenses.
        comp_by_id = {c["id"]: c for c in data.get("companies", [])}
        for e in data.get("employees", []):
            c = comp_by_id.get(e.get("company_id"))
            if c is not None:
                c["monthly_expenses"] = max(0, c.get("monthly_expenses", 0) - int(e.get("salary", 0)))
        # add employee five-stat / XP / assignment fields
        for e in data.get("employees", []):
            base = int(e.get("skill", 50))
            e.setdefault("coding", base)
            e.setdefault("prompting", base)
            e.setdefault("research", max(1, base - 10))
            e.setdefault("marketing", max(1, base - 10))
            e.setdefault("sanity", 80)
            e.setdefault("xp", 0)
            e.setdefault("assigned_project_id", -1)
            e.setdefault("state", "active")
            e.setdefault("state_until", 0)
            e.setdefault("backstory", "")
        data["schema_version"] = 6
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
            parent_company_id=int(c.get("parent_company_id", -1)),
            history=list(c.get("history", [])),
        ))

    def _load_project(pd: dict) -> Project:
        ds_data = pd.pop("dev_session", None)
        # Remove any keys that aren't Project fields to be forward-compatible
        known = {
            "name", "ptype", "model", "stack", "niche", "company_id",
            "status", "progress", "revenue", "users", "morale", "tokens_used",
            "bug_count", "hype", "tech_debt", "launch_date", "lifetime_revenue",
            "design_score", "tech_score", "quality_score", "qa_level", "scope",
            "budget", "dev_weeks", "dev_day", "dev_total_days",
            "faked_features", "paused_dev",
            # Phase 3 fields
            "revenue_model", "obsolescence_months", "age_months", "active_users",
            "churn_rate", "version", "parent_product_id", "auto_update_interval",
            "auto_update_countdown", "discontinued", "revenue_history",
        }
        clean = {k: v for k, v in pd.items() if k in known}
        p = Project(**clean)
        if ds_data and isinstance(ds_data, dict):
            p.dev_session = DevSession(
                terminal_log=ds_data.get("terminal_log", []),
                pending_interruption=ds_data.get("pending_interruption", {}),
                interruption_choice_idx=ds_data.get("interruption_choice_idx", 0),
                action_result=ds_data.get("action_result", ""),
            )
        return p

    _emp_fields = {
        "name", "role", "level", "salary", "mood", "skill", "hired_year",
        "company_id", "trait", "loyalty", "productivity",
        "coding", "prompting", "research", "marketing", "sanity", "xp",
        "assigned_project_id", "state", "state_until", "backstory",
    }

    def _load_employee(ed: dict) -> Employee:
        clean = {k: v for k, v in ed.items() if k in _emp_fields}
        return Employee(**clean)

    projects  = [_load_project(dict(p)) for p in data.get("projects", [])]
    employees = [_load_employee(e) for e in data.get("employees", [])]
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
