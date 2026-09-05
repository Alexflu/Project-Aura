# Architecture

## Implemented components

| Layer | Implementation | Responsibility |
| --- | --- | --- |
| Project Aura | Repository, documentation, MIT license | Umbrella project and community |
| AuraOS | `run_aura.py`, `launch_desktop.py` | Desktop/MCP entry points and lifecycle |
| AuraShell | `aura/shell.py`, `aura/ui.py` | Procedural avatar, animation, preview and floating window |
| AuraCore | `aura/core.py` | Validated state, explicit preferences, bounded adaptation, history, approval queue |
| AuraBridge | `aura/bridge.py`, `aura/mcp_server.py` | Approved Notepad launch and optional official MCP adapter |

The desktop uses Python/Tk without third-party packages. The optional SDK runs in a separate process; the portable desktop does not bundle it. SQLite transactions connect the two under one Windows user without an open network port. The Windows account is the local trust boundary, not a defense against programs already running as that user.

## Request lifecycle

1. A supported MCP client reads the permitted appearance context.
2. A tool validates an appearance patch or a fixed Notepad request.
3. AuraCore queues it only if the connection is enabled and Aura is not paused.
4. The desktop shows the request. Only a local review action can accept it; no MCP approval tool exists.
5. Appearance changes commit transactionally with undo. Launches are claimed once before invoking the bridge, and outcomes are recorded afterward.
6. The client polls the request identifier. Pending, applied, submitted, rejected, cancelled, expired and failed are distinct outcomes. A crash during a launch can leave `launching`, with explicitly unknown final outcome; it is not retried.

Pending requests expire after ten minutes. Queue size is bounded to ten pending and 100 total entries. Pausing or disabling the connection cancels pending work. Cosmetic animation is not proof of task success.

## Appearance and adaptation

Palette, hair, outfit, accessory and silhouette are enum-validated. No scripts, file paths, downloaded models or generated assets enter the renderer. The face stays consistent. Automatic adaptation changes only outfit, accessory and palette after the user records an activity; selected interests and manual counts determine the theme, while the favorite palette remains authoritative. Ties use selected-interest order. Counts saturate at 100. This deterministic baseline is not machine learning.

## Storage and extensions

Schema version 1 stores a JSON state document plus separate look history and request tables. Transactions avoid lost updates and double claims. Newer schemas and invalid state fail visibly. Up to 20 looks support undo. State is not encrypted. Reset clears application state, history and requests but cannot revoke information already sent to an MCP provider.

Future renderers should consume a versioned appearance document without gaining computer permissions. Integrations need separate schemas, explicit scopes, result receipts and tests. Credentials belong outside avatar state. The [beta plan](beta-plan.md) describes release gates for 3D, voice, providers, games, CAD and hardware. There is no auto-updater, plugin-code execution or general shell executor in this beta.
