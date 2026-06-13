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
# Dedicated warm theme for the loading + main-menu (title) screens so they
# can move away from the blue palette without touching the in-game screens.
PAIR_MENU_OVERLAY = 27
PAIR_MENU_LOGO    = 28
PAIR_MENU_TITLE   = 29
PAIR_MENU_BORDER  = 30
PAIR_MENU_DIM     = 31
PAIR_MENU_ACCENT  = 32
PAIR_MENU_BUTTON  = 33
PAIR_MENU_INPUT   = 34

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
    ORANGE   = 208
    WARM_BG  = 235   # warm charcoal backdrop, shared by menu + in-game screens
    WARM_BAR = 234   # slightly darker warm band for the topbar / tabs / status

    # In-game screens now share the warm theme used by the menu, loading, and
    # auth screens: charcoal backdrop, orange borders, pink titles, amber
    # highlights, green accents. Badges keep their semantic colours.
    p(PAIR_TOPBAR,       FG,      WARM_BAR)
    p(PAIR_TAB_ACTIVE,   NEARBLK, AMBER)
    p(PAIR_TAB_INACTIVE, FG_DIM,  WARM_BAR)
    p(PAIR_PANEL,        FG,      WARM_BG)
    p(PAIR_HIGHLIGHT,    NEARBLK, AMBER)
    p(PAIR_ACCENT,       GREEN,   WARM_BG)
    p(PAIR_DANGER,       RED,     WARM_BG)
    p(PAIR_WARN,         AMBER,   WARM_BG)
    p(PAIR_TITLE,        PINK,    WARM_BG)
    p(PAIR_BORDER,       ORANGE,  WARM_BG)
    p(PAIR_MUTED,        FG_DIM,  WARM_BG)
    p(PAIR_INPUT_FOCUS,  NEARBLK, AMBER)
    p(PAIR_INPUT_IDLE,   FG,      WARM_BG)
    p(PAIR_BUTTON,       NEARBLK, ORANGE)
    p(PAIR_BUTTON_FOCUS, NEARBLK, GREEN)
    p(PAIR_BADGE_BLUE,   NEARBLK, BLUE)
    p(PAIR_BADGE_GREEN,  NEARBLK, GREEN)
    p(PAIR_BADGE_AMBER,  NEARBLK, AMBER)
    p(PAIR_BADGE_RED,    NEARBLK, RED)
    p(PAIR_TICKER,       AMBER,   WARM_BG)
    p(PAIR_LOGO,         LOGO_FG, WARM_BAR)
    p(PAIR_OVERLAY,      FG,      WARM_BG)
    p(PAIR_TITLE_SCREEN, PINK,    WARM_BG)
    p(PAIR_MENU_SEL,     NEARBLK, AMBER)
    p(PAIR_MENU_IDLE,    FG_DIM,  WARM_BG)
    p(PAIR_FOUNDER,      PURPLE,  WARM_BG)

    # Warm, non-blue theme for the loading + main-menu screens.
    p(PAIR_MENU_OVERLAY, FG,      WARM_BG)
    p(PAIR_MENU_LOGO,    LOGO_FG, WARM_BG)
    p(PAIR_MENU_TITLE,   PINK,    WARM_BG)
    p(PAIR_MENU_BORDER,  ORANGE,  WARM_BG)
    p(PAIR_MENU_DIM,     FG_DIM,  WARM_BG)
    p(PAIR_MENU_ACCENT,  GREEN,   WARM_BG)
    p(PAIR_MENU_BUTTON,  NEARBLK, ORANGE)
    p(PAIR_MENU_INPUT,   NEARBLK, AMBER)
