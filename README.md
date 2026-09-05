# Project Aura

An open-source experiment in persistent AI embodiment.

Give an AI a workspace, visual presence, controlled computer access, and the ability to interact with software, games, hardware, and its environment while keeping the user in control.

The goal: make AI feel less like an application you open and more like a collaborator that inhabits the computer with you.

Desktop companion. Agent framework. Digital familiar. Occasionally arrives by helicopter.

## Status

Early planning and architecture. This repository describes the intended system; it does not yet contain a working runtime, desktop avatar, or game-playing agent.

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

## First milestone

Build a small Windows demonstration: Aura appears in an overlay, accepts a request to open a chosen application, obtains any required permission through AuraCore, invokes an AuraBridge integration, and reports the actual outcome. AuraShell animates the task's lifecycle.

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [contributing](CONTRIBUTING.md).

## Open-source licensing

Project Aura is licensed under the [MIT License](LICENSE).
