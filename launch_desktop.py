"""Desktop-only entry point used for the portable Windows build."""
import argparse
from aura.ui import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Aura desktop beta")
    parser.add_argument("--data", help="Alternate local SQLite file")
    args = parser.parse_args()
    run(args.data)
