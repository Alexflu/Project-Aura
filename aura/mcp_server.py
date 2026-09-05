"""Optional official MCP SDK adapter. Stdio only; no listening network socket."""
from typing import Literal
from functools import wraps
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from .core import Store, AuraError


def expected_errors(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AuraError as exc:
            raise ToolError(str(exc)) from None
    return wrapped


def create_server(store):
    server = MCPServer("Project Aura", version="0.1.0-beta.1", instructions=(
        "Aura is a local avatar companion. Read aura_status before proposing changes. "
        "Tools only queue proposals; the user approves them in Aura's desktop window. "
        "Poll aura_request_status to learn the outcome. Do not claim a pending action succeeded."))
    read = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
    write = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False, idempotentHint=False)

    @server.tool(annotations=read)
    @expected_errors
    def aura_status() -> dict:
        """Read appearance choices and connection status. Interests are returned only when the user enables sharing."""
        return store.public_state()

    @server.tool(annotations=write)
    @expected_errors
    def aura_propose_appearance(
        palette: Literal["violet", "ocean", "forest", "ember", "rose", "slate"] | None = None,
        hair: Literal["long", "bob", "pixie"] | None = None,
        outfit: Literal["explorer", "engineer", "casual", "tactical"] | None = None,
        accessory: Literal["none", "headphones", "goggles", "leaf"] | None = None,
        silhouette: Literal["balanced", "compact", "tall"] | None = None,
    ) -> dict:
        """Propose a bounded avatar change requested by the user or grounded in shared tastes. Queues local review; never applies automatically."""
        patch = {k: v for k, v in locals().items() if k in ("palette", "hair", "outfit", "accessory", "silhouette") and v is not None}
        return store.enqueue("appearance", patch)

    @server.tool(annotations=write)
    @expected_errors
    def aura_request_notepad() -> dict:
        """Ask Aura to open Windows Notepad after local user approval. Does not type, read files, or run commands."""
        return store.enqueue("launch", {"app": "notepad"})

    @server.tool(annotations=read)
    @expected_errors
    def aura_request_status(request_id: str) -> dict:
        """Check one queued request. Submitted means Windows accepted the launch, not that a task completed."""
        store.public_state()
        return store.request_status(request_id)

    return server


def run(path=None):
    create_server(Store(path)).run(transport="stdio")
