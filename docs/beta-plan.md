# Beta plan and contingencies

## Product decision

Project Aura remains the umbrella for persistent AI embodiment. This first beta establishes a real local body, bounded personalization, state continuity and a controlled integration boundary. A small original 2D avatar keeps the first release usable without a GPU, downloaded assets, paid inference or account setup. It is a foundation for richer embodiment, not a claim that the full vision is complete.

Interpretation of remodeling: change the avatar representation. The beta exposes finite palette, hair, outfit, accessory and silhouette choices. It does not fine-tune language models, modify its source, create arbitrary executable assets or claim general autonomous intelligence. The next renderer can replace these choices with versioned parameters, while the approval and rollback boundary stays the same.

## Shipped beta scope

- Windows appearance workbench, animated original avatar, optional floating window.
- Direct controls and honest offline request matching; preview, apply, discard and 20-step undo.
- Explicit interests and favorite palette; activity counts entered by the user. Optional automatic adaptation is triggered by recording an activity, uses only those inputs, and preserves undo.
- SQLite persistence, bounded request history, preference export, local reset, pause and reduced motion.
- Approved Notepad launch. A submitted launch is not falsely reported as task completion.
- Optional MCP proposal queue using the official SDK. No remote approval tool, arbitrary command tool or inbound network listener.

## Decision sequence

1. Establish explicit permissions, data ownership and bounded appearance parameters before adding reasoning integrations.
2. Exercise a real desktop workflow and a real MCP round trip before claiming integration readiness.
3. Package an unsigned portable tester build with source, dependency notices and honest limitations.
4. Validate the account-specific ChatGPT connection, clean-machine installation, display scaling and assistive technologies with testers.
5. Add richer rendering and narrowly scoped integrations only after their acceptance tests and asset rights are understood.

## Risk register and response

No design can enumerate every future possibility. The following covers plausible failure classes; revisit at every capability or distribution change.

| Scenario | Current response | Gate for expansion |
| --- | --- | --- |
| ChatGPT UI, account policy or SDK changes | Isolated adapter; offline workbench continues; pinned SDK and protocol tests | Test actual target app/account and update compatibility matrix |
| Tunnel or provider unavailable | No automatic retry of actions; local customization stays usable | Reconnect explicitly and test tool discovery |
| Untrusted chat text asks for broader access | Schema validates finite look choices; no command field; MCP cannot approve requests | Capability-specific authorization and hostile-input evaluations |
| Appearance suggestion misses the user's taste | Preview, discard, undo; automation off by default | Explicit preference feedback, no inferred sensitive traits |
| Habits reveal personal information | Manual counts only, no surveillance; sharing off; export/reset controls | Purpose-specific consent before any new observation source |
| Local malware or shared Windows account | State is not encrypted; documented same-user trust boundary | OS credential storage, per-user access controls and security review before sensitive data |
| Repeated requests or double approval | Ten pending requests, expiry, transaction claim, no automatic launch retry | Idempotency keys and load tests before public multi-user service |
| Crash during external launch | Request marked launching before effect; outcome may remain unknown; no retry | Integration-specific receipts and reconciliation before consequential actions |
| Disk failure, corrupt data or newer schema | Transactions; reject corrupt/newer state without silently resetting it | Versioned backup/restore and migration tests before schema changes |
| Inaccessible UI or small display | Keyboard controls and reduced motion; fixed minimum size documented | Screen-reader audit, responsive layout, high-DPI/multi-monitor tests |
| Heavy rendering or thermal/battery impact | Simple 2D rendering at a modest rate | Performance budget and fallback renderer before 3D/continuous perception |
| Malicious or unlicensed avatar asset | No external assets or asset import in beta | Provenance/license manifest, size limits, safe loader, no scripts, quarantine |
| User requests a real person's likeness | No likeness import/generation in beta | Consent and rights workflow before likeness features |
| Minors or harmful generated content | No open-ended generation in beta | Age-appropriate experience and provider-policy review before generation/community gallery |
| CAD output is mechanically unsafe | No CAD/hardware execution in beta | Units/constraints validation, simulation and qualified human review; physical interlocks |
| Game bans or anti-cheat conflict | No game automation in beta | Supported APIs, publisher terms, private testing; never anti-cheat evasion |
| Dependency compromise | Isolated optional SDK; tested versions and automated tests; no auto-updater | Advisory/license review and reproducible build evidence per release |
| Unsigned executable warnings | Source is available; build and hash provided; no instruction to disable protection | Trusted signing and clean-machine security checks before broad distribution |
| Project grows into a hosted service | Current single-user design stays local | Tenant isolation, authentication, revocation, rate limits, privacy policy and operational ownership |
| Project is abandoned or commercialized | MIT source, local operation, plain JSON preference export | Maintain clear licensing for new assets and third-party integrations |
| Funding or feature commitments distort priorities | No sponsorship-dependent functionality or delivery promises | Publish scope, costs and governance before paid tiers |
| Unknown issue appears | Pause/revoke; preserve evidence without private user data; classify and reproduce | Regression test plus updated risk register before release |

## Next milestones and measurable exit criteria

### 0.1 tester beta

Local core and UI tests pass; executable opens and closes; clean-machine and account integration tests are documented as pending. Gather feedback on identity, appearance controls and useful first tasks. Do not label this broadly production-ready.

### 0.2 conversational embodiment

Validate ChatGPT through the supported connection on named app versions. Add structured feedback to personalization, import/export with schema migration, accessible navigation, and scoped provider sessions if an independent API mode is justified. Keep consent and costs visible. Test malicious tool inputs, disconnects and cancellation.

### 0.3 richer body

Evaluate VRM/glTF or another licensed rig format with a renderer abstraction. Add bounded morph targets, material variants, rig compatibility, frame-time limits, asset provenance, preview and rollback. Isolate asset parsing; do not permit embedded executable behavior. Keep a 2D fallback.

### 0.4 useful workspace tasks

Add one official Windows/app API integration at a time, with receipts, failure reporting, audit boundaries and cancellation semantics. Prove it on test documents before using valuable data. Keep animations driven by actual task events.

### Research tracks

Co-op participation, CAD, hardware, cinematic helicopter arrivals and richer environmental perception remain research tracks. Each needs a concrete demo target, supported interface, performance budget, rights/terms review and acceptance tests. Physical machines need safeguards independent of the language model.

## Legal and policy posture

MIT covers Aura's source and original avatar artwork. Third-party components keep their own licenses. The beta uses documented integration mechanisms and does not patch or scrape ChatGPT. [OpenAI's terms](https://openai.com/policies/terms-of-use/) and applicable account/business terms must be rechecked for the intended deployment; integration design is not a blanket legal guarantee. Review jurisdiction-specific privacy, consumer and asset rights before a public hosted launch. The developer documentation currently supports [MCP integration](https://developers.openai.com/plugins/build/mcp-server); public distribution has separate requirements.
