# Project Aura

An open-source experiment in persistent AI embodiment.

Give an AI a workspace, visual presence, controlled computer access, and the ability to interact with software, games, hardware, and its environment while keeping the user in control.

The goal: make AI feel less like an application you open and more like a collaborator that inhabits the computer with you.

Desktop companion. Agent framework. Digital familiar. Occasionally arrives by helicopter.

## Status

**0.1.0-beta.1 — local Windows tester beta.** Aura now has an animated 2D avatar, a floating desktop window, bounded appearance customization, explicit-interest adaptation, persistent preferences, undo, and an optional MCP connection. Full 3D modeling, co-op play and CAD automation remain future work.

## Try the beta

From a portable Windows build, extract the entire archive and open `ProjectAura.exe` inside its folder. Keep `_internal` alongside it. No Python installation or API key is needed for the desktop workbench. The build is unsigned and tested on the development host, not certified across clean machines.

From source, use Python 3.11 or newer with Tk installed (the Windows python.org installer includes it):

```powershell
python run_aura.py
```

1. In **Appearance**, choose a palette, hairstyle, outfit, accessory and silhouette. Preview, apply, or undo.
2. In **Your interests**, save hobbies and a favorite palette, then **Suggest from interests**. Activity counts are entered by you. Automatic adaptation is optional and off by default.
3. Choose **Float on desktop** to show Aura alongside your applications. **Pause Aura** stops adaptation and cancels pending remote requests.
4. In **Connection**, try the approved Notepad launch. To connect ChatGPT, follow the separate [MCP setup guide](docs/chatgpt.md). The offline request field is keyword matching, not general AI chat.

State is local to your Windows account. Export preferences or reset them in **Your data**. See [testing and limitations](docs/testing.md).

## The project

| Component | Purpose |
| --- | --- |
| **Project Aura** | Umbrella project and contributor community. |
| **AuraOS** | Agent/runtime layer that hosts and manages Aura's operation. |
| **AuraShell** | Desktop avatar, overlays, animation, and visual interactions with windows and icons. |
| **AuraCore** | Orchestration, state, permissions, and task execution. |
| **AuraBridge** | Integrations with Windows, apps, hardware, games, and CAD tools. |

Aura is the reference character. The architecture should accommodate other avatars and personalities.

## What we want to build

- A persistent desktop presence with expressive animation and optional voice interaction.
- Useful computer assistance through explicit, scoped capabilities.
- Visual performances that accompany real task progress: an arrival by helicopter can announce work, while task results remain verifiable independently of the animation.
- Integrations that grow from desktop applications into CAD, hardware, and supported cooperative games.

## What works and what comes next

The beta opens Notepad only after approval and reports launch submission accurately. The official MCP SDK client/server round trip is tested; connection to a particular ChatGPT desktop account remains unverified. Appearance changes remodel the procedural avatar within supported parameters, not the language model.

The [beta plan and risk register](docs/beta-plan.md) cover integration changes, privacy, asset rights, crashes, outages, 3D models, games, CAD, hardware, packaging and future distribution.

## Develop and test

The desktop has no third-party Python dependencies. The optional MCP adapter uses the official SDK:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-mcp.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/gui_smoke.py
```

Build a portable Windows executable with `requirements-build.txt` and `python tools/build_windows.py`. The full tested Windows dependency snapshot is `requirements-lock.txt`. See [testing](docs/testing.md) for details.

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [contributing](CONTRIBUTING.md).

## Open-source licensing

Project Aura is licensed under the [MIT License](LICENSE).
