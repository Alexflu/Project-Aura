# Voice and presence preview — 0.3.0-beta.1

Close your previous Aura, extract the full portable ZIP, and run ProjectAura.exe. Existing appearance preferences remain in place. Open **Presence** for the new controls.

## Try it

1. Select Tactical Ops (`tactical`) or Stealth Striker (`stealth`) in Appearance, or use Try approved Aura look → Apply look.
2. In Presence, enter up to 1,000 characters and choose Speak text. Windows synthesizes an installed local voice into a temporary WAV, then Aura plays it. No account or API key is required. The default/female/male choices select available Windows voice hints; an unavailable voice may fall back or fail.
3. Stop cancels preparation/playback and removes temporary audio. Pause also stops speech. Reduce motion stops animation while allowing audio to play. A crash or forced process termination may leave a temporary file for normal OS cleanup.
4. Play a WAV accepts 16-bit PCM mono/stereo at 8–48 kHz, at most two minutes and 24 MB. Playback uses a temporary copy and never alters the selected source.
5. Mouth delay moves the animation relative to playback by -300 to +300 milliseconds. Positive values delay mouth movement. This compensates approximately for output-device latency.
6. Choose neutral, happy, thoughtful, focused, or sleepy. These explicitly selected cues use a star, dots, target, or sleepy eyes/Zs and adjust new speech's pace. They do not detect your emotions or extract emotion from audio.
7. Hologram adds cyan luminance and scanlines to the illustrated body. Dock left/right places Aura on her current monitor, using its work area. Double-click the floating avatar or select Play entrance for a brief portal/arrival effect. Local Notepad launch also cues arrival when motion is enabled.

Mood, effect, voice choice and timing offset are session controls. Hair and appearance still persist as before. Face and accessory layers, independent color channels, clean transparent edges, gestures, and the helicopter entrance remain future work.

## What synchronization means here

The app measures audio energy in 20 ms blocks and opens/closes the existing mouth sprite using a playback clock. Silence closes the mouth. This is approximate amplitude synchronization, not phoneme/viseme alignment. Device buffering and UI rendering can add latency. The classic body also supports the mouth signal. Audio with music or background noise will move the mouth too.

## ChatGPT / MCP

Restart your Project Aura MCP connection to load `aura_propose_performance(text, mood)`. Configuration paths stay the same. Ask the connected assistant to use this tool for a short line, then select the pending speech request in Aura's Connection tab and review the complete text in the scrollable approval window. The tool cannot approve its own request. An empty text sets only the mood. Requests expire and are cancelled by Pause or disabling the connection.

A submitted performance means local speech preparation was started; the MCP status does not certify that playback finished or was heard. Failures appear in Aura's status bar. No automatic retries. The request queue retains up to 100 records, now including proposed speech text, until bounded pruning or Forget my data. Locally typed text remains only in the window; normal audio completion/Stop removes the temporary playback file.

This does not attach to built-in ChatGPT Voice or use its voice/personality/audio stream. We did not establish a documented built-in voice output hook in the official MCP documentation reviewed on 2026-09-05. The [official MCP guide](https://learn.chatgpt.com/docs/extend/mcp) describes connecting tools. The [Realtime API guide](https://developers.openai.com/api/docs/guides/realtime) describes dedicated audio sessions over supported transports; that is a separate future integration requiring its own setup. No microphone capture, system loopback recording, browser inspection, API traffic, or account-session access is implemented in this build.

## Validation

32 automated tests cover core state, actual MCP stdio proposals/approval, audio envelopes and silence, WAV validation, cancellation/cleanup, bounded inputs, at-most-once performance, and negative-monitor docking geometry. Presence smoke tests use temporary profiles and a silent playback backend to exercise controls. Actual installed Windows speech was separately synthesized and its nonzero audio envelope verified outside the sandbox, which cannot access installed voices. Packaged launch is checked outside that sandbox as well.
