# Skeleton Zero: local Unreal bring-up

Status: tested offline Python controller plus **uncompiled Unreal source scaffold**.
There is no included character, map, animation Blueprint, audio playback or live AI.
Tracking: [issue #13](https://github.com/Alexflu/Project-Aura/issues/13).

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
   version and validating the build. No engine version has been compile-tested here.
2. Right-click `unreal/AuraBody/AuraBody.uproject`, generate Visual Studio project
   files, open the generated solution, and build **Development Editor / Win64**.
   Then open the `.uproject`. Alternatively use the installed engine's Build.bat:

   ```powershell
   & 'C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat' AuraBodyEditor Win64 Development '-Project=C:\path\to\Project-Aura\unreal\AuraBody\AuraBody.uproject' -WaitMutex
   ```

3. Create a Basic level with a floor, light and camera. Save it as
   `/Game/SkeletonZero/L_SkeletonZero`. Set it as the editor/game startup map in
   Project Settings. No map is supplied, so opening the project alone is not a demo.
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
or skeleton bone names. Create these Blueprint bindings before claiming a 3D demo:

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
These C++ behaviors are implemented but await compile/runtime verification.

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

## Acceptance evidence still required

- Successful Editor build, engine/toolchain versions and any source fixes.
- Runtime capture showing a genuinely skinned skeletal character performing all six
  behaviors; label synthetic mouth cues and any diagnostic placeholders.
- Kill the producer while moving/speaking: hold position and close mouth within 1s.
  Restart it, pause/resume, and try an invalid file without crashes or stale replay.
- Check a static leftover snapshot cannot animate on a fresh editor run.
- Record hardware, resolution, average and worst frame times over a one-minute run.
  Initial target: 60 fps on the test machine; this is a target, not a measured result.

## Validation of this supporting slice

Windows / Python 3.14.4: `python -m unittest discover -s tests -q` passed all
94 tests with desktop and MCP dependencies installed, including 12 new controller
tests and the existing real MCP subprocess round trip. Run
`python tools/skeleton_zero_smoke.py` for the separate real-time producer/reader
check: 512 distinct snapshots were observed over 17.14 seconds, covering all six
cue channels, pause and final idle, with no partial JSON. The smoke exposed a
Windows file-sharing race; bounded writer retries and transient reader retries
handle it. This verifies Python/file delivery, not Unreal rendering or C++ behavior.

No Unreal installation was found in the Epic installation registry, common install
location or executable path on this host. There is no compiled C++ result, asset
preview, live Realtime session, perception integration or packaged 3D application.

## Sources checked for this change

- [Epic MetaHuman Creator](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine): installation, character creation and assembly.
- [Epic Animation Blueprints](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprints-in-unreal-engine): skeletal mesh animation and Anim Class assignment.
- [OpenAI Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations): future conversation/audio integration; no live API implementation is claimed.
