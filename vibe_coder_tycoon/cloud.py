import json
import os
from typing import Optional

from .constants import SUPABASE_URL, SUPABASE_KEY, APP_CONFIG_DIR

_SESSION_FILE = os.path.join(APP_CONFIG_DIR, "auth_session.json")

# ─────────────────────── CLOUD SERVICE ────────────────────────

class CloudService:
    """
    Thin wrapper around supabase-py. All public methods return (result, error_str).
    When Supabase is not configured or unreachable, every method returns (None, msg)
    so callers can fall back to local saves gracefully.
    """

    def __init__(self):
        self._client = None
        self._ready = False
        self._init_client()

    def _init_client(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            return
        try:
            from supabase import create_client
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self._ready = True
        except Exception:
            pass

    def _guard(self):
        """Return an error string if cloud is not available, else None."""
        if not self._ready or self._client is None:
            return "Cloud not configured."
        return None

    # ── Auth ──────────────────────────────────────────────────

    def sign_up(self, email: str, password: str):
        if err := self._guard(): return None, err
        try:
            res = self._client.auth.sign_up({"email": email, "password": password})
            if res.user:
                return res.user, None
            return None, "Sign-up failed. Try a different email."
        except Exception as e:
            return None, _clean_error(e)

    def sign_in(self, email: str, password: str):
        if err := self._guard(): return None, err
        try:
            res = self._client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                self._save_session(res.session)
                return res.session, None
            return None, "Invalid email or password."
        except Exception as e:
            return None, _clean_error(e)

    def sign_out(self):
        if err := self._guard(): return None, err
        try:
            self._client.auth.sign_out()
            self._clear_session()
            return True, None
        except Exception as e:
            self._clear_session()
            return None, _clean_error(e)

    def restore_session(self):
        """Attempt to restore a persisted session from disk. Returns (user, error)."""
        if err := self._guard(): return None, err
        try:
            data = self._load_session_data()
            if not data:
                return None, "No saved session."
            res = self._client.auth.set_session(data["access_token"], data["refresh_token"])
            if res.user:
                return res.user, None
            return None, "Session expired."
        except Exception as e:
            return None, _clean_error(e)

    def current_user_id(self) -> Optional[str]:
        if not self._ready or self._client is None:
            return None
        try:
            user = self._client.auth.get_user()
            return user.user.id if user and user.user else None
        except Exception:
            return None

    # ── Profiles ──────────────────────────────────────────────

    def create_profile(self, user_id: str, username: str, founder_name: str, background: str):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("profiles")
                   .insert({
                       "id": user_id,
                       "username": username,
                       "founder_name": founder_name,
                       "background": background,
                   })
                   .execute())
            rows = res.data
            return rows[0] if rows else None, None
        except Exception as e:
            return None, _clean_error(e)

    def get_profile(self, user_id: str):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("profiles")
                   .select("*")
                   .eq("id", user_id)
                   .execute())
            rows = res.data
            return rows[0] if rows else None, None
        except Exception as e:
            return None, _clean_error(e)

    def update_profile_stats(self, user_id: str, reputation: int, tokens_used: int,
                              projects_launched: int, companies_created: int):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("profiles")
                   .update({
                       "reputation": reputation,
                       "total_tokens_used": tokens_used,
                       "total_projects_launched": projects_launched,
                       "total_companies_created": companies_created,
                   })
                   .eq("id", user_id)
                   .execute())
            return True, None
        except Exception as e:
            return None, _clean_error(e)

    # ── Save Slots ────────────────────────────────────────────

    def upload_save(self, user_id: str, slot_name: str, save_data: dict, checksum: str):
        if err := self._guard(): return None, err
        try:
            from .constants import GAME_VERSION
            # Upsert by user_id + slot_name
            existing, _ = self._get_slot_by_name(user_id, slot_name)
            payload = {
                "user_id": user_id,
                "slot_name": slot_name,
                "game_version": GAME_VERSION,
                "save_data": save_data,
                "checksum": checksum,
                "is_active": True,
            }
            if existing:
                res = (self._client.table("save_slots")
                       .update(payload)
                       .eq("id", existing["id"])
                       .execute())
            else:
                res = (self._client.table("save_slots")
                       .insert(payload)
                       .execute())
            rows = res.data
            return rows[0] if rows else None, None
        except Exception as e:
            return None, _clean_error(e)

    def _get_slot_by_name(self, user_id: str, slot_name: str):
        try:
            res = (self._client.table("save_slots")
                   .select("id, updated_at")
                   .eq("user_id", user_id)
                   .eq("slot_name", slot_name)
                   .execute())
            rows = res.data
            return (rows[0] if rows else None), None
        except Exception as e:
            return None, _clean_error(e)

    def download_save(self, slot_id: str):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("save_slots")
                   .select("save_data")
                   .eq("id", slot_id)
                   .execute())
            rows = res.data
            if rows:
                return rows[0]["save_data"], None
            return None, "Save slot not found."
        except Exception as e:
            return None, _clean_error(e)

    def list_save_slots(self, user_id: str):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("save_slots")
                   .select("id, slot_name, game_version, updated_at, save_data->founder, save_data->year, save_data->month")
                   .eq("user_id", user_id)
                   .eq("is_active", True)
                   .order("updated_at", desc=True)
                   .execute())
            return res.data or [], None
        except Exception as e:
            return None, _clean_error(e)

    def get_latest_save_slot(self, user_id: str):
        if err := self._guard(): return None, err
        try:
            res = (self._client.table("save_slots")
                   .select("*")
                   .eq("user_id", user_id)
                   .eq("is_active", True)
                   .order("updated_at", desc=True)
                   .limit(1)
                   .execute())
            rows = res.data
            return (rows[0] if rows else None), None
        except Exception as e:
            return None, _clean_error(e)

    # ── Game Runs ─────────────────────────────────────────────

    def submit_game_run(self, user_id: str, run_data: dict):
        if err := self._guard(): return None, err
        try:
            payload = {"user_id": user_id, **run_data}
            res = self._client.table("game_runs").insert(payload).execute()
            rows = res.data
            return rows[0] if rows else None, None
        except Exception as e:
            return None, _clean_error(e)

    # ── Session Persistence ───────────────────────────────────

    def _save_session(self, session):
        try:
            os.makedirs(APP_CONFIG_DIR, exist_ok=True)
            with open(_SESSION_FILE, "w") as f:
                json.dump({
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }, f)
        except Exception:
            pass

    def _load_session_data(self) -> Optional[dict]:
        try:
            if not os.path.exists(_SESSION_FILE):
                return None
            with open(_SESSION_FILE) as f:
                return json.load(f)
        except Exception:
            return None

    def _clear_session(self):
        try:
            if os.path.exists(_SESSION_FILE):
                os.remove(_SESSION_FILE)
        except Exception:
            pass

    @property
    def is_configured(self) -> bool:
        return self._ready


# ─────────────────────── HELPERS ──────────────────────────────

def _clean_error(exc: Exception) -> str:
    msg = str(exc)
    # Strip noisy supabase-py HTTP details
    if "Invalid login credentials" in msg:
        return "Invalid email or password."
    if "User already registered" in msg:
        return "An account with this email already exists."
    if "Network" in msg or "Connection" in msg or "timeout" in msg.lower():
        return "Network error. Check your internet connection."
    # Keep it short
    return msg[:120] if len(msg) > 120 else msg
