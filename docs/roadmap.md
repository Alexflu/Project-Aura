# Roadmap

These are scope milestones, not delivery dates. See the [beta plan and contingency register](beta-plan.md).

## Current priority: embodied 3D Aura

This ordering supersedes the older numbered milestones below for new embodiment
work. Maintain the existing 2D beta, but prioritize proving a real rigged body.

1. **Foundation / Skeleton Zero:** Unreal + a temporary rigged skeletal character,
   idle, gaze, listen, speech cue, gesture and movement in one real-time scene.
   The [offline controller and Unreal scaffold](skeleton-zero.md) are the first
   supporting slice; the compiled character demonstration is still open in
   [issue #13](https://github.com/Alexflu/Project-Aura/issues/13).
2. **Realtime conversation:** opt-in OpenAI Realtime, audible streaming playback,
   interruption, playback-clock mouth animation and session lifecycle.
3. **Behavior and expression:** semantic controls, coordinated gestures and gaze,
   MetaHuman face/body integration, authored emotion, then hair/cloth physics.
4. **Local perception:** explicit source selection/consent, ephemeral observations,
   freshness/confidence and visible capture state. No ambient capture by default.
5. **Desktop embodiment:** transparent host window, monitor coordinates, occlusion,
   hit-testing and approved app adapters through AuraCore.
6. **Polish/performance:** asset provenance, profiling, reduced motion/accessibility,
   packaging and clean-machine tests. High-fidelity assets follow the working loop.

## Earlier beta milestones (historical)

## 0.1 — local tester beta

- [x] MIT license and component boundaries.
- [x] Original animated 2D avatar and floating desktop window.
- [x] Bounded appearance changes, preview, discard and undo.
- [x] Explicit interests, activity recording and optional deterministic adaptation.
- [x] Local persistence, preference export, reset, pause and reduced motion.
- [x] Approved Notepad launch with honest submission reporting.
- [x] Optional MCP queue and real stdio integration test.
- [ ] Validate portable build on a clean Windows machine and multiple displays/scales.
- [ ] Validate the actual ChatGPT account/tunnel connection.
- [ ] Audit with assistive technologies.

## 0.2 — conversational embodiment

Validated ChatGPT compatibility matrix; feedback-driven personalization; versioned import, recovery and migrations; adaptive layout and accessible controls. Optional independent API reasoning only with explicit credentials, costs and privacy controls.

## 0.3 — richer body

Licensed rigged 3D asset format, bounded morph targets, asset provenance, safe loading, preview and rollback. Performance budget, 2D fallback and optional cinematic arrivals.

## 0.4 — useful workspace tasks

One supported app API at a time, with scoped authority, test fixtures, cancellation semantics and verifiable outcomes.

## Research tracks

Supported cooperative games, CAD workflows and hardware need separate platform terms, validation and physical safeguards. No dates or working integrations are implied here.

## Standing product constraint

Official Project Aura releases remain free and open source, with voluntary project-cost support rather than paid access or microtransactions. New integrations must disclose third-party charges and preserve payment-independent access to local features and creations. See the README funding commitment.
