# Updates when Aura opens

Starting with 0.7.0-beta.4, the packaged Windows desktop checks the official
Alexflu/Project-Aura GitHub releases when you open it. It includes newer beta
releases. There is no Windows startup registration, scheduled task, service,
or periodic background check. Launching a second copy of an already running
profile opens its existing Studio without checking again.

The small update window can be cancelled with **Open installed version now**.
Offline, rate-limited or invalid responses leave the installed app usable.
In **Controls → Menu → Studio → Your data**, uncheck **Check for updates when
Aura opens** to disable future network checks. Previously selected updates
remain selected. Source/developer launches never check automatically.

## Installation and recovery

The first updater-enabled release needs one manual download and extraction.
Keep that folder and your usual shortcut. Future updates are staged under
`%LOCALAPPDATA%\ProjectAura\updates`, not written over your original folder.
The launcher opens the selected newer copy. The downloaded ZIP is checked
against its official release size and SHA-256 manifest, its paths and expansion
size are validated, and its desktop must pass a startup self-check before the
selection changes. Profile files and imported models stay in their existing
locations. Failed checks do not replace the active version.

The beta 4 `bridge/AuraMCP.exe` launcher follows the selected version locally,
without making an update request. A running bridge keeps its current process
until the MCP client reconnects. Older bridge paths need to be changed once to
the beta 4 bridge; no changes are required for subsequent compatible releases.

To recover from a later runtime problem, launch the original executable with
`--skip-update`; this bypasses both the check and redirection for that launch.
Close Aura and its MCP connection before removing `active.json` from the update
folder to clear the selected update. No previous release folders are deleted
automatically, so this first updater can use additional disk space. Failed or
interrupted updates may leave unused staging folders after an abrupt shutdown.

The startup check detects launch failures, not every possible runtime bug.
Releases remain unsigned. HTTPS and the release manifest protect the download
route and integrity; they are not an independent publisher signature or a
guarantee against a compromised publishing account. Only the fixed official
repository is accepted; alternate update servers and downgrade updates are not
supported.

## Privacy

GitHub and its download infrastructure receive the normal connection information
(such as IP address and the updater user agent). The updater sends no interests,
speech, model files, profile contents, bank details or credentials. There is no
telemetry submission. The update preference and selected release are stored
locally and are shared by this Windows user's Aura profiles.
