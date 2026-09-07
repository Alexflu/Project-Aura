# Following apps, line-in/out and virtual routes

Open Studio → Presence and scroll to the audio source list.

1. Choose **Applications**, **Output devices**, or **Input devices**.
2. Click **Refresh**. Only active Windows endpoints are listed.
3. Select a row. Its complete name appears below; the list also scrolls horizontally.
4. Click **Follow selected**. **Stop following**, Pause, local speech or WAV playback disconnects it.

Applications isolate an app session on a particular output. Output devices meter
the selected Windows playback endpoint, such as speakers, line-out or a virtual
playback cable. Input devices meter a Windows recording endpoint, which may be
line-in, a microphone or a virtual recording cable. Choosing or refreshing a row
does not start metering. The source is not automatically reconnected on restart.

## Voicemeeter and voice chat

Route the voice-chat app into your chosen Voicemeeter channel/bus, then select the
corresponding Windows endpoint in Aura. Use Windows' playback/recording category
to choose Output/Input devices; a virtual device's friendly name may describe a
different perspective on the route. Aura displays the Windows-provided names.

A dedicated route keeps music and unrelated notifications out of the level Aura
follows. Selecting an entire output meters everything mixed into that endpoint.
Aura does not alter Voicemeeter routing, turn on monitoring, or enable Windows
"Listen to this device". Avoid adding an audible feedback route just to animate
the avatar; only the endpoint meter is needed.

If the meter stays silent, confirm that your chosen route is active in Windows
and Voicemeeter. Some input drivers need another app to keep the stream active.
Software peak meters can report zero in exclusive mode. Unplugged or disabled
devices disconnect with a status message; Refresh and select them again after
reconnecting. A physical line-in/out is available only if its driver exposes a
Windows audio endpoint.

This is amplitude-driven mouth movement, not word/phoneme timing or automatic
emotion detection. It works with routed sound without a direct ChatGPT Voice
integration. No PCM audio, recordings or transcripts are collected. Endpoint
meters may report levels before Windows volume attenuation, so muting a device
does not necessarily stop animation.

The implementation uses Microsoft's [IAudioMeterInformation endpoint interface](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nn-endpointvolume-iaudiometerinformation).
