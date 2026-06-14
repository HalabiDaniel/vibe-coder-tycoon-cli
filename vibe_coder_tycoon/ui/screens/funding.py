"""
Phase 11 — Funding Screen

Two views:
  "list"       — active loans, funding deals, pending investor offers
  "apply_loan" — pick a lender, enter amount, confirm
"""

import curses
from dataclasses import dataclass

from ..colors import *
from ..helpers import *
from ...constants import LENDERS, MONTH_NAMES
from ...models import GameState, Loan
from ...engine.systems.investors import get_eligible_lenders, amortized_payment


# ─────────────────────── STATE ─────────────────────────────────


@dataclass
class FundingUIState:
    view: str = "list"          # "list" | "apply_loan"
    offer_sel: int = 0          # selected pending offer index
    lender_sel: int = 0         # selected lender index in apply_loan
    loan_amount: str = ""       # text input for loan amount
    message: str = ""


# ─────────────────────── MAIN DRAW ────────────────────────────


def draw_funding(win, gs: GameState, ui: "FundingUIState", company_id: int):
    if ui.view == "apply_loan":
        _draw_apply_loan(win, gs, ui, company_id)
    else:
        _draw_list_view(win, gs, ui, company_id)


# ─────────────────────── LIST VIEW ────────────────────────────


def _draw_list_view(win, gs: GameState, ui: FundingUIState, company_id: int):
    h, w = win.getmaxyx()
    c = gs.company_by_id(company_id)
    if c is None:
        safe_addstr(win, 4, 4, "Company not found.", curses.color_pair(PAIR_DANGER))
        return

    y = 3
    safe_addstr(win, y, 2, f" FUNDING: {c.name} ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    y += 2

    # ── Active Loans ──────────────────────────────────────────
    company_loans = [l for l in c.loans if isinstance(l, Loan)]
    safe_addstr(win, y, 2, f"ACTIVE LOANS  ({len(company_loans)})",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
    hline(win, y, 2, w - 4, PAIR_BORDER); y += 1

    if not company_loans:
        safe_addstr(win, y, 4, "No active loans.", curses.color_pair(PAIR_MUTED)); y += 1
    else:
        header = f"  {'LENDER':<16} {'PRINCIPAL':>10} {'BALANCE':>10} {'RATE':>6} {'PMT/MO':>8} {'TERM':>5}"
        safe_addstr(win, y, 2, header, curses.color_pair(PAIR_MUTED) | curses.A_BOLD); y += 1
        for loan in company_loans:
            if y >= h - 14:
                break
            bal_p = PAIR_DANGER if loan.balance > loan.principal * 0.5 else PAIR_ACCENT
            safe_addstr(win, y, 2,
                        f"  {loan.lender:<16} ${loan.principal:>9,} ${loan.balance:>9,} "
                        f"{loan.rate:.0%}   ${loan.monthly_payment:>7,} {loan.term_months:>4}mo",
                        curses.color_pair(PAIR_PANEL))
            y += 1

    y += 1

    # ── Funding Deals ─────────────────────────────────────────
    company_deals = [d for d in gs.funding_deals if d.company_id == company_id]
    safe_addstr(win, y, 2, f"FUNDING DEALS  ({len(company_deals)})",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
    hline(win, y, 2, w - 4, PAIR_BORDER); y += 1

    if not company_deals:
        safe_addstr(win, y, 4, "No funding deals.", curses.color_pair(PAIR_MUTED)); y += 1
    else:
        for deal in company_deals:
            if y >= h - 10:
                break
            sp = {"active": PAIR_BADGE_AMBER, "met": PAIR_BADGE_GREEN,
                  "failed": PAIR_BADGE_RED}.get(deal.status, PAIR_MUTED)
            deadline_in = deal.deadline_month - gs.months_elapsed
            safe_addstr(win, y, 4,
                        f"{deal.round_type} — {deal.investor_name}  "
                        f"${deal.amount:,}  {deal.equity_pct:.0%} equity",
                        curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
            safe_addstr(win, y, 4 + 55, f"[{deal.status.upper()}]",
                        curses.color_pair(sp) | curses.A_BOLD)
            y += 1
            safe_addstr(win, y, 6,
                        f"Requirement: {deal.requirement_desc}  "
                        f"Deadline: {max(0, deadline_in)} months",
                        curses.color_pair(PAIR_MUTED))
            y += 1

    y += 1

    # ── Pending Investor Offers ───────────────────────────────
    safe_addstr(win, y, 2, f"PENDING OFFERS  ({len(gs.pending_offers)})",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
    hline(win, y, 2, w - 4, PAIR_BORDER); y += 1

    if not gs.pending_offers:
        safe_addstr(win, y, 4, "No pending offers. Build reputation to attract investors.",
                    curses.color_pair(PAIR_MUTED)); y += 1
    else:
        ui.offer_sel = max(0, min(ui.offer_sel, len(gs.pending_offers) - 1))
        for i, offer in enumerate(gs.pending_offers):
            if y >= h - 7:
                break
            is_sel = (i == ui.offer_sel)
            rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
            neg_tag = " [NEGOTIATED]" if offer.get("negotiated") else ""
            deadline_in = offer["deadline_month"] - gs.months_elapsed
            safe_addstr(win, y, 2, " " * (w - 4), curses.color_pair(rp))
            safe_addstr(win, y, 3,
                        f"{'▶ ' if is_sel else '  '}{offer['round_type']} — {offer['investor_name']}"
                        f"{neg_tag}",
                        curses.color_pair(rp))
            y += 1
            safe_addstr(win, y, 6,
                        f"${offer['amount']:,}  {offer['equity_pct']:.0%} equity  |  "
                        f"{offer['requirement_desc']}  Deadline: {max(0, deadline_in)}mo",
                        curses.color_pair(PAIR_MUTED if not is_sel else PAIR_ACCENT))
            y += 1

    safe_addstr(win, h - 5, 2,
                "↑↓:select offer  A:accept  X:reject  N:negotiate  L:apply for loan  Esc:back",
                curses.color_pair(PAIR_MUTED))
    loan_def = getattr(gs, "loan_default_count", 0)
    if loan_def > 0:
        safe_addstr(win, h - 4, 2,
                    f"Loan defaults: {loan_def}  (rates penalised +{loan_def * 3}%)",
                    curses.color_pair(PAIR_DANGER))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)


# ─────────────────────── APPLY LOAN VIEW ──────────────────────


def _draw_apply_loan(win, gs: GameState, ui: FundingUIState, company_id: int):
    h, w = win.getmaxyx()
    eligible = get_eligible_lenders(gs, company_id)
    y = 3
    safe_addstr(win, y, 2, " APPLY FOR LOAN ",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 2

    if not eligible:
        safe_addstr(win, y, 4,
                    "No eligible lenders at your current reputation.",
                    curses.color_pair(PAIR_DANGER))
        safe_addstr(win, h - 3, 2, "Esc: back", curses.color_pair(PAIR_MUTED))
        return

    safe_addstr(win, y, 4, "SELECT LENDER  (↑↓)",
                curses.color_pair(PAIR_TITLE) | curses.A_BOLD); y += 1
    hline(win, y, 4, w // 2, PAIR_BORDER); y += 1

    ui.lender_sel = max(0, min(ui.lender_sel, len(eligible) - 1))
    for i, lender in enumerate(eligible):
        is_sel = (i == ui.lender_sel)
        rp = PAIR_HIGHLIGHT if is_sel else PAIR_PANEL
        prefix = "▶ " if is_sel else "  "
        safe_addstr(win, y, 4, " " * (w // 2 - 5), curses.color_pair(rp))
        safe_addstr(win, y, 4,
                    f"{prefix}{lender['name']:<16}  {lender['rate']:.0%}/yr  "
                    f"max ${lender['max_amount']:,}  {lender['term_months']}mo",
                    curses.color_pair(rp))
        y += 1

    y += 1
    selected_lender = eligible[ui.lender_sel]
    safe_addstr(win, y, 4, f"Desc: {selected_lender['desc']}",
                curses.color_pair(PAIR_MUTED)); y += 2

    safe_addstr(win, y, 4, f"Amount ($): {ui.loan_amount}█",
                curses.color_pair(PAIR_INPUT_FOCUS) | curses.A_BOLD); y += 2

    # Payment preview
    try:
        amt = int(ui.loan_amount or "0")
    except ValueError:
        amt = 0
    if amt > 0:
        monthly = amortized_payment(amt, selected_lender["rate"], selected_lender["term_months"])
        safe_addstr(win, y, 4,
                    f"Monthly payment: ${monthly:,}/mo  "
                    f"Total: ~${monthly * selected_lender['term_months']:,}",
                    curses.color_pair(PAIR_ACCENT) | curses.A_BOLD)
        y += 1
        if amt > selected_lender["max_amount"]:
            safe_addstr(win, y, 4,
                        f"Exceeds max of ${selected_lender['max_amount']:,}!",
                        curses.color_pair(PAIR_DANGER))

    safe_addstr(win, h - 4, 2,
                "↑↓:lender  Type amount  Enter:confirm  Esc:back",
                curses.color_pair(PAIR_MUTED))
    if ui.message:
        mp = PAIR_ACCENT if "✓" in ui.message else PAIR_DANGER
        safe_addstr(win, h - 3, 2, ui.message[:w - 4], curses.color_pair(mp) | curses.A_BOLD)
