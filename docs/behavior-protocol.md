# Aura behavior protocol v1

This is a development-only, single-producer renderer interface. It is independent
of the shipped beta's MCP approval queue and is not exposed through MCP. The demo
never reads or changes the user's profile. A future product connection must route
Pause/revocation from AuraCore into this controller before enabling remote cues.

## Semantic commands

```json
{"version":1,"id":"wave-1","action":"gesture","params":{"name":"wave","duration_s":2}}
```

Only the four envelope fields above are allowed. Version is integer 1. IDs are
1..64 characters, unique within a producer session. Duplicates return `duplicate`;
the demo accepts at most 4096 distinct IDs before requiring a new controller.
Invalid commands raise ValueError without changing state. These return values mean
controller acceptance only, never proof that Unreal rendered a pose.

| Action | Exact params | Effect |
| --- | --- | --- |
| idle | {} | Clear speech/gesture and stop at current position |
| listen | {} | Interrupt speech/gesture/movement and enter listening |
| speak | duration_s | Synthetic mouth cue for 0.05..10 seconds |
| look_at | x, y, z | Persistent gaze target in stage-relative Unreal centimeters |
| gesture | name, duration_s | wave or nod, lasting 0.05..10 seconds |
| walk_to | x, y | Walk toward stage-relative XY at 100 cm/s, no overshoot |
| expression | name, intensity | Persistent neutral/happy/curious/concerned face intent at 0..1 intensity |
| posture | name | Persistent neutral/attentive/relaxed body intent |
| blush | intensity | Persistent material-effect intent at 0..1 |
| pause | {} | Cancel all transient behaviors and block new cues |
| resume | {} | Unpause; cancelled/rejected cues are not replayed |

Coordinates must be finite numbers within -500..500 cm. Unreal axes: X forward,
Y right, Z up. Movement remains on the stage plane; this is not navigation or
computer/window control. Speech and gesture can overlap movement. New commands
replace the same channel. Listening stops motion to attend to the user. Idle and
pause preserve gaze/position and persistent expression/posture/blush state; the
renderer should freeze animation while paused. Loss of the producer resets those
expressive channels to neutral so stale appearance cannot become stuck on screen.

The three expressive commands are deliberately semantic. `happy` does not specify
blendshape weights, `attentive` does not specify spine rotations, and blush does
not expose a material parameter name. Unreal/MetaHuman owns the mapping, blending,
retargeting and asset-specific implementation. This keeps model intent portable
across temporary mannequins, MetaHumans, and future rigs.

## Local snapshot transport

Python atomically replaces one UTF-8 JSON file at 30 Hz. Unreal samples at 30 Hz.
No TCP/UDP listener, key or transcript is involved. This simple transport is for
bring-up, not final audio streaming. Concurrent writers and network shares are not
supported. Windows reader locks are retried for up to 50 ms; persistent write
failure stops the producer and the receiver then times out.

Exactly 17 fields: `version`, `session` (UUID), `sequence` (positive increasing
integer), `paused`, `mode` (idle/listening/speaking), `x`, `y`, `moving`, `gaze_x`,
`gaze_y`, `gaze_z`, `gesture` (none/wave/nod), `expression`
(neutral/happy/curious/concerned), `expression_intensity` (0..1), `posture`
(neutral/attentive/relaxed), `blush` (0..1), and `mouth_open` (0..1).
The full snapshot replaces state; intermediate snapshots may be skipped, so this
transport cannot guarantee execution of very short gestures. No acknowledgment
or delivery guarantee is implemented. Use durations comfortably above 1/30s.
Freshness uses the receiver's monotonic clock and sequence advancement, not file
timestamps. Loss of fresh input for 1s stops motion/gesture/speech, holding position.
Same-user local processes are within the trust boundary.

## Next interfaces (not implemented)

AuraBridge will own the optional Realtime session, credentials and device consent.
It will send semantic cues through AuraCore validation, never model-supplied bone
transforms or arbitrary code. Unreal owns animation blending, retargeting and
physics. Local perception supplies bounded observations (source, confidence,
timestamp, expiry) to AuraCore, not direct renderer or computer commands.

Future voice adapter contract:

- `start_session(config)`: require explicit microphone/cloud consent and disclosed
  API costs; credentials stay outside snapshots and saved avatar appearance.
- `on_user_speech_started()`: stop current playback and expression, cancel the old
  response, enter listen; track played audio for conversation truncation.
- `on_audio_chunk(response_id, pcm)`: queue PCM for playback. Generation arrival
  does not mean the user has heard speech. Drive mouth/visemes using playback time.
- `on_playback_finished(response_id)`: clear speaking only after the device drains.
  Ignore late chunks from cancelled responses.
- `stop_session()`: cancel audio and behaviors, release the microphone, clear
  transient buffers. Never silently reconnect a revoked session.

These are design signatures, not callable stubs or a working API client. The
existing synthetic `speak` command must be replaced with playback-clock expression
for a live voice milestone. No emotional awareness or user attention sensing can
be inferred from a gaze animation alone.
