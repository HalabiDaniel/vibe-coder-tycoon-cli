import os
import sys
import curses

from .app import main


# ─────────────────────── ANSI EXIT BANNER ─────────────────────
# These run *after* curses has torn the screen down, so we fall back to plain
# ANSI escape codes for a colourful, bordered send-off.

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ORANGE  = "\033[38;5;208m"
AMBER   = "\033[38;5;214m"
PINK    = "\033[38;5;205m"
GREEN   = "\033[38;5;82m"
CYAN    = "\033[38;5;51m"
PURPLE  = "\033[38;5;141m"
GREY    = "\033[38;5;245m"


def _supports_ansi() -> bool:
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        # On Windows, os.system("") flips on virtual-terminal processing so the
        # escape codes below render instead of printing as raw text.
        os.system("")
    return True


def _print_exit_banner():
    if not _supports_ansi():
        print("\n  Thanks for playing Vibe Coder Tycoon\n")
        print("  Build fast. Ship often. Don't burn out.\n")
        return

    title    = "THANKS FOR PLAYING"
    game     = "⚡ VIBE  CODER  TYCOON ⚡"
    tagline  = "Build fast.  Ship often.  Don't burn out."
    width    = 56

    def disp_width(text):
        # The ⚡ emoji (and friends) render two terminal cells wide even though
        # len() counts them as one, so measure real display width for centering.
        wd = 0
        for ch in text:
            o = ord(ch)
            if ch == "\uFE0F":
                continue
            if (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or
                    0x2B00 <= o <= 0x2BFF or 0x1F900 <= o <= 0x1F9FF):
                wd += 2
            else:
                wd += 1
        return wd

    def center(text, color, w=width):
        pad = w - disp_width(text)
        left = pad // 2
        right = pad - left
        return f"{ORANGE}║{RESET}" + " " * left + color + text + RESET + " " * right + f"{ORANGE}║{RESET}"

    top    = f"{ORANGE}╔{'═' * width}╗{RESET}"
    bottom = f"{ORANGE}╚{'═' * width}╝{RESET}"
    sep    = f"{ORANGE}║{RESET}{ORANGE}{'─' * width}{RESET}{ORANGE}║{RESET}"
    blank  = f"{ORANGE}║{RESET}{' ' * width}{ORANGE}║{RESET}"

    lines = [
        "",
        top,
        blank,
        center(title, BOLD + PINK),
        blank,
        center(game, BOLD + AMBER),
        blank,
        sep,
        blank,
        center(tagline, GREEN),
        blank,
        center("See you in the next sprint, founder.", DIM + GREY),
        blank,
        bottom,
        "",
    ]
    print("\n".join(lines))


def run():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    _print_exit_banner()


if __name__ == "__main__":
    run()
