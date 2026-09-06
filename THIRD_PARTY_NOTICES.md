# Third-party components

Project Aura's source and original procedural avatar artwork are MIT licensed; see LICENSE.

The portable Windows desktop bundles Python and Tcl/Tk, including their standard-library components and runtime libraries. Their license notices are in `licenses/` and the bundled runtime. Python is under the Python Software Foundation license; Tcl/Tk uses its own permissive license. PyInstaller builds the executable using its GPL license with the bootloader exception, which allows distribution of non-GPL applications. Preserve these notices when redistributing the portable build.

The optional MCP adapter uses the official `mcp` Python SDK (MIT) and its transitive dependencies. They are bundled in the separate bridge/AuraMCP.exe distribution, and retain their individual licenses in licenses/. Source users install them separately. `requirements-mcp.txt` pins the SDK; `requirements-lock.txt` records the tested Windows environment including build/test tools. Review dependency licenses and advisories before changing or redistributing it.

No proprietary game characters, commercial avatar packs, OpenAI logos, or downloaded likenesses are included. Project Aura is not affiliated with or endorsed by OpenAI.

The illustrated sprite atlas and concept sheet were generated with OpenAI image generation from the user-approved original Aura direction. Reference screenshots are not redistributed. These are early animation assets, not a rigged 3D model.

The desktop now bundles Pillow (HPND license) for sprite rendering; see licenses/Pillow-LICENSE.txt and the Pillow distribution notices.

Local speech uses the Windows-installed System.Speech assembly and installed voices; these are not redistributed in the ZIP.

The optional tour includes synthetic narration rendered through an installed Windows voice and original mathematically synthesized effects. Voice engines and Windows font files are not bundled. The developer-only video exporter uses imageio-ffmpeg; no FFmpeg executable is shipped in the beta.

The tray uses pystray 0.19.5 (LGPLv3). Its exact unmodified Python sources, GPL/LGPL notices and rebuild instructions are included under licenses/pystray/. Application audio metering uses pycaw and comtypes (MIT), psutil (BSD) and six (MIT); their distribution notices are included in licenses/.
