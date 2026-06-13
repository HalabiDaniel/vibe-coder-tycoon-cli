import curses


# ─────────────────────── COLOUR PALETTE ───────────────────────

PAIR_TOPBAR       = 1
PAIR_TAB_ACTIVE   = 2
PAIR_TAB_INACTIVE = 3
PAIR_PANEL        = 4
PAIR_HIGHLIGHT    = 5
PAIR_ACCENT       = 6
PAIR_DANGER       = 7
PAIR_WARN         = 8
PAIR_TITLE        = 9
PAIR_BORDER       = 10
PAIR_MUTED        = 11
PAIR_INPUT_FOCUS  = 12
PAIR_INPUT_IDLE   = 13
PAIR_BUTTON       = 14
PAIR_BUTTON_FOCUS = 15
PAIR_BADGE_BLUE   = 16
PAIR_BADGE_GREEN  = 17
PAIR_BADGE_AMBER  = 18
PAIR_BADGE_RED    = 19
PAIR_TICKER       = 20
PAIR_LOGO         = 21
PAIR_OVERLAY      = 22
PAIR_TITLE_SCREEN = 23
PAIR_MENU_SEL     = 24
PAIR_MENU_IDLE    = 25
PAIR_FOUNDER      = 26

def init_colors():
    curses.start_color()
    curses.use_default_colors()

    def p(pair, fg, bg): curses.init_pair(pair, fg, bg)

    BG       = 17
    BG2      = 18
    BG_TAB   = 234
    FG       = 252
    FG_DIM   = 245
    GREEN    = 82
    RED      = 196
    AMBER    = 214
    CYAN     = 51
    BLUE     = 33
    PURPLE   = 141
    PINK     = 205
    LOGO_FG  = 214
    NAVY     = 17
    NEARBLK  = 232

    p(PAIR_TOPBAR,       FG,      NAVY)
    p(PAIR_TAB_ACTIVE,   NEARBLK, GREEN)
    p(PAIR_TAB_INACTIVE, FG_DIM,  BG_TAB)
    p(PAIR_PANEL,        FG,      NEARBLK)
    p(PAIR_HIGHLIGHT,    NEARBLK, CYAN)
    p(PAIR_ACCENT,       GREEN,   NEARBLK)
    p(PAIR_DANGER,       RED,     NEARBLK)
    p(PAIR_WARN,         AMBER,   NEARBLK)
    p(PAIR_TITLE,        CYAN,    NEARBLK)
    p(PAIR_BORDER,       BLUE,    NEARBLK)
    p(PAIR_MUTED,        FG_DIM,  NEARBLK)
    p(PAIR_INPUT_FOCUS,  NEARBLK, CYAN)
    p(PAIR_INPUT_IDLE,   FG,      235)
    p(PAIR_BUTTON,       NEARBLK, BLUE)
    p(PAIR_BUTTON_FOCUS, NEARBLK, GREEN)
    p(PAIR_BADGE_BLUE,   NEARBLK, BLUE)
    p(PAIR_BADGE_GREEN,  NEARBLK, GREEN)
    p(PAIR_BADGE_AMBER,  NEARBLK, AMBER)
    p(PAIR_BADGE_RED,    NEARBLK, RED)
    p(PAIR_TICKER,       AMBER,   NEARBLK)
    p(PAIR_LOGO,         LOGO_FG, NAVY)
    p(PAIR_OVERLAY,      FG,      NAVY)
    p(PAIR_TITLE_SCREEN, CYAN,    NAVY)
    p(PAIR_MENU_SEL,     NEARBLK, AMBER)
    p(PAIR_MENU_IDLE,    FG_DIM,  NAVY)
    p(PAIR_FOUNDER,      PURPLE,  NEARBLK)
    p(PAIR_MUTED,        FG_DIM,  NEARBLK)
