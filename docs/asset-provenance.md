# Release asset provenance

The generated design sheet (`approved-direction.png`) and runtime sprite atlas (`aura-atlas-v1.png`) are the original Project Aura direction approved by the maintainer for public distribution, including their embedded AI provenance metadata. Private reference screenshots are not included. The reference rig PNGs are generated from the original drawing code in `tools/create_reference_rig.py`.

The two tour WAVs are **synthetic program assets**, not microphone recordings, loopback captures or audio-meter diagnostics. `tools/create_tour_audio.py` generates the seven fixed narration lines in `aura/showcase.py` using installed Windows text-to-speech, then mixes mathematically synthesized rotor, rocket, impact and magic effects with a fixed random seed. `tour-narration.json` contains the exact narration text and timing.

On 2026-09-06 both WAVs were regenerated silently into an isolated folder on the development host. Each was byte-for-byte identical to the release asset:

| Asset | SHA-256 |
| --- | --- |
| tour-audio.wav | `2e07f1d1f11070fc6cf7c6ac96feef8b8f90b244c7993b619a2b810520352f4d` |
| tour-voice.wav | `f14eb8ba03d7830266f99e484111e90f467c5dae81a130eb346d94a860c30ae3` |

A different installed voice can produce different synthesized audio; normal playback uses these included assets. The demo MP4 is exported from the same local performance renderer and synthetic mix. Diagnostic files under `artifacts/` are excluded from repository source publication.
