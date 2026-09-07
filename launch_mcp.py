"""Portable stdio bridge. This executable never starts a desktop or listens on TCP."""
import argparse
import subprocess
import sys
from aura.mcp_server import run

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Project Aura local MCP bridge")
    parser.add_argument("--data",help="Alternate local SQLite profile")
    args=parser.parse_args()
    if getattr(sys, 'frozen', False):
        from aura.updater import cached
        target = cached(bridge=True)
        if target:
            try:
                sys.exit(subprocess.call([str(target)] + sys.argv[1:]))
            except OSError:
                pass
    run(args.data)
