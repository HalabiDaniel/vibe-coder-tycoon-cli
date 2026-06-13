import curses
import random

from .ui.colors import init_colors, PAIR_TICKER, PAIR_PANEL, PAIR_OVERLAY
from .ui.helpers import (
    safe_addstr, fill_background, draw_topbar, draw_tabs, draw_statusbar,
)
from .ui.screens.title import draw_title_screen, draw_credits, TITLE_MENU
from .ui.screens.loading import run_loading_screen
from .ui.screens.auth import (
    SignInState, SignUpState, draw_sign_in, draw_sign_up,
)
from .ui.screens.settings import SettingsUIState, draw_settings_screen, SETTINGS_OPTIONS
from .ui.screens.dashboard import draw_dashboard
from .ui.screens.founder import draw_founder
from .ui.screens.companies import CompaniesUIState, draw_companies
from .ui.screens.projects import ProjectsUIState, draw_projects
from .ui.screens.employees import EmployeesUIState, draw_employees
from .ui.screens.market import draw_market
from .ui.screens.research import ResearchUIState, draw_research
from .ui.screens.news import NewsUIState, draw_news
from .ui.screens.help import draw_help
from .ui.screens.demo_end import draw_demo_end
from .models import Founder, Company, Project, Employee, GameState
from .persistence import (
    accounts_sign_in, accounts_create, save_game, load_game, default_settings,
)
from .engine import make_new_game, advance_month
from .constants import (
    TABS, BACKGROUNDS, AI_SUBS, DEMO_MONTH_LIMIT, MONTH_NAMES,
    EMPLOYEE_ROLES, EMPLOYEE_TRAITS, RESEARCH_CATEGORIES,
    COMPANY_LEGAL_STYLES, COMPANY_FOCUS_AREAS, FUNDING_STYLES, RISK_APPETITES,
    PROJECT_TYPES, TECH_STACKS, NICHES,
)


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

    # ── Loading screen (feels nice, ~3s) ──
    run_loading_screen(stdscr, duration=3.0)

    # ── State ──
    screen = "title"    # title | sign_in | sign_up | credits | settings_pre | game
    title_sel = 0
    blink = True
    blink_tick = 0
    ticker_idx = 0
    ticker_tick = 0
    status_msg = ""

    sign_in_state = SignInState()
    sign_up_state = SignUpState()
    settings_ui   = SettingsUIState()
    standalone_settings = default_settings()

    gs: Optional[GameState] = None
    current_user: Optional[str] = None

    active_tab = 0
    dash_company_sel = 0
    companies_ui = CompaniesUIState()
    projects_ui  = ProjectsUIState()
    employees_ui = EmployeesUIState()
    research_ui  = ResearchUIState()
    news_ui      = NewsUIState()

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

        # ── DRAW ──
        if screen == "title":
            draw_title_screen(stdscr, title_sel, blink)

        elif screen == "sign_in":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_in(stdscr, sign_in_state, blink)

        elif screen == "sign_up":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_sign_up(stdscr, sign_up_state, blink)

        elif screen == "credits":
            draw_credits(stdscr)

        elif screen == "settings_pre":
            fill_background(stdscr, PAIR_OVERLAY)
            draw_settings_screen(stdscr, None, settings_ui, standalone_settings)

        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            if gs.demo_ended:
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
                    draw_companies(stdscr, gs, companies_ui)
                elif tab == "Projects":
                    draw_projects(stdscr, gs, projects_ui)
                elif tab == "Employees":
                    draw_employees(stdscr, gs, employees_ui)
                elif tab == "Market":
                    draw_market(stdscr, gs)
                elif tab == "Research":
                    draw_research(stdscr, gs, research_ui)
                elif tab == "News":
                    draw_news(stdscr, gs, news_ui)
                elif tab == "Settings":
                    draw_settings_screen(stdscr, gs, settings_ui)
                elif tab == "Help":
                    draw_help(stdscr)

                # Ticker
                ticker_msg = TICKERS[ticker_idx]
                safe_addstr(stdscr, h-2, 2, f" ▶ {ticker_msg} ",
                            curses.color_pair(PAIR_TICKER))
                draw_statusbar(stdscr, status_msg)

        stdscr.refresh()

        # ── INPUT ──
        key = stdscr.getch()
        if key == -1:
            continue

        # ── TITLE SCREEN ──
        if screen == "title":
            if key == curses.KEY_UP:
                title_sel = (title_sel - 1) % len(TITLE_MENU)
            elif key == curses.KEY_DOWN:
                title_sel = (title_sel + 1) % len(TITLE_MENU)
            elif key in (10, curses.KEY_ENTER, ord(' ')):
                sel_key, sel_label = TITLE_MENU[title_sel]
                if sel_key == "Q":
                    break
                elif sel_key == "S":
                    sign_in_state = SignInState()
                    screen = "sign_in"
                elif sel_key == "C":
                    sign_up_state = SignUpState()
                    screen = "sign_up"
                elif sel_key == "O":
                    # Play offline — create a quick offline founder
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
                    run_loading_screen(stdscr)
                    screen = "game"
                    active_tab = 0
                    status_msg = "Playing offline. Progress will not be saved."
                elif sel_key == "T":
                    screen = "settings_pre"
                elif sel_key == "R":
                    screen = "credits"
            # Keyboard shortcuts on title
            elif key == ord('q') or key == ord('Q'):
                break
            elif key == ord('s') or key == ord('S'):
                sign_in_state = SignInState()
                screen = "sign_in"
            elif key == ord('c') or key == ord('C'):
                sign_up_state = SignUpState()
                screen = "sign_up"
            elif key == ord('o') or key == ord('O'):
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
                run_loading_screen(stdscr)
                screen = "game"
                status_msg = "Playing offline."
            elif key == ord('r') or key == ord('R'):
                screen = "credits"
            elif key == ord('t') or key == ord('T'):
                screen = "settings_pre"

        # ── SIGN IN ──
        elif screen == "sign_in":
            if sign_in_state.step == "welcome":
                if key in (10, curses.KEY_ENTER, 27):
                    # Load or create game for this user
                    loaded = load_game(current_user)
                    if loaded:
                        gs = loaded
                    else:
                        founder = Founder(
                            username=current_user,
                            background_idx=0,
                            reputation=20, burnout=0,
                            skill_prototyping=40, skill_sales=20,
                            skill_tech=35, skill_management=20,
                            total_tokens_used=0,
                        )
                        gs = make_new_game(founder, 0)
                    run_loading_screen(stdscr)
                    screen = "game"
                    status_msg = f"Welcome back, {current_user}!"
            else:
                if key == 27:  # Esc
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
                    uname = sign_in_state.fields[0]["value"].strip()
                    pw    = sign_in_state.fields[1]["value"]
                    if not uname or not pw:
                        sign_in_state.message = "Please fill in both fields."
                    else:
                        name, data = accounts_sign_in(uname, pw)
                        if name:
                            current_user = name
                            sign_in_state.success_name   = name
                            sign_in_state.success_date   = data.get("last_played", "—")
                            sign_in_state.success_status = data.get("founder_status", "Rookie Founder")
                            sign_in_state.step = "welcome"
                        else:
                            sign_in_state.message = "Invalid username or password."
                elif 32 <= key < 127:
                    f = sign_in_state.fields[sign_in_state.focused]
                    if len(f["value"]) < 80:
                        f["value"] += chr(key)

        # ── SIGN UP ──
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
                        ok, msg = accounts_create(uname, email, pw1)
                        if ok:
                            current_user = uname
                            sign_up_state.step = "founder"
                        else:
                            sign_up_state.message = msg
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
                    run_loading_screen(stdscr)
                    screen = "game"
                    status_msg = f"Welcome, {current_user}! Your journey begins."

        # ── CREDITS ──
        elif screen == "credits":
            if key in (27, 10, curses.KEY_ENTER, ord('q'), ord('Q')):
                screen = "title"

        # ── SETTINGS (pre-game) ──
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

        # ── IN GAME ──
        elif screen == "game":
            if gs is None:
                screen = "title"
                continue

            if gs.demo_ended:
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('r') or key == ord('R'):
                    screen = "title"
                    gs = None
                continue

            # Global quit
            if key == ord('q') or key == ord('Q'):
                if current_user:
                    save_game(gs, current_user)
                break

            # Tab navigation
            if key == ord('\t'):
                active_tab = (active_tab + 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"
            elif key == curses.KEY_BTAB:
                active_tab = (active_tab - 1) % len(TABS)
                status_msg = f"Switched to: {TABS[active_tab]}"

            tab = TABS[active_tab]

            # N: advance month (any tab)
            if key in (ord('n'), ord('N')):
                status_msg = advance_month(gs)
                if current_user:
                    save_game(gs, current_user)
                if gs.months_elapsed >= DEMO_MONTH_LIMIT:
                    gs.demo_ended = True
                continue

            # Tab-specific keys
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
                        companies_ui.view = "detail"
                elif companies_ui.view in ("detail", "new"):
                    if key == 27:
                        companies_ui.view = "list"
                    elif companies_ui.view == "new":
                        _handle_new_company_keys(key, companies_ui, gs)

            elif tab == "Projects":
                if projects_ui.view == "list":
                    if key == curses.KEY_UP:
                        projects_ui.selected = max(0, projects_ui.selected - 1)
                    elif key == curses.KEY_DOWN:
                        projects_ui.selected = min(len(gs.projects)-1,
                                                   projects_ui.selected + 1)
                    elif key == curses.KEY_LEFT:
                        filters = ["All", "In Dev", "Launched", "Growing", "Failed", "Archived", "Sold"]
                        idx = filters.index(projects_ui.filter_status)
                        projects_ui.filter_status = filters[(idx-1) % len(filters)]
                    elif key == curses.KEY_RIGHT:
                        filters = ["All", "In Dev", "Launched", "Growing", "Failed", "Archived", "Sold"]
                        idx = filters.index(projects_ui.filter_status)
                        projects_ui.filter_status = filters[(idx+1) % len(filters)]
                    elif key in (ord('n'), ord('N')):
                        if gs.active_companies():
                            projects_ui.view = "new"
                            projects_ui.new_step = 0
                            projects_ui.message = ""
                        else:
                            status_msg = "Create a company first before adding a project."
                elif projects_ui.view == "new":
                    if key == 27:
                        if projects_ui.new_step > 0:
                            projects_ui.new_step -= 1
                        else:
                            projects_ui.view = "list"
                    else:
                        _handle_new_project_keys(key, projects_ui, gs, status_msg)
                        # Check if we just confirmed and should go back
                        if projects_ui.view == "list":
                            status_msg = projects_ui.message

            elif tab == "Employees":
                if key == curses.KEY_UP:
                    employees_ui.selected = max(0, employees_ui.selected - 1)
                elif key == curses.KEY_DOWN:
                    employees_ui.selected = min(len(gs.employees)-1,
                                                employees_ui.selected + 1)
                elif key in (ord('h'), ord('H')):
                    # Hire a random employee
                    names = ["Ama Kwei", "Taro Naka", "Zara Malik", "Ivan Petrov",
                             "Lena Chen", "Rafi Hassan", "Suki Park", "Omar Ali"]
                    if gs.active_companies():
                        cid = gs.active_companies()[0].id
                        emp = Employee(
                            name=random.choice(names),
                            role=random.choice(EMPLOYEE_ROLES),
                            level=1,
                            salary=random.randint(1500, 3500),
                            mood=random.randint(70, 90),
                            skill=random.randint(40, 65),
                            hired_year=gs.year,
                            company_id=cid,
                            trait=random.choice(EMPLOYEE_TRAITS),
                        )
                        gs.employees.append(emp)
                        c = gs.company_by_id(cid)
                        if c:
                            c.monthly_expenses += emp.salary
                        status_msg = f"Hired {emp.name} as {emp.role}!"

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
        name = ui.new_fields[0]["value"].strip() or "New Venture"
        legal = COMPANY_LEGAL_STYLES[ui.new_fields[1]["selected"]]
        focus = COMPANY_FOCUS_AREAS[ui.new_fields[2]["selected"]]
        funding = FUNDING_STYLES[ui.new_fields[3]["selected"]]
        risk = RISK_APPETITES[ui.new_fields[4]["selected"]]
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

def _handle_new_project_keys(key, ui: ProjectsUIState, gs: GameState, status_msg: str):
    if ui.new_step == 0:
        active = gs.active_companies()
        if key == curses.KEY_UP:
            ui.new_company_idx = max(0, ui.new_company_idx - 1)
        elif key == curses.KEY_DOWN:
            ui.new_company_idx = min(len(active)-1, ui.new_company_idx + 1)
        elif key in (10, curses.KEY_ENTER):
            ui.new_step = 1

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
            sub_name = [s["name"] for s in AI_SUBS][ui.new_fields[2]["selected"]]
            stack    = TECH_STACKS[ui.new_fields[3]["selected"]]
            niche    = NICHES[ui.new_fields[4]["selected"]]
            active   = gs.active_companies()
            cid      = active[ui.new_company_idx].id if active else 0
            p = Project(
                name=name, ptype=ptype, model=sub_name, stack=stack, niche=niche,
                company_id=cid, status="In Dev", progress=0,
                revenue=0, users=0, morale=80, tokens_used=0,
            )
            gs.projects.append(p)
            gs.events.insert(0, ("🚀", f"Project '{name}' started!", "good",
                                  f"{MONTH_NAMES[gs.month-1]} {gs.year}"))
            ui.message = f"'{name}' added to your queue!"
            ui.view = "list"
            ui.new_step = 0

