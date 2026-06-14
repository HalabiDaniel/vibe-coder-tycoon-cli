import curses
import random
import sys
from typing import Optional

from .ui.colors import init_colors, PAIR_TICKER, PAIR_PANEL, PAIR_OVERLAY
from .ui.helpers import (
    safe_addstr, fill_background, draw_topbar, draw_tabs, draw_statusbar,
)
from .ui.screens.title import draw_title_screen, draw_credits, TITLE_MENU, TITLE_MENU_LOGGED_IN
from .ui.screens.profile import draw_profile
from .ui.screens.loading import run_loading_screen
from .ui.screens.auth import (
    SignInState, SignUpState, draw_sign_in, draw_sign_up,
)
from .ui.screens.settings import SettingsUIState, draw_settings_screen, SETTINGS_OPTIONS
from .ui.screens.dashboard import draw_dashboard
from .ui.screens.founder import draw_founder
from .ui.screens.companies import CompaniesUIState, draw_companies
from .ui.screens.projects import ProjectsUIState, draw_projects
from .ui.screens.development import DevUIState, draw_development
from .ui.screens.employees import EmployeesUIState, draw_employees, _assignable_projects
from .ui.screens.market import draw_market, MarketUIState, draw_stocks, draw_ipo
from .ui.screens.model_lab import draw_model_lab, ModelLabUIState
from .ui.screens.funding import draw_funding, FundingUIState
from .ui.screens.research import ResearchUIState, draw_research
from .ui.screens.news import NewsUIState, draw_news
from .ui.screens.events import draw_event_card
from .ui.screens.help import draw_help
from .ui.screens.demo_end import draw_demo_end, draw_victory, draw_game_over
from .ui.screens.account import AccountUIState, draw_account, ACCOUNT_BUTTON_COUNT, account_button_label
from .ui.screens.save_slots import SaveSlotsUIState, draw_save_slots
from .ui.screens.sync_conflict import draw_sync_conflict, CONFLICT_OPTIONS
from .models import Founder, Company, Project, Employee, GameState
from .persistence import (
    accounts_sign_in, accounts_create, save_game, load_game, default_settings,
    compute_checksum, add_to_sync_queue, flush_sync_queue,
    gs_from_cloud_data, save_game_from_cloud,
)
from .engine import make_new_game, advance_month, dispatch
from .cloud import CloudService
from .constants import (
    TABS, BACKGROUNDS, AI_SUBS, DEMO_MONTH_LIMIT, DEMO_MODE, MONTH_NAMES,
    EMPLOYEE_ROLES, EMPLOYEE_TRAITS, RESEARCH_CATEGORIES,
    COMPANY_LEGAL_STYLES, COMPANY_FOCUS_AREAS, FUNDING_STYLES, RISK_APPETITES,
    PROJECT_TYPES, TECH_STACKS, NICHES, AUTO_DEPOSIT_CYCLE, FEATURE_SCOPES, QA_OPTIONS,
    AUTO_UPDATE_CYCLES, OFFICE_LEVELS,
)
from .engine.systems.companies import (
    can_build_project_type, get_office_employee_cap, get_focus_data,
)
from .engine.systems.employees import generate_candidates


# ─────────────────────── MAIN LOOP ────────────────────────────

TICKERS = [
    "⚡ AI Index up 3.4% — investors bullish on LLM tooling",
    "💬 'I shipped a SaaS in 6 hours' — IndieScroll trending",
    "⚠️  SnapStack announces new pricing — devs panicking",
    "📣 BirdBoard top launch today: 8K users day one",
    "🌍 Beirut co-working scene expanding — builders arriving",
    "🤖 Llamurai 70B drops: open-source devs celebrate",
    "🏦 AngelBridge seed: $500K in 48h via cold emails",
    "📉 ChatNPC Turbo token costs rise 22% next quarter",
    "🔥 HuntProductive hits $50K MRR — solo founder",
    "💡 DeployGoblin acquired for $2M — rumours confirmed",
]

def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(100)

    run_loading_screen(stdscr, duration=3.0)

    # ── Cloud service (lazy-initialised; no-ops if unconfigured) ──
    cloud = CloudService()

    # ── Navigation / animation state ──
    screen = "title"
    title_sel = 0
    blink = True
    blink_tick = 0
    ticker_idx = 0
    ticker_tick = 0
    status_msg = ""

    # ── Auth UI state ──
    sign_in_state  = SignInState()
    sign_up_state  = SignUpState()
    settings_ui    = SettingsUIState()
    standalone_settings = default_settings()

    # ── Cloud / session state ──
    gs: Optional[GameState] = None
    current_user: Optional[str] = None   # display username
    cloud_user_id: Optional[str] = None  # Supabase UUID
    cloud_email: Optional[str] = None
    cloud_sync_status: str = ""          # "synced" | "pending" | "failed" | ""
    cloud_last_sync: str = "Never"
    pending_cloud_slots: list = []       # slots fetched after sign-in
    pending_cloud_slot_id: Optional[str] = None  # slot chosen from save_slots screen
    conflict_local_info: dict = {}
    conflict_cloud_info: dict = {}
    conflict_cloud_slot_id: Optional[str] = None
    conflict_sel: int = 0

    # ── Game UI state ──
    active_tab = 0
    dash_company_sel = 0
    companies_ui  = CompaniesUIState()
    projects_ui   = ProjectsUIState()
    dev_ui        = DevUIState()
    employees_ui  = EmployeesUIState()
    research_ui   = ResearchUIState()
    market_ui     = MarketUIState()
    model_lab_ui  = ModelLabUIState()
    funding_ui    = FundingUIState()
    news_ui       = NewsUIState()
    event_card_sel = 0   # Phase 13 — selection in the active event card overlay
    account_ui    = AccountUIState()
    save_slots_ui = SaveSlotsUIState()

    # ── Attempt to restore a saved session silently ──
    if cloud.is_configured:
        restored_user, _ = cloud.restore_session()
        if restored_user:
            cloud_user_id = restored_user.id
            cloud_email   = restored_user.email
            profile, _    = cloud.get_profile(cloud_user_id)
            if profile:
                current_user = profile.get("username", cloud_email)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        blink_tick += 1
        if blink_tick >= 5:
            blink_tick = 0
            blink = not blink

        ticker_tick += 1
        if ticker_tick >= 60:
            ticker_tick = 0
            ticker_idx = (ticker_idx + 1) % len(TICKERS)

        # ── DRAW ──────────────────────────────────────────────
        if screen == "title":
            draw_title_screen(stdscr, title_sel, blink, current_user)

        elif screen == "sign_in":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_in(stdscr, sign_in_state, blink)

        elif screen == "sign_up":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_up(stdscr, sign_up_state, blink)

        elif screen == "profile":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_profile(stdscr, current_user or "—", cloud_email or "—", pending_cloud_slots)

        elif screen == "credits":
            draw_credits(stdscr)

        elif screen == "settings_pre":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_settings_screen(stdscr, None, settings_ui, standalone_settings)

        elif screen == "save_slots":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_save_slots(stdscr, pending_cloud_slots, save_slots_ui)

        elif screen == "sync_conflict":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sync_conflict(stdscr, conflict_local_info, conflict_cloud_info, conflict_sel)

        elif screen == "account":
            fill_background(stdscr, PAIR_OVERLAY)
            cloud_info = {
                "username":     current_user or "—",
                "email":        cloud_email or "—",
                "founder_name": gs.founder.username if gs and gs.founder else "—",
                "background":   BACKGROUNDS[gs.founder.background_idx]["name"]
                                if gs and gs.founder else "—",
                "login_status": "Signed In" if cloud_user_id else "Offline",
                "last_sync":    cloud_last_sync,
                "slot_name":    "autosave",
                "is_configured": cloud.is_configured,
            }
            draw_account(stdscr, gs, account_ui, cloud_info)

        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            if gs.victory and not gs.endgame_continue:
                draw_victory(stdscr, gs)
            elif gs.game_over:
                draw_game_over(stdscr, gs)
            elif gs.demo_ended:
                draw_demo_end(stdscr, gs)
            else:
                fill_background(stdscr, PAIR_PANEL)
                draw_topbar(stdscr, gs)
                draw_tabs(stdscr, active_tab)

                tab = TABS[active_tab]
                if tab == "Dashboard":
                    draw_dashboard(stdscr, gs, dash_company_sel)
                elif tab == "Founder":
                    draw_founder(stdscr, gs)
                elif tab == "Companies":
                    if companies_ui.view == "funding":
                        sel_cid = (gs.companies[companies_ui.selected].id
                                   if gs.companies and 0 <= companies_ui.selected < len(gs.companies)
                                   else 0)
                        draw_funding(stdscr, gs, funding_ui, sel_cid)
                    else:
                        draw_companies(stdscr, gs, companies_ui)
                elif tab == "Projects":
                    if projects_ui.view == "dev":
                        draw_development(stdscr, gs, projects_ui.dev_project_idx, dev_ui)
                    else:
                        draw_projects(stdscr, gs, projects_ui)
                elif tab == "Employees":
                    draw_employees(stdscr, gs, employees_ui)
                elif tab == "Market":
                    if market_ui.view == "model_lab":
                        draw_model_lab(stdscr, gs, model_lab_ui)
                    elif market_ui.view == "stocks":
                        draw_stocks(stdscr, gs, market_ui)
                    elif market_ui.view == "ipo":
                        draw_ipo(stdscr, gs, market_ui)
                    else:
                        draw_market(stdscr, gs, market_ui)
                elif tab == "Research":
                    draw_research(stdscr, gs, research_ui)
                elif tab == "News":
                    draw_news(stdscr, gs, news_ui)
                elif tab == "Settings":
                    draw_settings_screen(stdscr, gs, settings_ui)
                elif tab == "Help":
                    draw_help(stdscr)

                ticker_msg = TICKERS[ticker_idx]
                safe_addstr(stdscr, h-2, 2, f" ▶ {ticker_msg} ",
                            curses.color_pair(PAIR_TICKER))

                sync_indicator = ""
                if cloud_sync_status == "synced":
                    sync_indicator = " ☁ synced"
                elif cloud_sync_status == "pending":
                    sync_indicator = " ⚠ sync pending"
                elif cloud_sync_status == "failed":
                    sync_indicator = " ✗ sync failed"
                draw_statusbar(stdscr, status_msg + sync_indicator)

                # Phase 13 — event choice card overlay (drawn on top of all tabs)
                if gs.pending_event_cards:
                    card = gs.pending_event_cards[0]
                    event_card_sel = max(0, min(event_card_sel,
                                                len(card.get("choices", [])) - 1))
                    draw_event_card(stdscr, card, event_card_sel)

        stdscr.refresh()

        # ── INPUT ─────────────────────────────────────────────
        key = stdscr.getch()
        if key == -1:
            continue

        # ── TITLE SCREEN ──────────────────────────────────────
        if screen == "title":
            active_menu = TITLE_MENU_LOGGED_IN if current_user else TITLE_MENU
            if key == curses.KEY_UP:
                title_sel = (title_sel - 1) % len(active_menu)
            elif key == curses.KEY_DOWN:
                title_sel = (title_sel + 1) % len(active_menu)
            elif key in (10, curses.KEY_ENTER, ord(' ')):
                sel_key, sel_label = active_menu[title_sel]
                if sel_key == "Q":
                    break
                elif sel_key == "S":
                    sign_in_state = SignInState()
                    sign_in_state.fields[0]["label"] = "Email Address"
                    screen = "sign_in"
                elif sel_key == "C":
                    sign_up_state = SignUpState()
                    screen = "sign_up"
                elif sel_key == "P":
                    screen = "profile"
                elif sel_key == "X":
                    cloud.sign_out()
                    cloud_user_id = None
                    cloud_email = None
                    current_user = None
                    cloud_sync_status = ""
                    gs = None
                    title_sel = 0
                elif sel_key == "O":
                    if current_user:
                        # Load cloud or local save for logged-in user
                        if cloud_user_id:
                            slots, _ = cloud.list_save_slots(cloud_user_id)
                            pending_cloud_slots = slots or []
                            if pending_cloud_slots:
                                save_data, _ = cloud.download_save(pending_cloud_slots[0]["id"])
                                if save_data:
                                    gs = gs_from_cloud_data(save_data) or load_game(current_user)
                                    cloud_sync_status = "synced"
                                    cloud_last_sync = _now_str()
                                else:
                                    gs = load_game(current_user)
                            else:
                                gs = load_game(current_user)
                        else:
                            gs = load_game(current_user)
                        if gs is None:
                            gs = make_new_game(_default_founder(current_user), 0)
                        run_loading_screen(stdscr)
                        screen = "game"
                        active_tab = 0
                        status_msg = f"Welcome back, {current_user}!"
                    else:
                        founder = Founder(
                            username="OfflineFounder",
                            background_idx=0,
                            reputation=20, burnout=0,
                            skill_prototyping=40, skill_sales=20,
                            skill_tech=35, skill_management=20,
                            total_tokens_used=0,
                        )
                        gs = make_new_game(founder, 0)
                        current_user = None
                        cloud_user_id = None
                        run_loading_screen(stdscr)
                        screen = "game"
                        active_tab = 0
                        status_msg = "Playing offline. Progress will not be saved."
                elif sel_key == "T":
                    screen = "settings_pre"
                elif sel_key == "R":
                    screen = "credits"
            elif key == ord('q') or key == ord('Q'):
                break
            elif key == ord('p') or key == ord('P'):
                if current_user:
                    screen = "profile"
            elif key == ord('x') or key == ord('X'):
                if current_user:
                    cloud.sign_out()
                    cloud_user_id = None
                    cloud_email = None
                    current_user = None
                    cloud_sync_status = ""
                    gs = None
                    title_sel = 0
            elif key == ord('s') or key == ord('S'):
                if not current_user:
                    sign_in_state = SignInState()
                    sign_in_state.fields[0]["label"] = "Email Address"
                    screen = "sign_in"
            elif key == ord('c') or key == ord('C'):
                if not current_user:
                    sign_up_state = SignUpState()
                    screen = "sign_up"
            elif key == ord('o') or key == ord('O'):
                if current_user:
                    if cloud_user_id:
                        slots, _ = cloud.list_save_slots(cloud_user_id)
                        pending_cloud_slots = slots or []
                        if pending_cloud_slots:
                            save_data, _ = cloud.download_save(pending_cloud_slots[0]["id"])
                            if save_data:
                                gs = gs_from_cloud_data(save_data) or load_game(current_user)
                                cloud_sync_status = "synced"
                                cloud_last_sync = _now_str()
                            else:
                                gs = load_game(current_user)
                        else:
                            gs = load_game(current_user)
                    else:
                        gs = load_game(current_user)
                    if gs is None:
                        gs = make_new_game(_default_founder(current_user), 0)
                    run_loading_screen(stdscr)
                    screen = "game"
                    status_msg = f"Welcome back, {current_user}!"
                else:
                    founder = Founder(
                        username="OfflineFounder",
                        background_idx=0,
                        reputation=20, burnout=0,
                        skill_prototyping=40, skill_sales=20,
                        skill_tech=35, skill_management=20,
                        total_tokens_used=0,
                    )
                    gs = make_new_game(founder, 0)
                    current_user = None
                    cloud_user_id = None
                    run_loading_screen(stdscr)
                    screen = "game"
                    status_msg = "Playing offline."
            elif key == ord('r') or key == ord('R'):
                screen = "credits"
            elif key == ord('t') or key == ord('T'):
                screen = "settings_pre"

        # ── SIGN IN ───────────────────────────────────────────
        elif screen == "sign_in":
            if sign_in_state.step == "welcome":
                if key in (10, curses.KEY_ENTER, 27):
                    _do_enter_game(stdscr, gs)
                    screen = "game"
                    status_msg = f"Welcome back, {current_user}!"
                    if cloud_user_id:
                        flush_sync_queue(cloud, cloud_user_id)
            else:
                if key == 27:
                    screen = "title"
                elif key == curses.KEY_UP:
                    sign_in_state.focused = max(0, sign_in_state.focused - 1)
                elif key == curses.KEY_DOWN:
                    sign_in_state.focused = min(len(sign_in_state.fields)-1,
                                                sign_in_state.focused + 1)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    f = sign_in_state.fields[sign_in_state.focused]
                    f["value"] = f["value"][:-1]
                elif key in (10, curses.KEY_ENTER):
                    email = sign_in_state.fields[0]["value"].strip()
                    pw    = sign_in_state.fields[1]["value"]
                    if not email or not pw:
                        sign_in_state.message = "Please fill in both fields."
                    else:
                        session, err = cloud.sign_in(email, pw)
                        if session:
                            cloud_user_id = session.user.id
                            cloud_email   = session.user.email
                            profile, _    = cloud.get_profile(cloud_user_id)
                            current_user  = (profile.get("username") if profile else None) or email

                            # Fetch cloud saves
                            slots, _ = cloud.list_save_slots(cloud_user_id)
                            pending_cloud_slots = slots or []
                            local_save = load_game(current_user)
                            has_local = local_save is not None

                            if pending_cloud_slots and has_local:
                                # Conflict: show resolution screen
                                latest_slot = pending_cloud_slots[0]
                                conflict_cloud_slot_id = latest_slot["id"]
                                cloud_save_data, _ = cloud.download_save(conflict_cloud_slot_id)
                                conflict_local_info = _save_summary(local_save)
                                if cloud_save_data:
                                    cloud_gs = gs_from_cloud_data(cloud_save_data)
                                    conflict_cloud_info = _save_summary(cloud_gs)
                                else:
                                    conflict_cloud_info = {}
                                conflict_sel = 0
                                screen = "sync_conflict"
                            elif pending_cloud_slots:
                                # No local — download latest cloud save
                                latest_slot = pending_cloud_slots[0]
                                save_data, dl_err = cloud.download_save(latest_slot["id"])
                                if save_data:
                                    save_game_from_cloud(current_user, save_data)
                                    gs = gs_from_cloud_data(save_data) or load_game(current_user)
                                else:
                                    gs = make_new_game(_default_founder(current_user), 0)
                                _post_sign_in(sign_in_state, current_user, profile)
                                run_loading_screen(stdscr)
                                screen = "game"
                                status_msg = f"Welcome back, {current_user}! Cloud save loaded."
                                cloud_sync_status = "synced"
                            else:
                                # No cloud saves — load local or new
                                gs = local_save or make_new_game(_default_founder(current_user), 0)
                                _post_sign_in(sign_in_state, current_user, profile)
                                run_loading_screen(stdscr)
                                screen = "game"
                                status_msg = f"Welcome, {current_user}!"
                        else:
                            # Cloud sign-in failed — try local fallback
                            local_name, local_data = accounts_sign_in(email, pw)
                            if local_name:
                                current_user  = local_name
                                cloud_user_id = None
                                sign_in_state.success_name   = local_name
                                sign_in_state.success_date   = local_data.get("last_played", "—")
                                sign_in_state.success_status = local_data.get("founder_status", "Rookie Founder")
                                sign_in_state.step = "welcome"
                                gs = load_game(current_user) or make_new_game(_default_founder(current_user), 0)
                            else:
                                sign_in_state.message = err or "Invalid email or password."
                elif 32 <= key < 127:
                    f = sign_in_state.fields[sign_in_state.focused]
                    if len(f["value"]) < 80:
                        f["value"] += chr(key)

        # ── SIGN UP ───────────────────────────────────────────
        elif screen == "sign_up":
            if sign_up_state.step == "form":
                if key == 27:
                    screen = "title"
                elif key == curses.KEY_UP:
                    sign_up_state.focused = max(0, sign_up_state.focused - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.focused = min(len(sign_up_state.fields)-1,
                                                sign_up_state.focused + 1)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    f = sign_up_state.fields[sign_up_state.focused]
                    f["value"] = f["value"][:-1]
                elif key in (10, curses.KEY_ENTER):
                    uname = sign_up_state.fields[0]["value"].strip()
                    email = sign_up_state.fields[1]["value"].strip()
                    pw1   = sign_up_state.fields[2]["value"]
                    pw2   = sign_up_state.fields[3]["value"]
                    if not uname or not email or not pw1:
                        sign_up_state.message = "All fields are required."
                    elif pw1 != pw2:
                        sign_up_state.message = "Passwords do not match."
                    elif len(uname) < 3:
                        sign_up_state.message = "Username must be at least 3 characters."
                    else:
                        user, err = cloud.sign_up(email, pw1)
                        if user:
                            cloud_user_id = user.id
                            cloud_email   = user.email
                            current_user  = uname
                            sign_up_state.step = "founder"
                        elif err and "Cloud not configured" in err:
                            # Offline fallback: create local account
                            ok, msg = accounts_create(uname, email, pw1)
                            if ok:
                                current_user  = uname
                                cloud_user_id = None
                                sign_up_state.step = "founder"
                            else:
                                sign_up_state.message = msg
                        else:
                            sign_up_state.message = err or "Sign-up failed."
                elif 32 <= key < 127:
                    f = sign_up_state.fields[sign_up_state.focused]
                    mx = f.get("max", 80)
                    if len(f["value"]) < mx:
                        f["value"] += chr(key)

            elif sign_up_state.step == "founder":
                if key == 27:
                    sign_up_state.step = "form"
                elif key == curses.KEY_UP:
                    sign_up_state.founder_bg_sel = max(0, sign_up_state.founder_bg_sel - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.founder_bg_sel = min(len(BACKGROUNDS)-1,
                                                       sign_up_state.founder_bg_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    sign_up_state.step = "ai_sub"

            elif sign_up_state.step == "ai_sub":
                if key == 27:
                    sign_up_state.step = "founder"
                elif key == curses.KEY_UP:
                    sign_up_state.ai_sub_sel = max(0, sign_up_state.ai_sub_sel - 1)
                elif key == curses.KEY_DOWN:
                    sign_up_state.ai_sub_sel = min(len(AI_SUBS)-1,
                                                   sign_up_state.ai_sub_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    bg_idx = sign_up_state.founder_bg_sel
                    bg     = BACKGROUNDS[bg_idx]
                    founder = Founder(
                        username=current_user,
                        background_idx=bg_idx,
                        reputation=20,
                        burnout=0,
                        skill_prototyping=40 + bg["bonuses"]["prototyping"],
                        skill_sales=20      + bg["bonuses"]["sales"],
                        skill_tech=35       + bg["bonuses"]["tech_skill"],
                        skill_management=20 + bg["bonuses"]["burnout_resist"],
                        total_tokens_used=0,
                    )
                    gs = make_new_game(founder, sign_up_state.ai_sub_sel)
                    # Save locally first
                    save_data = save_game(gs, current_user)
                    # Create cloud profile + upload initial save
                    if cloud_user_id:
                        cloud.create_profile(
                            cloud_user_id,
                            current_user,
                            current_user,
                            bg["name"],
                        )
                        checksum = compute_checksum(save_data)
                        _, upload_err = cloud.upload_save(cloud_user_id, "autosave", save_data, checksum)
                        cloud_sync_status = "failed" if upload_err else "synced"
                        if not upload_err:
                            cloud_last_sync = _now_str()
                    run_loading_screen(stdscr)
                    screen = "game"
                    status_msg = f"Welcome, {current_user}! Your journey begins."

        # ── CREDITS ───────────────────────────────────────────
        elif screen == "credits":
            if key in (27, 10, curses.KEY_ENTER, ord('q'), ord('Q')):
                screen = "title"

        # ── PROFILE ───────────────────────────────────────────
        elif screen == "profile":
            if key in (27, 10, curses.KEY_ENTER, ord('q'), ord('Q')):
                screen = "title"

        # ── SETTINGS (pre-game) ───────────────────────────────
        elif screen == "settings_pre":
            if key == 27 or key in (10, curses.KEY_ENTER):
                screen = "title"
            elif key == curses.KEY_UP:
                settings_ui.focused = max(0, settings_ui.focused - 1)
            elif key == curses.KEY_DOWN:
                settings_ui.focused = min(len(settings_ui.keys)-1,
                                          settings_ui.focused + 1)
            else:
                _handle_settings_key(key, settings_ui, standalone_settings)

        # ── SAVE SLOTS ────────────────────────────────────────
        elif screen == "save_slots":
            all_entries = list(pending_cloud_slots) + [{"_new": True}]
            if key == 27:
                screen = "title"
            elif key == curses.KEY_UP:
                save_slots_ui.selected = max(0, save_slots_ui.selected - 1)
            elif key == curses.KEY_DOWN:
                save_slots_ui.selected = min(len(all_entries)-1,
                                             save_slots_ui.selected + 1)
            elif key in (10, curses.KEY_ENTER):
                chosen = all_entries[save_slots_ui.selected]
                if chosen.get("_new"):
                    gs = make_new_game(_default_founder(current_user), 0)
                else:
                    save_data, dl_err = cloud.download_save(chosen["id"])
                    if save_data:
                        save_game_from_cloud(current_user, save_data)
                        gs = gs_from_cloud_data(save_data)
                        cloud_sync_status = "synced"
                        cloud_last_sync = _now_str()
                    else:
                        save_slots_ui.message = f"Failed to load: {dl_err}"
                        continue
                if gs is None:
                    gs = make_new_game(_default_founder(current_user), 0)
                run_loading_screen(stdscr)
                screen = "game"
                active_tab = 0

        # ── SYNC CONFLICT ─────────────────────────────────────
        elif screen == "sync_conflict":
            if key == curses.KEY_UP:
                conflict_sel = max(0, conflict_sel - 1)
            elif key == curses.KEY_DOWN:
                conflict_sel = min(len(CONFLICT_OPTIONS)-1, conflict_sel + 1)
            elif key in (10, curses.KEY_ENTER):
                local_save = load_game(current_user)
                if conflict_sel == 0:
                    # Upload local → overwrite cloud
                    if local_save and cloud_user_id:
                        save_data = save_game(local_save, current_user)
                        checksum  = compute_checksum(save_data)
                        cloud.upload_save(cloud_user_id, "autosave", save_data, checksum)
                        cloud_sync_status = "synced"
                        cloud_last_sync   = _now_str()
                    gs = local_save or make_new_game(_default_founder(current_user), 0)
                elif conflict_sel == 1:
                    # Download cloud → overwrite local
                    save_data, _ = cloud.download_save(conflict_cloud_slot_id)
                    if save_data:
                        save_game_from_cloud(current_user, save_data)
                        gs = gs_from_cloud_data(save_data)
                        cloud_sync_status = "synced"
                        cloud_last_sync   = _now_str()
                    else:
                        gs = local_save or make_new_game(_default_founder(current_user), 0)
                elif conflict_sel == 2:
                    # Keep both: upload local as "local-backup", use local
                    if local_save and cloud_user_id:
                        save_data = save_game(local_save, current_user)
                        checksum  = compute_checksum(save_data)
                        cloud.upload_save(cloud_user_id, "local-backup", save_data, checksum)
                    gs = local_save or make_new_game(_default_founder(current_user), 0)
                else:
                    # Stay offline
                    gs = local_save or make_new_game(_default_founder(current_user), 0)
                    cloud_user_id = None

                if gs is None:
                    gs = make_new_game(_default_founder(current_user), 0)
                run_loading_screen(stdscr)
                screen = "game"
                active_tab = 0
                status_msg = f"Welcome back, {current_user}!"

        # ── ACCOUNT SCREEN ────────────────────────────────────
        elif screen == "account":
            if key == 27:
                screen = "game" if gs else "title"
            elif key == curses.KEY_LEFT:
                account_ui.selected = (account_ui.selected - 1) % ACCOUNT_BUTTON_COUNT
            elif key == curses.KEY_RIGHT:
                account_ui.selected = (account_ui.selected + 1) % ACCOUNT_BUTTON_COUNT
            elif key in (10, curses.KEY_ENTER):
                action = account_button_label(account_ui.selected)
                if action == "Sync Now":
                    if cloud_user_id and gs and current_user:
                        save_data = save_game(gs, current_user)
                        checksum  = compute_checksum(save_data)
                        _, err = cloud.upload_save(cloud_user_id, "autosave", save_data, checksum)
                        if err:
                            account_ui.message = f"Sync failed: {err}"
                            cloud_sync_status  = "failed"
                        else:
                            account_ui.message  = "Cloud save complete."
                            cloud_sync_status   = "synced"
                            cloud_last_sync     = _now_str()
                    else:
                        account_ui.message = "Not signed in."
                elif action == "Log Out":
                    cloud.sign_out()
                    cloud_user_id = None
                    cloud_email   = None
                    cloud_sync_status = ""
                    account_ui.message = "Signed out."
                    screen = "title"
                    gs = None
                    current_user = None
                elif action == "Delete Local Session":
                    cloud.sign_out()
                    cloud_user_id = None
                    cloud_email   = None
                    cloud_sync_status = ""
                    account_ui.message = "Local session cleared."
                elif action == "Back":
                    screen = "game" if gs else "title"

        # ── IN GAME ───────────────────────────────────────────
        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            # Phase 14 — victory screen: continue, restart, or quit
            if gs.victory and not gs.endgame_continue:
                if key == ord('q') or key == ord('Q'):
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    break
                elif key == ord('c') or key == ord('C'):
                    dispatch(gs, "continue_after_win")
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    status_msg = "Empire continues. Go bigger."
                elif key == ord('r') or key == ord('R'):
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    screen = "title"
                    gs = None
                continue

            # Phase 14 — game over: restart or quit
            if gs.game_over:
                if key == ord('q') or key == ord('Q'):
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    break
                elif key == ord('r') or key == ord('R'):
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    screen = "title"
                    gs = None
                continue

            if gs.demo_ended:
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('r') or key == ord('R'):
                    # Submit game run to cloud before resetting
                    if cloud_user_id and gs:
                        _submit_game_run(cloud, cloud_user_id, gs)
                    screen = "title"
                    gs = None
                continue

            # Phase 13 — an open event card blocks other input until resolved
            if gs.pending_event_cards:
                card = gs.pending_event_cards[0]
                choices = card.get("choices", [])
                if key == curses.KEY_UP:
                    event_card_sel = max(0, event_card_sel - 1)
                elif key == curses.KEY_DOWN:
                    event_card_sel = min(len(choices) - 1, event_card_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    result = dispatch(gs, "resolve_event_choice",
                                      card_id=card.get("card_id"),
                                      choice_idx=event_card_sel)
                    status_msg = result.message
                    event_card_sel = 0
                continue

            if key == ord('q') or key == ord('Q'):
                if current_user:
                    save_data = save_game(gs, current_user)
                    if cloud_user_id:
                        checksum = compute_checksum(save_data)
                        _, err = cloud.upload_save(cloud_user_id, "autosave", save_data, checksum)
                        if err:
                            add_to_sync_queue(current_user, save_data)
                            cloud_sync_status = "pending"
                        else:
                            cloud_sync_status = "synced"
                            cloud_last_sync = _now_str()
                    status_msg = ""
                gs = None
                screen = "title"
                title_sel = 0
                active_tab = 0
                continue

            # Open account screen
            if key == ord('a') or key == ord('A'):
                account_ui = AccountUIState()
                screen = "account"
                continue

            if key == ord('\t'):
                active_tab = (active_tab + 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"
            elif key == curses.KEY_BTAB:
                active_tab = (active_tab - 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"

            tab = TABS[active_tab]

            if key in (ord('n'), ord('N')):
                status_msg = advance_month(gs)
                if current_user:
                    save_data = save_game(gs, current_user)
                    if cloud_user_id:
                        checksum = compute_checksum(save_data)
                        _, err = cloud.upload_save(cloud_user_id, "autosave", save_data, checksum)
                        if err:
                            add_to_sync_queue(current_user, save_data)
                            cloud_sync_status = "pending"
                        else:
                            cloud_sync_status = "synced"
                            cloud_last_sync = _now_str()
                if DEMO_MODE and gs.months_elapsed >= DEMO_MONTH_LIMIT:
                    gs.demo_ended = True
                    if cloud_user_id:
                        _submit_game_run(cloud, cloud_user_id, gs)
                continue

            if tab == "Dashboard":
                if key == curses.KEY_UP:
                    dash_company_sel = max(0, dash_company_sel - 1)
                elif key == curses.KEY_DOWN:
                    dash_company_sel = min(len(gs.active_companies())-1,
                                           dash_company_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    active_tab = TABS.index("Companies")

            elif tab == "Companies":
                if companies_ui.view == "list":
                    if key == curses.KEY_UP:
                        companies_ui.selected = max(0, companies_ui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        companies_ui.selected = min(len(gs.companies)-1,
                                                    companies_ui.selected + 1)
                    elif key in (ord('n'), ord('N')):
                        companies_ui.view = "new"
                        companies_ui.message = ""
                    elif key in (10, curses.KEY_ENTER):
                        pass  # stay in list; detail is inline below
                    elif gs.companies and 0 <= companies_ui.selected < len(gs.companies):
                        sel_c = gs.companies[companies_ui.selected]
                        if key in (ord('d'), ord('D')):
                            companies_ui.view = "deposit"
                            companies_ui.finance_amount = ""
                            companies_ui.message = ""
                        elif key in (ord('w'), ord('W')):
                            companies_ui.view = "withdraw"
                            companies_ui.finance_amount = ""
                            companies_ui.message = ""
                        elif key in (ord('t'), ord('T')):
                            cur = sel_c.auto_deposit_pct
                            try:
                                idx = AUTO_DEPOSIT_CYCLE.index(cur)
                            except ValueError:
                                idx = 0
                            new_pct = AUTO_DEPOSIT_CYCLE[(idx + 1) % len(AUTO_DEPOSIT_CYCLE)]
                            result = dispatch(gs, "set_auto_deposit",
                                              company_id=sel_c.id, pct=new_pct)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('c'), ord('C')):
                            result = dispatch(gs, "toggle_cover_personal",
                                              company_id=sel_c.id)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('o'), ord('O')):
                            result = dispatch(gs, "upgrade_office",
                                              company_id=sel_c.id)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('l'), ord('L')):
                            result = dispatch(gs, "upgrade_legal",
                                              company_id=sel_c.id)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('i'), ord('I')):
                            companies_ui.view = "infra"
                            companies_ui.infra_gpu_sel = 0
                            companies_ui.message = ""
                        elif key in (ord('h'), ord('H')):
                            focus_d = get_focus_data(sel_c.focus_area)
                            if focus_d and focus_d["name"] == "Holding Company":
                                companies_ui.view = "holding"
                            else:
                                companies_ui.message = "✗ Only Holding Company focus has a holding view."
                        elif key in (ord('f'), ord('F')):
                            companies_ui.view = "funding"
                            funding_ui.view = "list"
                            funding_ui.message = ""

                elif companies_ui.view == "holding":
                    if key == 27:
                        companies_ui.view = "list"
                        companies_ui.message = ""
                    elif key in (ord('s'), ord('S')):
                        holding = (gs.companies[companies_ui.selected]
                                   if gs.companies and 0 <= companies_ui.selected < len(gs.companies)
                                   else None)
                        if holding is not None:
                            subs = [c for c in gs.companies
                                    if c.parent_company_id == holding.id and c.active]
                            swept = 0
                            for sub in subs:
                                if sub.cash > 0:
                                    res = dispatch(gs, "transfer_between_companies",
                                                   from_id=sub.id, to_id=holding.id,
                                                   amount=sub.cash)
                                    if res.ok:
                                        swept += 1
                            if swept:
                                companies_ui.message = f"✓ Swept cash from {swept} subsidiary(ies)."
                            else:
                                companies_ui.message = "✗ Nothing to sweep."
                            status_msg = companies_ui.message

                elif companies_ui.view == "infra":
                    from .constants import HOSTING_PROVIDERS, GPU_GENERATIONS
                    sel_c = (gs.companies[companies_ui.selected]
                             if gs.companies and 0 <= companies_ui.selected < len(gs.companies)
                             else None)
                    if key == 27:
                        companies_ui.view = "list"
                        companies_ui.message = ""
                    elif sel_c is not None:
                        if key == curses.KEY_UP:
                            companies_ui.infra_gpu_sel = max(0, companies_ui.infra_gpu_sel - 1)
                        elif key == curses.KEY_DOWN:
                            companies_ui.infra_gpu_sel = min(len(GPU_GENERATIONS) - 1,
                                                             companies_ui.infra_gpu_sel + 1)
                        elif key in (ord('p'), ord('P')):
                            names = [h["name"] for h in HOSTING_PROVIDERS]
                            cur = names.index(sel_c.hosting_provider) if sel_c.hosting_provider in names else 0
                            nxt = names[(cur + 1) % len(names)]
                            result = dispatch(gs, "set_hosting", company_id=sel_c.id, provider=nxt)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('g'), ord('G')):
                            gpu = GPU_GENERATIONS[companies_ui.infra_gpu_sel]
                            result = dispatch(gs, "buy_gpu", company_id=sel_c.id, gpu_name=gpu["name"])
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('d'), ord('D')):
                            result = dispatch(gs, "upgrade_datacenter", company_id=sel_c.id)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('s'), ord('S')):
                            result = dispatch(gs, "toggle_compute_sale", company_id=sel_c.id)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message

                elif companies_ui.view == "funding":
                    sel_cid = (gs.companies[companies_ui.selected].id
                               if gs.companies and 0 <= companies_ui.selected < len(gs.companies)
                               else 0)
                    if funding_ui.view == "apply_loan":
                        if key == 27:
                            funding_ui.view = "list"
                            funding_ui.message = ""
                        elif key == curses.KEY_UP:
                            eligible = __import__(
                                "vibe_coder_tycoon.engine.systems.investors",
                                fromlist=["get_eligible_lenders"]
                            ).get_eligible_lenders(gs, sel_cid)
                            funding_ui.lender_sel = max(0, funding_ui.lender_sel - 1)
                        elif key == curses.KEY_DOWN:
                            from .engine.systems.investors import get_eligible_lenders
                            eligible = get_eligible_lenders(gs, sel_cid)
                            funding_ui.lender_sel = min(max(0, len(eligible) - 1),
                                                        funding_ui.lender_sel + 1)
                        elif key in (curses.KEY_BACKSPACE, 127, 8):
                            funding_ui.loan_amount = funding_ui.loan_amount[:-1]
                        elif 48 <= key <= 57:
                            if len(funding_ui.loan_amount) < 10:
                                funding_ui.loan_amount += chr(key)
                        elif key in (10, curses.KEY_ENTER):
                            from .engine.systems.investors import get_eligible_lenders
                            eligible = get_eligible_lenders(gs, sel_cid)
                            if eligible:
                                lender = eligible[funding_ui.lender_sel]
                                try:
                                    amount = int(funding_ui.loan_amount or "0")
                                except ValueError:
                                    amount = 0
                                result = dispatch(gs, "apply_for_loan",
                                                  company_id=sel_cid,
                                                  lender_name=lender["name"],
                                                  amount=amount)
                                funding_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                                status_msg = result.message
                                if result.ok:
                                    funding_ui.view = "list"
                                    funding_ui.loan_amount = ""
                    else:
                        if key == 27:
                            companies_ui.view = "list"
                            funding_ui.message = ""
                        elif key == curses.KEY_UP:
                            funding_ui.offer_sel = max(0, funding_ui.offer_sel - 1)
                        elif key == curses.KEY_DOWN:
                            funding_ui.offer_sel = min(max(0, len(gs.pending_offers) - 1),
                                                       funding_ui.offer_sel + 1)
                        elif key in (ord('a'), ord('A')):
                            if gs.pending_offers and 0 <= funding_ui.offer_sel < len(gs.pending_offers):
                                offer = gs.pending_offers[funding_ui.offer_sel]
                                result = dispatch(gs, "accept_investor_offer",
                                                  offer_id=offer["offer_id"],
                                                  company_id=sel_cid)
                                funding_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                                status_msg = result.message
                                funding_ui.offer_sel = 0
                        elif key in (ord('x'), ord('X')):
                            if gs.pending_offers and 0 <= funding_ui.offer_sel < len(gs.pending_offers):
                                offer = gs.pending_offers[funding_ui.offer_sel]
                                result = dispatch(gs, "reject_investor_offer",
                                                  offer_id=offer["offer_id"])
                                funding_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                                status_msg = result.message
                                funding_ui.offer_sel = 0
                        elif key in (ord('n'), ord('N')):
                            if gs.pending_offers and 0 <= funding_ui.offer_sel < len(gs.pending_offers):
                                offer = gs.pending_offers[funding_ui.offer_sel]
                                result = dispatch(gs, "negotiate_offer",
                                                  offer_id=offer["offer_id"])
                                funding_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                                status_msg = result.message
                        elif key in (ord('l'), ord('L')):
                            funding_ui.view = "apply_loan"
                            funding_ui.loan_amount = ""
                            funding_ui.lender_sel = 0
                            funding_ui.message = ""

                elif companies_ui.view == "new":
                    if key == 27:
                        companies_ui.view = "list"
                    else:
                        _handle_new_company_keys(key, companies_ui, gs)

                elif companies_ui.view in ("deposit", "withdraw"):
                    if key == 27:
                        companies_ui.view = "list"
                        companies_ui.message = ""
                    elif key in (curses.KEY_BACKSPACE, 127, 8):
                        companies_ui.finance_amount = companies_ui.finance_amount[:-1]
                    elif 48 <= key <= 57:  # digits 0-9
                        if len(companies_ui.finance_amount) < 10:
                            companies_ui.finance_amount += chr(key)
                    elif key in (10, curses.KEY_ENTER):
                        try:
                            amount = int(companies_ui.finance_amount or "0")
                        except ValueError:
                            amount = 0
                        if amount <= 0:
                            companies_ui.message = "✗ Enter a positive amount."
                        elif gs.companies and 0 <= companies_ui.selected < len(gs.companies):
                            cid = gs.companies[companies_ui.selected].id
                            action = ("deposit_to_company" if companies_ui.view == "deposit"
                                      else "withdraw_to_personal")
                            result = dispatch(gs, action, company_id=cid, amount=amount)
                            companies_ui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                            if result.ok:
                                companies_ui.view = "list"

            elif tab == "Projects":
                _DEV_FILTERS = ["All", "In Dev", "Dev Complete", "Launched", "Growing", "Failed", "Archived", "Sold"]

                if projects_ui.view == "dev":
                    p_idx = projects_ui.dev_project_idx
                    p = gs.projects[p_idx] if 0 <= p_idx < len(gs.projects) else None
                    ds = p.dev_session if p else None

                    if key == 27:
                        projects_ui.view = "list"
                    elif ds and ds.pending_interruption:
                        # Route keys to interruption overlay
                        choices = ds.pending_interruption.get("choices", [])
                        if key == curses.KEY_UP:
                            ds.interruption_choice_idx = max(0, ds.interruption_choice_idx - 1)
                        elif key == curses.KEY_DOWN:
                            ds.interruption_choice_idx = min(len(choices)-1, ds.interruption_choice_idx + 1)
                        elif key in (10, curses.KEY_ENTER):
                            result = dispatch(gs, "dev_resolve_interruption",
                                              project_idx=p_idx,
                                              choice_idx=ds.interruption_choice_idx)
                            status_msg = result.message
                    elif p and p.status == "Dev Complete" and key in (ord('l'), ord('L')):
                        result = dispatch(gs, "dev_launch", project_idx=p_idx)
                        status_msg = result.message
                        if result.ok:
                            projects_ui.view = "list"
                    elif key == curses.KEY_LEFT:
                        dev_ui.action_sel = (dev_ui.action_sel - 1) % 5
                    elif key == curses.KEY_RIGHT:
                        dev_ui.action_sel = (dev_ui.action_sel + 1) % 5
                    elif key in (10, curses.KEY_ENTER):
                        result = dispatch(gs, "dev_do_action",
                                          project_idx=p_idx,
                                          action_idx=dev_ui.action_sel)
                        status_msg = result.message
                    elif key in (ord('p'), ord('P')):
                        result = dispatch(gs, "dev_toggle_pause", project_idx=p_idx)
                        status_msg = result.message
                    elif key in (ord('q'), ord('Q')):
                        if p:
                            cur_idx = next((i for i, q in enumerate(QA_OPTIONS) if q["name"] == p.qa_level), 0)
                            new_idx = (cur_idx + 1) % len(QA_OPTIONS)
                            result = dispatch(gs, "dev_set_qa", project_idx=p_idx, qa_idx=new_idx)
                            status_msg = result.message
                    elif 49 <= key <= 53:   # keys 1-5 for direct action
                        action_idx = key - 49
                        result = dispatch(gs, "dev_do_action",
                                          project_idx=p_idx,
                                          action_idx=action_idx)
                        status_msg = result.message

                elif projects_ui.view == "list":
                    _visible = [p for p in gs.projects
                                if projects_ui.filter_status == "All"
                                or p.status == projects_ui.filter_status
                                or (projects_ui.filter_status == "In Dev" and p.status == "Dev Complete")]
                    if key == curses.KEY_UP:
                        projects_ui.selected = max(0, projects_ui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        projects_ui.selected = min(len(gs.projects)-1,
                                                   projects_ui.selected + 1)
                    elif key == curses.KEY_LEFT:
                        idx = _DEV_FILTERS.index(projects_ui.filter_status) if projects_ui.filter_status in _DEV_FILTERS else 0
                        projects_ui.filter_status = _DEV_FILTERS[(idx-1) % len(_DEV_FILTERS)]
                    elif key == curses.KEY_RIGHT:
                        idx = _DEV_FILTERS.index(projects_ui.filter_status) if projects_ui.filter_status in _DEV_FILTERS else 0
                        projects_ui.filter_status = _DEV_FILTERS[(idx+1) % len(_DEV_FILTERS)]
                    elif key in (ord('n'), ord('N')):
                        if gs.active_companies():
                            projects_ui.view = "new"
                            projects_ui.new_step = 0
                            projects_ui.message = ""
                            # Phase 7: offer only year-unlocked AI models in the wizard.
                            from .engine.systems.models_ai import available_model_names
                            names = available_model_names(gs)
                            mf = projects_ui.new_fields[2]
                            mf["options"] = names
                            mf["selected"] = (names.index(gs.active_model)
                                              if gs.active_model in names else 0)
                        else:
                            status_msg = "Create a company first before adding a project."
                    elif key in (ord('b'), ord('B')):
                        if gs.active_companies():
                            projects_ui.view = "templates"
                            projects_ui.tmpl_message = ""
                        else:
                            status_msg = "Create a company first."
                    elif key in (10, curses.KEY_ENTER):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("In Dev", "Dev Complete"):
                                p_idx = gs.projects.index(p)
                                projects_ui.dev_project_idx = p_idx
                                projects_ui.view = "dev"
                                dev_ui.action_sel = 0
                    # ── Phase 3 product lifecycle actions ──────────
                    elif key in (ord('u'), ord('U')):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("Launched", "Growing"):
                                p_idx = gs.projects.index(p)
                                result = dispatch(gs, "product_minor_update", project_idx=p_idx)
                                status_msg = ("✓ " if result.ok else "✗ ") + result.message
                    elif key in (ord('m'), ord('M')):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("Launched", "Growing"):
                                p_idx = gs.projects.index(p)
                                result = dispatch(gs, "product_major_revision", project_idx=p_idx)
                                status_msg = ("✓ " if result.ok else "✗ ") + result.message
                                if result.ok:
                                    projects_ui.dev_project_idx = p_idx
                                    projects_ui.view = "dev"
                                    dev_ui.action_sel = 0
                    elif key in (ord('v'), ord('V')):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("Launched", "Growing"):
                                p_idx = gs.projects.index(p)
                                result = dispatch(gs, "product_new_version", project_idx=p_idx)
                                status_msg = ("✓ " if result.ok else "✗ ") + result.message
                    elif key in (ord('s'), ord('S')):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("Launched", "Growing"):
                                p_idx = gs.projects.index(p)
                                result = dispatch(gs, "product_discontinue", project_idx=p_idx)
                                status_msg = ("✓ " if result.ok else "✗ ") + result.message
                    elif key in (ord('a'), ord('A')):
                        if _visible and 0 <= projects_ui.selected < len(_visible):
                            p = _visible[projects_ui.selected]
                            if p.status in ("Launched", "Growing"):
                                p_idx = gs.projects.index(p)
                                cur = getattr(p, "auto_update_interval", 0)
                                try:
                                    idx = AUTO_UPDATE_CYCLES.index(cur)
                                except ValueError:
                                    idx = 0
                                new_interval = AUTO_UPDATE_CYCLES[(idx + 1) % len(AUTO_UPDATE_CYCLES)]
                                result = dispatch(gs, "product_set_auto_update",
                                                  project_idx=p_idx, interval=new_interval)
                                status_msg = ("✓ " if result.ok else "✗ ") + result.message

                elif projects_ui.view == "templates":
                    active = gs.active_companies()
                    from .constants import TEMPLATE_TYPES
                    if key == 27:
                        projects_ui.view = "list"
                        projects_ui.tmpl_message = ""
                    elif key == curses.KEY_UP:
                        projects_ui.tmpl_type_idx = max(0, projects_ui.tmpl_type_idx - 1)
                    elif key == curses.KEY_DOWN:
                        projects_ui.tmpl_type_idx = min(len(TEMPLATE_TYPES) - 1,
                                                        projects_ui.tmpl_type_idx + 1)
                    elif key in (ord('c'), ord('C')):
                        if active:
                            projects_ui.tmpl_company_idx = (projects_ui.tmpl_company_idx + 1) % len(active)
                    elif key in (10, curses.KEY_ENTER):
                        if active:
                            ci = max(0, min(projects_ui.tmpl_company_idx, len(active) - 1))
                            ttype = TEMPLATE_TYPES[projects_ui.tmpl_type_idx]["name"]
                            result = dispatch(gs, "build_template",
                                              company_id=active[ci].id, template_type=ttype)
                            projects_ui.tmpl_message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message

                elif projects_ui.view == "new":
                    if key == 27:
                        if projects_ui.new_step > 0:
                            projects_ui.new_step -= 1
                        else:
                            projects_ui.view = "list"
                    else:
                        _handle_new_project_keys(key, projects_ui, gs, status_msg)
                        if projects_ui.view == "list":
                            status_msg = projects_ui.message

            elif tab == "Employees":
                eui = employees_ui

                # ── HIRE VIEW ─────────────────────────────────
                if eui.view == "hire":
                    if key == 27:
                        eui.view = "list"
                        eui.message = ""
                    elif key == curses.KEY_UP:
                        eui.cand_sel = max(0, eui.cand_sel - 1)
                    elif key == curses.KEY_DOWN:
                        eui.cand_sel = min(len(eui.candidates) - 1, eui.cand_sel + 1)
                    elif key in (ord('r'), ord('R')):
                        eui.candidates = generate_candidates(gs, eui.hire_company_id, 4)
                        eui.cand_sel = 0
                        eui.message = "Rerolled candidates."
                    elif key in (10, curses.KEY_ENTER):
                        if eui.candidates and 0 <= eui.cand_sel < len(eui.candidates):
                            cand = eui.candidates[eui.cand_sel]
                            result = dispatch(gs, "hire_employee",
                                              company_id=eui.hire_company_id, candidate=cand)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                            if result.ok:
                                eui.candidates.pop(eui.cand_sel)
                                eui.cand_sel = max(0, eui.cand_sel - 1)
                                if not eui.candidates:
                                    eui.view = "list"

                # ── ASSIGN VIEW ───────────────────────────────
                elif eui.view == "assign":
                    if key == 27:
                        eui.view = "list"
                    elif 0 <= eui.selected < len(gs.employees):
                        emp = gs.employees[eui.selected]
                        options = _assignable_projects(gs, emp)
                        if key == curses.KEY_UP:
                            eui.assign_sel = max(0, eui.assign_sel - 1)
                        elif key == curses.KEY_DOWN:
                            eui.assign_sel = min(len(options) - 1, eui.assign_sel + 1)
                        elif key in (10, curses.KEY_ENTER) and options:
                            pidx = options[eui.assign_sel][0]
                            result = dispatch(gs, "assign_employee",
                                              emp_index=eui.selected, project_idx=pidx)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                            if result.ok:
                                eui.view = "list"

                # ── TRAIN VIEW ────────────────────────────────
                elif eui.view == "train":
                    if key == 27:
                        eui.view = "list"
                        eui.message = ""
                    elif key == curses.KEY_UP:
                        eui.train_sel = max(0, eui.train_sel - 1)
                    elif key == curses.KEY_DOWN:
                        eui.train_sel = min(len(TRAINING_ACTIONS) - 1, eui.train_sel + 1)
                    elif key in (10, curses.KEY_ENTER):
                        result = dispatch(gs, "train_employee",
                                          emp_index=eui.selected, training_idx=eui.train_sel)
                        eui.message = ("✓ " if result.ok else "✗ ") + result.message
                        status_msg = result.message

                # ── LIST VIEW ─────────────────────────────────
                else:
                    if key == curses.KEY_UP:
                        eui.selected = max(0, eui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        eui.selected = min(len(gs.employees) - 1, eui.selected + 1)
                    elif key in (ord('h'), ord('H')):
                        if gs.active_companies():
                            cid = gs.active_companies()[0].id
                            eui.hire_company_id = cid
                            eui.candidates = generate_candidates(gs, cid, 4)
                            eui.cand_sel = 0
                            eui.view = "hire"
                            eui.message = ""
                        else:
                            status_msg = "Create a company first."
                    elif gs.employees and 0 <= eui.selected < len(gs.employees):
                        if key in (10, curses.KEY_ENTER):
                            eui.view = "assign"
                            eui.assign_sel = 0
                        elif key in (ord('u'), ord('U')):
                            result = dispatch(gs, "unassign_employee", emp_index=eui.selected)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('t'), ord('T')):
                            eui.view = "train"
                            eui.train_sel = 0
                            eui.message = ""
                        elif key in (ord('r'), ord('R')):
                            result = dispatch(gs, "rest_employee", emp_index=eui.selected)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('i'), ord('I')):
                            result = dispatch(gs, "inspirational_talk", emp_index=eui.selected)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('g'), ord('G')):
                            result = dispatch(gs, "distraction", emp_index=eui.selected)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                        elif key in (ord('f'), ord('F')):
                            result = dispatch(gs, "fire_employee", emp_index=eui.selected)
                            eui.message = ("✓ " if result.ok else "✗ ") + result.message
                            status_msg = result.message
                            eui.selected = max(0, eui.selected - 1)

            elif tab == "Founder":
                if key in (ord('b'), ord('B')):
                    status_msg = dispatch(gs, "founder_take_break").message
                elif key in (ord('r'), ord('R')):
                    # Team Recharge on the active company with the most worn-out team.
                    def _avg_sanity(cid):
                        team = [e for e in gs.employees_for_company(cid) if e.state == "active"]
                        return sum(e.sanity for e in team) / len(team) if team else 999
                    cos = gs.active_companies()
                    if cos:
                        target = min(cos, key=lambda c: _avg_sanity(c.id))
                        status_msg = dispatch(gs, "team_recharge", company_id=target.id).message
                    else:
                        status_msg = "No company to recharge."
                elif key in (ord('t'), ord('T')):
                    active_emps = [(i, e) for i, e in enumerate(gs.employees) if e.state == "active"]
                    if active_emps:
                        idx, _ = min(active_emps, key=lambda pair: pair[1].sanity)
                        status_msg = dispatch(gs, "inspirational_talk", emp_index=idx).message
                    else:
                        status_msg = "No employees to inspire."

            elif tab == "Market":
                from .engine.systems.models_ai import (
                    available_models, available_ides,
                )
                from .constants import SUBSCRIPTION_TIERS

                if market_ui.view == "model_lab":
                    _handle_model_lab_keys(key, model_lab_ui, gs, status_msg)
                    status_msg = model_lab_ui.message or status_msg
                    if key == 27:
                        market_ui.view = "market"
                        model_lab_ui.message = ""
                elif market_ui.view == "stocks":
                    if key in (27, ord('t'), ord('T')):
                        market_ui.view = "market"
                        market_ui.message = ""
                    elif key in (ord('p'), ord('P')):
                        market_ui.view = "ipo"
                        market_ui.message = ""
                        market_ui.ipo_price = ""
                        market_ui.ipo_shares = ""
                        market_ui.ipo_field = 0
                elif market_ui.view == "ipo":
                    from .ui.screens.market import _ipo_companies
                    companies = _ipo_companies(gs)
                    if key == 27:
                        market_ui.view = "stocks"
                        market_ui.message = ""
                    elif key == curses.KEY_UP:
                        market_ui.stock_company_sel = max(0, market_ui.stock_company_sel - 1)
                    elif key == curses.KEY_DOWN:
                        market_ui.stock_company_sel = min(
                            max(0, len(companies) - 1), market_ui.stock_company_sel + 1)
                    elif key == 9:   # Tab switches input field
                        market_ui.ipo_field = 1 - market_ui.ipo_field
                    elif companies:
                        c = companies[min(market_ui.stock_company_sel, len(companies) - 1)]
                        if key in (10, curses.KEY_ENTER):
                            if c.ipo_stage != "Pricing":
                                result = dispatch(gs, "prepare_ipo", company_id=c.id)
                                market_ui.message = result.message
                            else:
                                try:
                                    price = float(market_ui.ipo_price or "0")
                                    shares = int(market_ui.ipo_shares or "0")
                                except ValueError:
                                    price, shares = 0.0, 0
                                result = dispatch(gs, "price_ipo",
                                                  company_id=c.id, price=price, shares=shares)
                                market_ui.message = result.message
                                if result.ok:
                                    market_ui.view = "stocks"
                        elif key in (8, 127, curses.KEY_BACKSPACE):
                            if market_ui.ipo_field == 0:
                                market_ui.ipo_price = market_ui.ipo_price[:-1]
                            else:
                                market_ui.ipo_shares = market_ui.ipo_shares[:-1]
                        elif 48 <= key <= 57 or (key == ord('.') and market_ui.ipo_field == 0):
                            ch = chr(key)
                            if market_ui.ipo_field == 0:
                                market_ui.ipo_price += ch
                            else:
                                market_ui.ipo_shares += ch
                else:
                    models = available_models(gs)
                    if key == curses.KEY_UP:
                        market_ui.model_sel = max(0, market_ui.model_sel - 1)
                    elif key == curses.KEY_DOWN:
                        market_ui.model_sel = min(max(0, len(models) - 1),
                                                  market_ui.model_sel + 1)
                    elif key in (10, curses.KEY_ENTER):
                        if models and 0 <= market_ui.model_sel < len(models):
                            name = models[market_ui.model_sel]["name"]
                            result = dispatch(gs, "set_active_model", model_name=name)
                            status_msg = result.message
                    elif key in (ord('s'), ord('S')):
                        tiers = [t["name"] for t in SUBSCRIPTION_TIERS]
                        cur = tiers.index(gs.subscription_tier) if gs.subscription_tier in tiers else 0
                        nxt = tiers[(cur + 1) % len(tiers)]
                        status_msg = dispatch(gs, "set_subscription_tier", tier=nxt).message
                    elif key in (ord('i'), ord('I')):
                        ides = [i["name"] for i in available_ides(gs)]
                        if ides:
                            cur = ides.index(gs.active_ide) if gs.active_ide in ides else 0
                            nxt = ides[(cur + 1) % len(ides)]
                            status_msg = dispatch(gs, "set_active_ide", ide_name=nxt).message
                    elif key in (ord('l'), ord('L')):
                        market_ui.view = "model_lab"
                        model_lab_ui.message = ""
                    elif key in (ord('t'), ord('T')):
                        market_ui.view = "stocks"
                        market_ui.message = ""

            elif tab == "Research":
                if key == curses.KEY_UP:
                    research_ui.cat_sel = max(0, research_ui.cat_sel - 1)
                    research_ui.item_sel = 0
                elif key == curses.KEY_DOWN:
                    research_ui.cat_sel = min(len(RESEARCH_CATEGORIES)-1,
                                              research_ui.cat_sel + 1)
                    research_ui.item_sel = 0
                elif key == curses.KEY_LEFT:
                    research_ui.item_sel = max(0, research_ui.item_sel - 1)
                elif key == curses.KEY_RIGHT:
                    _, items = RESEARCH_CATEGORIES[research_ui.cat_sel]
                    research_ui.item_sel = min(len(items)-1, research_ui.item_sel + 1)
                elif key in (10, curses.KEY_ENTER):
                    _, items = RESEARCH_CATEGORIES[research_ui.cat_sel]
                    item = items[research_ui.item_sel]
                    if item not in gs.founder.unlocked_research:
                        gs.founder.unlocked_research.append(item)
                        gs.founder.total_tokens_used += 500
                        status_msg = f"Unlocked: {item}!"
                    else:
                        status_msg = f"{item} is already unlocked."

            elif tab == "News":
                if key == curses.KEY_UP:
                    news_ui.selected = max(0, news_ui.selected - 1)
                elif key == curses.KEY_DOWN:
                    news_ui.selected = min(len(gs.news_feed)-1, news_ui.selected + 1)

            elif tab == "Settings":
                if key == curses.KEY_UP:
                    settings_ui.focused = max(0, settings_ui.focused - 1)
                elif key == curses.KEY_DOWN:
                    settings_ui.focused = min(len(settings_ui.keys)-1,
                                              settings_ui.focused + 1)
                else:
                    _handle_settings_key(key, settings_ui, gs.settings)


# ─────────────────────── HELPERS ──────────────────────────────

def _default_founder(username: str) -> Founder:
    return Founder(
        username=username or "Founder",
        background_idx=0,
        reputation=20, burnout=0,
        skill_prototyping=40, skill_sales=20,
        skill_tech=35, skill_management=20,
        total_tokens_used=0,
    )

def _post_sign_in(state: SignInState, name: str, profile: Optional[dict]):
    state.success_name   = name
    state.success_date   = profile.get("updated_at", "—")[:10] if profile else "—"
    state.success_status = "Rookie Founder"
    state.step = "welcome"

def _do_enter_game(stdscr, gs):
    run_loading_screen(stdscr)

def _save_summary(gs: Optional[GameState]) -> dict:
    if gs is None:
        return {}
    return {
        "last_played": f"{MONTH_NAMES[gs.month-1]} {gs.year}",
        "cash":        gs.total_cash(),
        "projects":    len(gs.projects),
        "months_elapsed": gs.months_elapsed,
        "companies":   len(gs.active_companies()),
    }

def _now_str() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def _submit_game_run(cloud: CloudService, user_id: str, gs: GameState):
    run_data = {
        "months_survived":   gs.months_elapsed,
        "companies_created": len(gs.companies),
        "projects_launched": len([p for p in gs.projects if p.status in ("Launched", "Growing")]),
        "projects_failed":   len([p for p in gs.projects if p.status == "Failed"]),
        "total_revenue":     sum(p.lifetime_revenue for p in gs.projects),
        "total_users":       sum(p.users for p in gs.projects),
        "final_reputation":  gs.founder.reputation if gs.founder else 0,
        "final_burnout":     gs.founder.burnout if gs.founder else 0,
        "final_rank":        _rank(gs),
    }
    cloud.submit_game_run(user_id, run_data)

def _rank(gs: GameState) -> str:
    rev = sum(p.lifetime_revenue for p in gs.projects)
    if rev >= 100_000: return "Unicorn Chaser"
    if rev >= 50_000:  return "Series A Hopeful"
    if rev >= 10_000:  return "Ramen Profitable"
    if rev >= 1_000:   return "Side Project"
    return "Vibe Coder"

def _handle_settings_key(key, ui: SettingsUIState, settings: dict):
    k = ui.keys[ui.focused]
    if k in SETTINGS_OPTIONS:
        opts = SETTINGS_OPTIONS[k]
        cur = settings.get(k, opts[0])
        try:    idx = opts.index(cur)
        except: idx = 0
        if key == curses.KEY_LEFT:
            settings[k] = opts[(idx-1) % len(opts)]
        elif key == curses.KEY_RIGHT:
            settings[k] = opts[(idx+1) % len(opts)]
        elif key in (10, curses.KEY_ENTER):
            settings[k] = opts[(idx+1) % len(opts)]
    elif isinstance(settings.get(k), bool):
        if key in (10, curses.KEY_ENTER, curses.KEY_LEFT, curses.KEY_RIGHT):
            settings[k] = not settings[k]

def _handle_new_company_keys(key, ui: CompaniesUIState, gs: GameState):
    idx = ui.new_focused
    f = ui.new_fields[idx]
    if key == curses.KEY_UP:
        ui.new_focused = max(0, ui.new_focused - 1)
    elif key == curses.KEY_DOWN:
        ui.new_focused = min(len(ui.new_fields)-1, ui.new_focused + 1)
    elif f["type"] == "options":
        opts = f["options"]
        if key == curses.KEY_LEFT:
            f["selected"] = (f["selected"] - 1) % len(opts)
        elif key == curses.KEY_RIGHT:
            f["selected"] = (f["selected"] + 1) % len(opts)
    elif f["type"] == "text":
        if key in (curses.KEY_BACKSPACE, 127, 8):
            f["value"] = f["value"][:-1]
        elif 32 <= key < 127 and len(f["value"]) < f.get("max", 30):
            f["value"] += chr(key)
    if key in (10, curses.KEY_ENTER) and ui.new_focused == len(ui.new_fields) - 1:
        name    = ui.new_fields[0]["value"].strip() or "New Venture"
        legal   = COMPANY_LEGAL_STYLES[ui.new_fields[1]["selected"]]
        focus   = COMPANY_FOCUS_AREAS[ui.new_fields[2]["selected"]]
        funding = FUNDING_STYLES[ui.new_fields[3]["selected"]]
        risk    = RISK_APPETITES[ui.new_fields[4]["selected"]]
        try:    cash = int(ui.new_fields[5]["value"])
        except: cash = 2000
        cid = len(gs.companies)
        c = Company(
            id=cid, name=name, legal_style=legal, focus_area=focus,
            funding_style=funding, risk_appetite=risk,
            cash=cash, monthly_revenue=0, monthly_expenses=300,
            debt=0, reputation=10, valuation=cash,
            office_level=1, mood=80,
            founded_month=gs.month, founded_year=gs.year,
            loans=[],
        )
        gs.companies.append(c)
        gs.events.insert(0, ("🏢", f"New company '{name}' founded!", "good",
                              f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
        ui.message = f"'{name}' created successfully!"
        ui.view = "list"

def _handle_model_lab_keys(key, ui, gs: GameState, status_msg: str):
    from .ui.screens.model_lab import ModelLabUIState
    from .constants import AI_MODEL_AXES, AXIS_POINT_BUDGET

    if ui.view == "train":
        if ui.name_input:
            if key == 27 or key in (10, curses.KEY_ENTER):
                ui.name_input = False
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                ui.model_name = ui.model_name[:-1]
            elif 32 <= key < 127 and len(ui.model_name) < 30:
                ui.model_name += chr(key)
        else:
            if key == 27:
                ui.view = "list"
                ui.message = ""
            elif key == curses.KEY_UP:
                ui.axis_sel = max(0, ui.axis_sel - 1)
            elif key == curses.KEY_DOWN:
                ui.axis_sel = min(len(AI_MODEL_AXES) - 1, ui.axis_sel + 1)
            elif key == curses.KEY_LEFT:
                if ui.axis_points[ui.axis_sel] > 0:
                    ui.axis_points[ui.axis_sel] -= 1
            elif key == curses.KEY_RIGHT:
                total = sum(ui.axis_points)
                if total < AXIS_POINT_BUDGET:
                    ui.axis_points[ui.axis_sel] += 1
            elif key in (ord('n'), ord('N')):
                ui.name_input = True
            elif key in (10, curses.KEY_ENTER):
                total = sum(ui.axis_points)
                if total <= 0:
                    ui.message = "✗ Invest at least 1 point before training."
                elif not ui.model_name.strip():
                    ui.message = "✗ Enter a model name (press N)."
                else:
                    axes_dict = {AI_MODEL_AXES[i]["name"]: ui.axis_points[i]
                                 for i in range(len(AI_MODEL_AXES))}
                    invest_dict = {k: v for k, v in axes_dict.items() if v > 0}
                    if gs.active_companies():
                        cid = gs.active_companies()[0].id
                        result = dispatch(gs, "start_model_training",
                                          company_id=cid,
                                          name=ui.model_name.strip(),
                                          axes=axes_dict,
                                          invest_points=invest_dict)
                        ui.message = ("✓ " if result.ok else "✗ ") + result.message
                        if result.ok:
                            ui.view = "list"
                            ui.axis_points = [0] * 6
                            ui.model_name = ""
                    else:
                        ui.message = "✗ No active company."
    else:
        if key == curses.KEY_UP:
            ui.selected = max(0, ui.selected - 1)
        elif key == curses.KEY_DOWN:
            ui.selected = min(max(0, len(gs.player_models) - 1), ui.selected + 1)
        elif key in (ord('l'), ord('L')):
            if gs.player_models and 0 <= ui.selected < len(gs.player_models):
                m = gs.player_models[ui.selected]
                result = dispatch(gs, "toggle_model_licensing", model_id=m.model_id)
                ui.message = ("✓ " if result.ok else "✗ ") + result.message
        elif key in (ord('t'), ord('T')):
            ui.view = "train"
            ui.axis_points = [0] * 6
            ui.model_name = ""
            ui.message = ""
        elif key in (ord('r'), ord('R')):
            if gs.player_models and 0 <= ui.selected < len(gs.player_models):
                m = gs.player_models[ui.selected]
                result = dispatch(gs, "retire_player_model", model_id=m.model_id)
                ui.message = ("✓ " if result.ok else "✗ ") + result.message
                ui.selected = max(0, ui.selected - 1)


def _handle_new_project_keys(key, ui: ProjectsUIState, gs: GameState, status_msg: str):
    if ui.new_step == 0:
        active = gs.active_companies()
        if key == curses.KEY_UP:
            ui.new_company_idx = max(0, ui.new_company_idx - 1)
        elif key == curses.KEY_DOWN:
            ui.new_company_idx = min(len(active)-1, ui.new_company_idx + 1)
        elif key in (10, curses.KEY_ENTER):
            ui.new_step = 1
            # Phase 8: populate the (company-filtered) template selector.
            if len(ui.new_fields) > 8:
                from .engine.systems.templates import templates_for_company
                company = active[ui.new_company_idx] if active else None
                tmpls = templates_for_company(gs, company.id) if company else []
                tf = ui.new_fields[8]
                tf["options"] = ["None"] + [t.name for t in tmpls]
                tf["selected"] = 0

    elif ui.new_step == 1:
        idx = ui.new_focused
        f = ui.new_fields[idx]
        if key == curses.KEY_UP:
            ui.new_focused = max(0, ui.new_focused - 1)
        elif key == curses.KEY_DOWN:
            ui.new_focused = min(len(ui.new_fields)-1, ui.new_focused + 1)
        elif f.get("type") == "options":
            opts = f["options"]
            if key == curses.KEY_LEFT:
                f["selected"] = (f["selected"] - 1) % len(opts)
            elif key == curses.KEY_RIGHT:
                f["selected"] = (f["selected"] + 1) % len(opts)
        elif f.get("type") == "text":
            if key in (curses.KEY_BACKSPACE, 127, 8):
                f["value"] = f["value"][:-1]
            elif 32 <= key < 127 and len(f["value"]) < f.get("max", 30):
                f["value"] += chr(key)
        if key in (10, curses.KEY_ENTER) and ui.new_focused == len(ui.new_fields) - 1:
            ui.new_step = 2

    elif ui.new_step == 2:
        if key in (10, curses.KEY_ENTER):
            name     = ui.new_fields[0]["value"].strip() or "Unnamed Project"
            ptype    = PROJECT_TYPES[ui.new_fields[1]["selected"]]
            model_field = ui.new_fields[2]
            model_opts = model_field.get("options", [s["name"] for s in AI_SUBS])
            sub_name = model_opts[model_field["selected"]] if model_opts else gs.active_model
            stack    = TECH_STACKS[ui.new_fields[3]["selected"]]
            niche    = NICHES[ui.new_fields[4]["selected"]]
            scope    = ["Lean MVP", "Standard", "Feature-Rich", "Overengineered"][ui.new_fields[5]["selected"]]
            try:    budget = int(ui.new_fields[6]["value"])
            except: budget = 500
            try:    dev_weeks = int(ui.new_fields[7]["value"])
            except: dev_weeks = 4
            scope_data = FEATURE_SCOPES.get(scope, FEATURE_SCOPES["Standard"])
            active   = gs.active_companies()
            company  = active[ui.new_company_idx] if active else None
            cid      = company.id if company else 0

            # Phase 4: enforce focus restrictions
            if company:
                allowed, reason = can_build_project_type(company, ptype)
                if not allowed:
                    ui.message = f"✗ {reason}"
                    return

            # Phase 8: resolve the optional template selection to an id.
            template_id = -1
            if company and len(ui.new_fields) > 8:
                tf = ui.new_fields[8]
                tsel = tf.get("selected", 0)
                if tsel > 0:
                    from .engine.systems.templates import templates_for_company
                    tmpls = templates_for_company(gs, company.id)
                    if 0 <= tsel - 1 < len(tmpls):
                        template_id = gs.templates.index(tmpls[tsel - 1])

            p = Project(
                name=name, ptype=ptype, model=sub_name, stack=stack, niche=niche,
                company_id=cid, status="In Dev", progress=0,
                revenue=0, users=0, morale=80, tokens_used=0,
                scope=scope, budget=budget, dev_weeks=dev_weeks,
                dev_total_days=scope_data["base_days"],
                template_id=template_id,
            )
            gs.projects.append(p)
            p_idx = len(gs.projects) - 1
            # Kick off dev session immediately
            from .engine.systems.development import start_dev_session
            start_dev_session(gs, p_idx)
            gs.events.insert(0, ("💻", f"Project '{name}' started! ({scope}, {scope_data['base_days']} days)", "good",
                                  f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
            ui.message = f"'{name}' added! Open dev dashboard to manage it."
            ui.view = "list"
            ui.new_step = 0
