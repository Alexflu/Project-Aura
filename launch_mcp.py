"""Portable stdio bridge. This executable never starts a desktop or listens on TCP."""
import argparse
from aura.mcp_server import run

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Project Aura local MCP bridge")
    parser.add_argument("--data",help="Alternate local SQLite profile")
    args=parser.parse_args()
    run(args.data)
