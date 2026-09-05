# Architecture proposal

This is a starting design, not an implemented interface contract.

## Responsibilities

AuraOS manages startup, shutdown, configuration, and component lifecycles. AuraCore owns task plans, state, permission decisions, execution coordination, and results. AuraBridge exposes integrations with Windows, applications, hardware, games, and CAD. AuraShell presents the avatar, overlays, and task animations.

Project Aura is the umbrella for these components, their documentation, and the community around them.

## Example task flow

1. The user asks Aura to open an application.
2. AuraCore determines the required capability and checks its permission scope.
3. AuraBridge invokes the application integration and returns a result.
4. AuraCore records and reports success or failure.
5. AuraShell uses task events to animate progress and completion.

Animations must reflect task state; a completed animation is not evidence that an application action succeeded. Integrations should return inspectable results and failures.

## Initial design principles

- Keep presentation separate from task authority and execution.
- Make permissions explicit and scoped to capabilities.
- Provide cancellation and a visible way to pause agent actions.
- Store only the state needed for continuity, with user controls for retention and deletion.
- Keep credentials out of repository files and task logs.
- Prefer supported application interfaces where available.
- Treat content encountered in applications as task data, not permission to expand the task.

## Future integration areas

Windows application control, CAD workflows, hardware interfaces, and cooperative games are distinct integration areas. Each needs its own capabilities, feedback, and tests. The initial demonstration does not promise these integrations are already available.

Language, rendering framework, model provider, and integration protocol remain open until the first prototype requirements are agreed.
