# Skeleton Zero: local Unreal bring-up

Status: offline Python controller plus a native Unreal mannequin stage. See the
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

Install MetaHuman Creator Core Data and enable the MetaHuman Creator plugin in the
engine project. Create and assemble a MetaHuman locally, then bind the same receiver
to its body/face animation setup. Follow Epic's assembly instructions for the chosen
engine version. Keep the initial goal to idle, gaze, mouth controls, one gesture and
walking; strand hair, cloth, blush and advanced expression are later acceptance gates.
Record engine version, asset source, compatible skeleton, animations and licensing
in a local asset manifest before proposing binary assets for the repository.
Repository MIT licensing does not relicense Epic assets.

## Remaining acceptance gates

- Bind an assembled MetaHuman and facial rig with audible speech.
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
