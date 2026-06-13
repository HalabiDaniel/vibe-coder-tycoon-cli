import curses

from .app import main


def run():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n  Thanks for playing Vibe Coder Tycoon\n")
    print("  Build fast. Ship often. Don't burn out.\n")


if __name__ == "__main__":
    run()
