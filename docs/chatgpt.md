# ChatGPT compatibility

Verified documentation: September 5, 2026. Account-level connection has **not** been tested in this beta. The real local MCP stdio client/server flow is tested.

## Supported boundary

Aura runs alongside ChatGPT as a separate desktop application. The optional official MCP SDK adapter exposes four tools: `aura_status`, `aura_propose_appearance`, `aura_request_notepad`, and `aura_request_status`. It does not modify ChatGPT, read its database, scrape conversations, inject input, reuse session cookies, or obtain model weights. A ChatGPT subscription is not treated as permission to call private APIs.

The desktop works offline. Its request field uses explicitly labeled keyword matching. ChatGPT supplies language reasoning only after you connect the MCP tools. Tool metadata describes the limited actions and never impersonates a system instruction.

## Local MCP clients

Install Python 3.11 or newer and the optional SDK in a virtual environment from the source checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-mcp.txt
```

Configure a client that supports local stdio MCP with an absolute command and arguments:

```json
{
  "mcpServers": {
    "project-aura": {
      "command": "C:/path/to/Project-Aura/.venv/Scripts/python.exe",
      "args": ["C:/path/to/Project-Aura/run_aura.py", "--mcp"]
    }
  }
}
```

This is a generic MCP example, not a ChatGPT settings file. Use your client's documented configuration interface. Keep the desktop and MCP process under the same Windows user. Both use `%LOCALAPPDATA%/ProjectAura/aura.sqlite3` by default; if using `--data`, pass the identical absolute file path to both processes.

Open Aura's Connection tab, enable incoming requests, and save. Optional sharing exposes selected interests and favorite palette, never activity counts. The server opens no inbound port. Only connect clients you trust; the trust boundary is your Windows account and the selected client. Do not expose this single-user server as a shared public endpoint.

## ChatGPT through the current supported tunnel

OpenAI's current documentation supports private stdio MCP servers through Secure MCP Tunnel. It requires developer-mode access, a Platform tunnel, appropriate tunnel permissions, a runtime credential for the separate tunnel client, and association with the intended ChatGPT workspace. Availability is account-dependent. Aura itself does not collect that credential.

1. Follow [OpenAI's Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) to create a tunnel and obtain the official tunnel client.
2. Configure the tunnel client's local stdio command to run the Python MCP command above. Use the official quickstart/doctor commands to validate your configuration. Keep its credentials in the mechanism recommended by the tunnel client, outside this repository.
3. Follow [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt) to enable developer mode, add the tunnel connection, and inspect the four tools.
4. Ask ChatGPT to read Aura's status, then propose an ocean palette with headphones. In Aura, select the queued request and review it. Verify ChatGPT reports pending until you accept, then reports applied when it polls the request identifier.
5. Test rejection, pause, connection disable, and request expiry. Record the actual ChatGPT desktop version, account type and results in the compatibility matrix before declaring that version supported.

If your account lacks tunnel/developer access, use the offline appearance workbench or a supported local MCP client. No fallback attempts to bypass account restrictions. Public plugin distribution would require a separate authenticated multi-user service and review; this beta does not provide one.

## Compatibility matrix

| Surface | Beta status |
| --- | --- |
| Windows local appearance workbench | Tested on the development host |
| Official Python MCP SDK 2.1.1 stdio client | Automated end-to-end test passed |
| ChatGPT desktop + Secure MCP Tunnel | Documented integration path; account connection unverified |
| ChatGPT web + Secure MCP Tunnel | Documented integration path; account connection unverified |
| Other local MCP clients | Protocol-compatible design; client-specific validation needed |
| macOS/Linux desktop | Source may run with Tk; not certified, Notepad disabled |

The adapter pins SDK 2.1.1. On SDK or ChatGPT changes, rerun the protocol and approval tests before updating the matrix. [Official MCP server guidance](https://developers.openai.com/plugins/build/mcp-server) identifies the supported Python SDK and recommends focused tools with schemas and annotations.
