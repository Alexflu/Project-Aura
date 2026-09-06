# Local MCP setup — 0.6

Aura's Windows ZIP now includes `bridge/AuraMCP.exe`. Leave its adjacent `_internal` folder intact. In Aura, open Connection, enable requests, save, then use **Copy MCP setup**. This copies the command and arguments for the running build and its actual profile.

For a client with separate form fields, select **STDIO**, put the full path to `bridge/AuraMCP.exe` in Command, and add `--data` and the copied database path as separate arguments. No environment variables are required. Do not add `--mcp` to AuraMCP.exe; it is already the dedicated bridge. Run ProjectAura.exe alongside the client so local review can appear.

The copied JSON is a common MCP-client configuration format; a client using TOML needs the same values in its own format. Codex's documented configuration uses `[mcp_servers.<name>]` with command and arguments. Consult [official OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp) for the current client controls and supported transports. This beta does not require a plugin bundle or browser CDP access for its local stdio route.

Source users can keep the existing command: their Python executable, `run_aura.py`, `--mcp`, and optionally `--data` plus the profile path. Install requirements-mcp.txt first. Do not switch the existing Node_repl server to Aura.

Restart or refresh the client's Aura server after upgrading. Expected tools:

- aura_status
- aura_propose_appearance
- aura_propose_performance
- aura_propose_cue
- aura_request_notepad
- aura_request_status

No tool can approve a request. Appearance, speech/mood, visual cues and the Notepad demo enter the local review queue. Pause cancels pending requests. `submitted` means an action started, not that a performance or task completed. Cast/reveal require compatible equipped items.

The stdio bridge opens no inbound network port. This configuration is for a local desktop client with stdio support. A web/cloud client needs its own supported connection mechanism, which this package does not configure. No ChatGPT cookies, passwords or API keys are collected by Aura.

MCP text/tool access does not provide the built-in ChatGPT Voice audio stream. This beta uses local Windows speech or explicitly selected WAV files. A future API-backed voice mode is separate work and must not be described as syncing the built-in app's voice.

Verified here: source SDK round trip and portable bridge protocol checks. The user's earlier desktop connection worked with the source command; the new portable bridge still requires client-specific validation across different machines and account configurations.
