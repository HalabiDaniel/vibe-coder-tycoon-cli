import curses

from ..colors import *
from ..helpers import *
from ...constants import BACKGROUNDS, AI_SUBS, TOKEN_MILESTONES, FOUNDER_CONDITIONS


# ─────────────────────── FOUNDER TAB ──────────────────────────

def draw_founder(win, gs):
    h, w = win.getmaxyx()
    f = gs.founder
    bg = BACKGROUNDS[f.background_idx]
    y = 3
    mid = w // 2

    # ── Left column: identity + resources ──────────────────────
    safe_addstr(win, y, 2, " FOUNDER PROFILE ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    # Personal finance row
    safe_addstr(win, y, 4, f"{'Personal Cash':<22}",  curses.color_pair(PAIR_MUTED))
    safe_addstr(win, y, 26, f"${f.personal_cash:,.0f}",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    y += 1

    rows = [
        ("Name",        f.username),
        ("Background",  bg["name"]),
        ("AI Sub",      AI_SUBS[gs.active_ai_sub_idx]["name"]),
        ("Companies",   str(len(gs.active_companies()))),
        ("Projects",    str(len(gs.projects))),
    ]
    for label, val in rows:
        safe_addstr(win, y, 4, f"{label:<22}", curses.color_pair(PAIR_MUTED))
        safe_addstr(win, y, 26, val, curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        y += 1

    y += 1
    safe_addstr(win, y, 4, "RESOURCES", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1

    lw = mid - 4
    bar_w = lw - 22

    # Reputation bar
    safe_addstr(win, y, 4, f"  {'Reputation':<14}", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y, 20, bar_w, f.reputation, PAIR_ACCENT, PAIR_MUTED)
    safe_addstr(win, y, 20 + bar_w + 1, f"{f.reputation:3d}/100",
                curses.color_pair(PAIR_ACCENT))
    y += 1

    # Vibe bar (calm→chaotic colour)
    vibe_pair = PAIR_WARN if f.vibe >= 70 else PAIR_ACCENT if f.vibe >= 30 else PAIR_MUTED
    safe_addstr(win, y, 4, f"  {'Vibe':<14}", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y, 20, bar_w, f.vibe, vibe_pair, PAIR_MUTED)
    vibe_label = "chaotic" if f.vibe >= 70 else "flowing" if f.vibe >= 30 else "calm"
    safe_addstr(win, y, 20 + bar_w + 1, f"{f.vibe:3.0f} {vibe_label}",
                curses.color_pair(vibe_pair))
    y += 1

    # Sanity bar
    sanity_pair = PAIR_DANGER if f.sanity < 30 else PAIR_WARN if f.sanity < 60 else PAIR_ACCENT
    safe_addstr(win, y, 4, f"  {'Sanity':<14}", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y, 20, bar_w, f.sanity, sanity_pair, PAIR_MUTED)
    safe_addstr(win, y, 20 + bar_w + 1, f"{f.sanity:3d}%",
                curses.color_pair(sanity_pair))
    y += 1

    # Burnout bar
    burn_pair = PAIR_DANGER if f.burnout > 70 else PAIR_WARN if f.burnout > 40 else PAIR_ACCENT
    safe_addstr(win, y, 4, f"  {'Burnout':<14}", curses.color_pair(PAIR_MUTED))
    progress_bar(win, y, 20, bar_w, f.burnout, burn_pair, PAIR_MUTED)
    safe_addstr(win, y, 20 + bar_w + 1, f"{f.burnout:3d}%",
                curses.color_pair(burn_pair))
    y += 2

    # ── Mental health: conditions + wired actions ──────────────
    safe_addstr(win, y, 4, "MENTAL HEALTH", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    if f.conditions:
        for cond in f.conditions:
            info = FOUNDER_CONDITIONS.get(cond, {})
            safe_addstr(win, y, 4, f"  ⚠ {cond}", curses.color_pair(PAIR_DANGER) | curses.A_BOLD)
            safe_addstr(win, y, 4 + len(cond) + 5, info.get("effect", "")[:mid - 30],
                        curses.color_pair(PAIR_MUTED))
            y += 1
    else:
        safe_addstr(win, y, 4, "  No active conditions. Keep it that way.",
                    curses.color_pair(PAIR_MUTED))
        y += 1
    safe_addstr(win, y, 4,
                "[ B: Take a Break ]  [ R: Team Recharge ]  [ T: Inspire Team ]",
                curses.color_pair(PAIR_BUTTON) | curses.A_BOLD)
    y += 2

    # Skills
    safe_addstr(win, y, 4, "SKILLS", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    skills = [
        ("Prototyping", f.skill_prototyping),
        ("Sales",       f.skill_sales),
        ("Tech Depth",  f.skill_tech),
        ("Management",  f.skill_management),
    ]
    for name, val in skills:
        safe_addstr(win, y, 4, f"  {name:<14}", curses.color_pair(PAIR_MUTED))
        progress_bar(win, y, 20, bar_w, val, PAIR_ACCENT, PAIR_MUTED)
        safe_addstr(win, y, 20 + bar_w + 1, f"{val:3d}",
                    curses.color_pair(PAIR_MUTED))
        y += 1

    y += 1
    safe_addstr(win, y, 4, f"Background: {bg['name']}",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 1
    safe_addstr(win, y, 6, bg["desc"][:mid - 8], curses.color_pair(PAIR_MUTED))
    y += 1
    bonuses = bg["bonuses"]
    bstr = (f"  Proto {bonuses['prototyping']:+d}  Sales {bonuses['sales']:+d}  "
            f"Tech {bonuses['tech_skill']:+d}  Burnout Resist {bonuses['burnout_resist']:+d}")
    safe_addstr(win, y, 6, bstr[:mid - 8], curses.color_pair(PAIR_ACCENT))

    # ── Right column: token milestones + achievements + research ──
    rx = mid + 2
    rw = w - mid - 4
    ry = 3

    safe_addstr(win, ry, rx, " TOKEN MILESTONES ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    tokens = f.total_tokens_used
    safe_addstr(win, ry, rx + 2, f"Lifetime tokens used: {tokens:,}K",
                curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
    ry += 1
    for threshold, title in TOKEN_MILESTONES:
        reached = tokens >= threshold
        marker = "✓" if reached else "·"
        col = PAIR_ACCENT if reached else PAIR_MUTED
        label = f"  {marker} {title:<22} ({threshold:,}K)"
        safe_addstr(win, ry, rx + 2, label[:rw - 4], curses.color_pair(col))
        ry += 1
        if ry >= h - 14:
            break

    ry += 1
    safe_addstr(win, ry, rx, " ACHIEVEMENTS ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.achievements:
        for ach in f.achievements[:6]:
            safe_addstr(win, ry, rx + 2, f"🏆 {ach}"[:rw - 4],
                        curses.color_pair(PAIR_WARN))
            ry += 1
    else:
        safe_addstr(win, ry, rx + 2, "No achievements yet. Go ship something.",
                    curses.color_pair(PAIR_MUTED))
        ry += 1

    ry += 1
    safe_addstr(win, ry, rx, " UNLOCKED RESEARCH ", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    ry += 1
    if f.unlocked_research:
        for res in f.unlocked_research[:6]:
            safe_addstr(win, ry, rx + 2, f"✓ {res}"[:rw - 4],
                        curses.color_pair(PAIR_ACCENT))
            ry += 1
    else:
        safe_addstr(win, ry, rx + 2, "Nothing unlocked yet. Visit Research.",
                    curses.color_pair(PAIR_MUTED))
