"""AuraOS entry point. Desktop and optional MCP processes share transactional state."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Project Aura desktop beta")
    parser.add_argument("--data", help="Alternate SQLite data file (for testing or separate profiles)")
    parser.add_argument("--mcp", action="store_true", help="Run the optional stdio MCP server")
    parser.add_argument("--studio", action="store_true", help="Open Studio instead of starting in the tray")
    args = parser.parse_args()
    if args.mcp:
        from aura.mcp_server import run
        run(args.data)
    else:
        from aura.ui import run
        run(args.data, studio=args.studio)


if __name__ == "__main__":
    main()
