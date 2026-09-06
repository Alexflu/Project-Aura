"""Desktop-only entry point used for the portable Windows build."""
import argparse
from aura.ui import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Aura desktop beta")
    parser.add_argument("--data", help="Alternate local SQLite file")
    parser.add_argument("--studio", action="store_true", help="Open Studio instead of starting in the tray")
    args = parser.parse_args()
    run(args.data, studio=args.studio)
