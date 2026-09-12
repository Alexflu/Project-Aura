# Skeleton Zero: local Unreal bring-up

Status: offline Python controller plus native Unreal mannequin and MetaHuman stages. See the
runtime validation section below for what has actually been checked. The mannequin
is a temporary rigged 3D body; it is not Aura's final MetaHuman. There is no audio
playback or live AI in this harness.
Tracking: [issue #13](https://github.com/Alexflu/Project-Aura/issues/13).

## Automated mannequin route

Install Unreal 5.6.1 with **Templates and Feature Packs**, Engine Source and
MetaHuman Creator Core Data. On the development host this is
`D:\Programs\EpicGames\UE_5.6`. Visual Studio 2022 C++ tools and a compatible Windows
SDK are required. From the repository root:

```powershell
python tools/unreal_body.py prepare --engine-root D:\Programs\EpicGames\UE_5.6
python tools/unreal_body.py build --engine-root D:\Programs\EpicGames\UE_5.6
python tools/unreal_body.py demo --engine-root D:\Programs\EpicGames\UE_5.6
```

After setup, double-click **Launch Skeleton Zero.cmd**. The helper discovers Unreal
from Epic's installation manifest (or `AURA_UNREAL_ROOT`), waits for the rig to load,
plays the sequence, and leaves the stage open until you close it. Each demo has an
isolated input directory. For manual control use `run` instead of `demo`, then run
`python tools/skeleton_zero.py` in a second terminal. The native game mode
creates the stage, lights, camera and skeletal actor in the engine's Entry map.
No hand-authored map or Animation Blueprint is needed for this temporary route.
The helper keeps its derived-data cache beside the project on D:. It copies local
Epic template assets without overwriting differing files and records their source
and hashes in `Saved/Aura/asset-manifest.json`. Those assets are ignored by Git;
they are not relicensed as MIT. Install them locally on each development machine.

The mannequin uses an actual skinned skeletal mesh with procedural idle, gaze,
walking and a wave/nod. These are prototype poses, not motion-captured performance,
navigation, foot-contact IK or production animation blending. Listening changes
the attentive pose and HUD. The synthetic speech signal is a HUD meter because
this mannequin has no facial rig. Expression/blush are also diagnostic signals;
MetaHuman face/material bindings remain open. Pause/disconnect hold position and
freeze skeletal motion. There is no transparent desktop window yet.

Run the real-engine smoke test with the stage closed:

```powershell
python tools/unreal_runtime_smoke.py --engine-root D:\Programs\EpicGames\UE_5.6
```

It launches its own stage with isolated input/telemetry files, checks a static stale
snapshot, skeletal load and cue responses, then verifies timeout, malformed-input
stop and producer restart. It closes only its own Unreal process. JSON evidence is
saved under `Saved/Aura/Smoke/`. `-AuraDataDir` is a startup option for isolated
tests; semantic commands cannot choose files. `-AuraTelemetry` enables at most two
minutes of development telemetry at 10 Hz, without screenshots or private data.

The following manual route is still useful when replacing the native mannequin
with a custom Animation Blueprint or MetaHuman.

## Run the part that works today

From the repository root, with Python 3.11+:

```powershell
python tools/skeleton_zero.py
```

This runs a 17-second authored sequence at 30 updates/second and atomically writes
`unreal/AuraBody/Saved/Aura/behavior.json`. It prints each accepted cue. Use `--fast`
only for offline checks; Unreal needs the normally paced stream. Ctrl+C writes a
final idle state. A killed producer is handled by the Unreal receiver timeout.
No credentials, network listener, audio capture, camera or screen capture is used.
Use one producer and one editor instance per project copy.

## Install and build locally

1. Install Unreal Engine 5.6 through Epic Games Launcher, plus the Visual Studio
   C++ game-development toolchain and Windows SDK required by that engine release.
   The descriptor targets 5.6; a later installed engine requires selecting that
   version and validating the build. Unreal 5.6.1 has been compile-tested here.
2. Right-click `unreal/AuraBody/AuraBody.uproject`, generate Visual Studio project
   files, open the generated solution, and build **Development Editor / Win64**.
   Then open the `.uproject`. Alternatively use the installed engine's Build.bat:

   ```powershell
   & 'C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat' AuraBodyEditor Win64 Development '-Project=C:\path\to\Project-Aura\unreal\AuraBody\AuraBody.uproject' -WaitMutex
   ```

3. For a custom Blueprint replacement, create a Basic level with a floor, light and camera. Save it as
   `/Game/SkeletonZero/L_SkeletonZero`. Set it as the editor/game startup map in
   Project Settings. The native route already supplies a stage; override AuraStageMode in your
   custom map to avoid spawning a second body.
4. For the first proof, add the engine's Third Person content pack (or migrate its
   mannequin and dependencies from a local Third Person template project). Use a
   skeletal mesh with its compatible idle/walk animations. A rigid mesh, screenshot
   or articulated picture does **not** satisfy this milestone.
5. Create Actor Blueprint `BP_AuraHarness`. Add a scene root, SkeletalMesh component
   and **Aura Behavior Component**. Place the actor on the floor. Set the mesh's
   Animation Mode to Use Animation Blueprint and choose its compatible Anim Class.
   Do not enable physics simulation or a competing movement controller in this
   harness. Collision/pathfinding and CharacterMovement integration come later.

## Wire the receiver to the actual rig

The component only exposes validated state; it intentionally knows no asset paths
or skeleton bone names. AuraRigActor already binds the mannequin. Use these equivalent Blueprint
bindings for a custom replacement:

| Binding | Exact behavior to implement |
| --- | --- |
| BeginPlay | Save actor location as `StageOrigin`. Save initial mesh orientation. Bind a custom event to the component's OnBehaviorUpdated dispatcher. |
| OnBehaviorUpdated | If Connected, set actor location to StageOrigin + PositionCm. Position is relative to the stage, not desktop pixels. |
| Idle/walk | Feed Moving into an Anim Blueprint blend between compatible looping idle and walk sequences. Derive facing from consecutive positions; keep prior facing when stopped. Do not also apply root-motion translation. |
| Gaze | Transform StageOrigin + GazeTargetCm into the space expected by a head/eye Look At or Control Rig node. Blend gradually and clamp head rotation to the rig's comfortable range. |
| Listen | Mode == listening lights a small visible listening indicator; optionally use an attentive pose. This is an authored cue, not a working microphone. |
| Speak | Feed MouthOpen (0..1) into a jaw morph/rig control if the mesh has one. A mannequin without a facial rig can show a clearly labeled diagnostic meter, but facial acceptance remains open. The value is a synthetic oscillator, not lip sync or audio. |
| Gesture | Compare Gesture to a saved PreviousGesture; on change to wave/nod play the corresponding compatible montage once. Add its slot to the AnimGraph. Stop/fade the montage when Gesture becomes none. Do not restart it on every heartbeat. |
| Pause/disconnect | Stop montages, set mouth to zero and disable walking. Freeze procedural gaze/secondary motion while Paused. Hold the actor position. On reconnect ease to the new position if a producer restarted. |

`LastError` and `Connected` are available for a development HUD. The receiver reads
only `Saved/Aura/behavior.json`, rejects malformed/oversized/unsupported snapshots,
requires an advancing sequence, and idles after one second without fresh valid data.
A leftover file cannot start animation: each new session needs a second snapshot.
These C++ behaviors passed real-engine runtime verification.

Run `python tools/skeleton_zero.py` **after Play In Editor**. Expected checkpoints:
0s idle; 1s gaze; 2s listening; 4s speaking cue; 4.5s wave; 8s walk 200 cm;
11s pause; 12s resume; 12.5s walk home; 15s idle. The script exits around 17s.
The timeline is reproducible and is not model-driven behavior.

## Replace the mannequin with MetaHuman

**Appearance target remains the [approved Aura design](../aura/assets/approved-direction.png).**
The Ada preset is a disposable rigging/animation reference, not a replacement
character design. Preserve Aura's stylized face, black/violet hair, violet eyes
and established wardrobe direction when building the final assets. Custom hair,
clothing and facial shaping may be needed; importing a preset does not achieve
that likeness.

After building, close any other full editor instance for this project and double-click
**Open Aura MetaHuman.cmd**, or run `python tools/unreal_body.py open-metahuman`.
This opens the full editor directly on the preserved local character, preparing it
if missing. Startup can take several minutes. Script failures appear in
`unreal/AuraBody/Saved/Logs/AuraBody.log`; successful opening logs
`AURA_METAHUMAN_EDITOR_OPEN`. Opening the editor does not assemble or connect a
runtime body. Rigging and assembly remain separate steps inside MetaHuman Creator.

The project enables the 16-bit bone indices, unlimited influences, skin cache,
mesh distance fields and DirectX 12 / Shader Model 6 settings required by this
local MetaHuman preview. Restart an already-open editor after changing these.
The launch script explicitly keeps the editor alive after its Python work finishes.

For the next local gate, select **Create Full Rig**. If Epic opens its account
portal in your browser, complete the sign-in there. The rigging service requires
that account session; the local mannequin demo does not. After rigging completes,
download the texture source and select **Assembly > UE Optimized > High**, then
assemble and save the generated assets. Follow the
[Unreal 5.6 assembly guide](https://dev.epicgames.com/documentation/metahuman/assembly?application_version=5.6).
An opened preset or success marker alone is not evidence of an assembled rig.

### Verified local assembly

The development host has now completed Full Rig (joints and blend shapes),
downloaded 4K face/body texture sources and assembled **UE Optimized / High**.
The saved prototype Blueprint is
`/Game/MetaHumans/AuraPrototype_Ada/BP_AuraPrototype_Ada`.
The authoring character remains `/Game/Aura/Characters/AuraPrototype_Ada`.
Both are locally licensed prototype assets, ignored by Git along with their
shared `Content/MetaHumans` dependencies.

After assembling and saving on another machine, verify the assets with:

```powershell
python tools/unreal_body.py audit-metahuman
```

This starts a separate Unreal commandlet, loads the Blueprint, constructs a
temporary actor, verifies skeletal Body and Face components and destroys the
actor without saving a level. Evidence goes to `Saved/Aura/metahuman-audit.json`.
The local audit passed with **342 body bones and 875 face bones**, plus a clothing
skeletal component. The commandlet reported zero errors and warnings.
This proves asset loading/construction, not animation or packaged-game readiness.

### Run the assembled MetaHuman

After assembly, audit and a native build, double-click **Launch Aura MetaHuman Demo.cmd**
or run `python tools/unreal_body.py demo --metahuman`. The launcher waits for the
MetaHuman adapter before sending the same 17-second offline sequence. For manual
input use `python tools/unreal_body.py run --metahuman` and then the producer.
If the Blueprint or required skeleton is missing, Unreal logs the failure and
keeps Quinn visible; the MetaHuman demo times out with setup guidance. A mannequin
fallback does not pass the MetaHuman smoke test.

`UAuraMetaHuman` spawns the fixed local assembled Blueprint alongside the hidden
Quinn pose driver. Its animation proxy transfers common bone rotation deltas by
name while preserving the target's reference proportions. The face follows the
body and retains its assembled post-process RigLogic. Inputs are copied on the
game thread before worker evaluation; explicit tick prerequisites order driver,
body and face. No asset path is accepted through semantic commands.

The synthetic mouth signal drives `CTRL_expressions_jawOpen`. `happy` blends
mouth-corner pull with cheek raise; `curious` raises the brows asymmetrically;
`concerned` blends inner-brow raise, brow lowering and mouth-corner depression.
Expression weights ease toward their targets rather than switching abruptly.
A 250 ms procedural blink repeats every 3.7 seconds while connected and active.
Pause/disconnect immediately zeros facial controls and resets the blink clock.
These are authored expression mappings, not inferred emotion. Blush remains a
diagnostic value without a material binding. The stage camera is now on the same
side as the initial gaze target so the face is easier to inspect. There is
still no audio, phoneme lip sync, live conversation or production foot-contact IK.
The visible prototype is Ada; the approved Aura appearance above is unchanged.

Run the real-engine check with other stage instances closed:

```powershell
python tools/unreal_runtime_smoke.py --engine-root D:\Programs\EpicGames\UE_5.6 --metahuman
```

This checks actual MetaHuman jaw-bone articulation, wrist displacement, stage
movement and mouth shutdown on input loss, in addition to the receiver checks.
It also checks expression curves, actual lip-corner bone deformation with a silent
jaw, blink activity and clearing an active smile on pause.
Bounded `metahuman-runtime.jsonl` telemetry accompanies the existing driver log.
The recorded run passed with a 20.52-degree jaw range and 171 driver samples;
sampled warm mean/worst frame times were 16.668/16.823 ms on the hardware below.
These exclude startup stalls and do not constitute a one-minute benchmark.
A subsequent validation of the final build also passed the behavior checks, but
sampled 19.447 ms mean with a 400 ms worst frame. Smooth 60 fps is not yet a
reliable acceptance result; investigate these hitches before performance signoff.
The separate local speech route below connects audio-envelope jaw motion; the
next facial gate is phoneme-shaped lip sync.

Install MetaHuman Creator Core Data and enable the MetaHuman Creator plugin in the
engine project. Create and assemble a MetaHuman locally, then bind the same receiver
to its body/face animation setup. Follow Epic's assembly instructions for the chosen
engine version. Keep the initial goal to idle, gaze, mouth controls, one gesture and
walking; strand hair, cloth, blush and advanced expression are later acceptance gates.
Record engine version, asset source, compatible skeleton, animations and licensing
in a local asset manifest before proposing binary assets for the repository.
Repository MIT licensing does not relicense Epic assets.

## Remaining acceptance gates

### Local audible speech prototype

After building and assembling the MetaHuman, run:

```powershell
python tools/unreal_speech.py --text "Hello Alex. This is local speech playback."
```

This opens its own stage, waits for the MetaHuman receiver to connect, synthesizes
text using the installed Windows voice, and sends the existing audio envelope to
the jaw while Windows plays the clip. It closes its own stage after playback.
Ctrl+C, renderer exit, loss of renderer telemetry or a playback error stop audio.
The adapter also stops audio when paused; there is not yet a product pause button
for this command-line prototype. Text is limited to 1,000 characters and each
playback session to 110 seconds including synthesis. Temporary audio is cleaned up.
No text, paths or device commands have been added to the semantic protocol.

This is volume-driven jaw movement using the Windows WAV player's reported
position in milliseconds, not phoneme-shaped lip sync or a hardware sample clock.
Polling and rendering latency can still introduce an offset. The local MetaHuman
route uses a dedicated MCI WAV player; the existing 2D speech player is unchanged.
Microsoft documents position and time formats in its
[MCI status reference](https://learn.microsoft.com/en-us/windows/win32/multimedia/status).
MCI is a legacy backend suitable for this bounded WAV prototype; a future streaming
conversation needs a streaming audio backend. There is no microphone, live Realtime conversation, or
automatic speech triggered by the existing silent demo. Force-killing the helper
can bypass its cleanup; ordinary interruption and renderer loss use explicit stop.

The first local Windows speech run completed with 97 MetaHuman telemetry samples,
a 22.81-degree jaw range, and zero mouth/jaw values at completion. The Unreal build
and 105 Python tests passed, including playback-envelope silence, pause and error
cleanup. This does not measure acoustic output latency or phoneme accuracy.
The playback-position update passed 107 tests and a second Unreal speech run
(86 samples, 22.81-degree jaw range, ending at zero). A real Windows player check
also verified advancing position, explicit stop, reopening and natural completion.

- Replace approximate audio-envelope jaw movement with phoneme-shaped facial animation.
- Replace procedural poses with authored animation and foot-contact IK.
- Record hardware, resolution, average and worst frame times over a one-minute run.
  Initial target: 60 fps on the test machine; this is a target, not a measured result.

## Validation of this supporting slice

Windows / Python 3.14.4: `python -m unittest discover -s tests -q` passed all
95 tests with desktop and MCP dependencies installed, including controller
tests and the existing real MCP subprocess round trip. Run
`python tools/skeleton_zero_smoke.py` for the separate real-time producer/reader
check: 512 distinct snapshots were observed over 17.14 seconds, covering all six
cue channels, pause and final idle, with no partial JSON. The smoke exposed a
Windows file-sharing race; bounded writer retries and transient reader retries
handle it. This verifies Python/file delivery separately from the native runtime test.

Unreal 5.6.1 Development Editor / Win64 compiled with Visual Studio 2022 17.14,
MSVC 14.44.35225 and Windows SDK 10.0.22621.0. Unreal warns that MSVC 14.38 is
preferred; the installed compiler completed both native and MetaHuman plugin builds.
The stage loaded Quinn Simple with 89 bones from 128 local template files.
A visible 17-second recording showed the offline sequence. The real-engine smoke
checked wrist/foot bone displacement, gaze, movement and input-loss behavior.

On RTX 3090 / Ryzen 9 3900X / 64 GB RAM, a corrected-body run recorded 178 samples
at 10 Hz. After the first three seconds, sampled mean frame time was 16.667 ms and
worst 16.682 ms with a 60 fps cap. Requested window size was 1280x720; Windows
125% DPI produced a 1600x900 capture. These are sampled warm frame times, not an
every-frame or one-minute benchmark. Cold startup can stall.

There is no live Realtime session, facial lip sync, perception integration or
packaged transparent desktop application in this slice.

## Sources checked for this change

- [Epic MetaHuman Creator](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine): installation, character creation and assembly.
- [Epic Animation Blueprints](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprints-in-unreal-engine): skeletal mesh animation and Anim Class assignment.
- [OpenAI Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations): future conversation/audio integration; no live API implementation is claimed.
