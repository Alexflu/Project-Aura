# Third-party components

Project Aura's source and original procedural avatar artwork are MIT licensed; see LICENSE.

The portable Windows desktop bundles Python and Tcl/Tk, including their standard-library components and runtime libraries. Their license notices are in `licenses/` and the bundled runtime. Python is under the Python Software Foundation license; Tcl/Tk uses its own permissive license. PyInstaller builds the executable using its GPL license with the bootloader exception, which allows distribution of non-GPL applications. Preserve these notices when redistributing the portable build.

The optional MCP adapter uses the official `mcp` Python SDK (MIT) and its transitive dependencies. They are installed separately, are not bundled in the desktop executable, and retain their individual licenses. `requirements-mcp.txt` pins the SDK; `requirements-lock.txt` records the tested Windows environment including build/test tools. Review dependency licenses and advisories before changing or redistributing it.

No proprietary game characters, commercial avatar packs, OpenAI logos, or downloaded likenesses are included. Project Aura is not affiliated with or endorsed by OpenAI.
