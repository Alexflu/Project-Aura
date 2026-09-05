# Contributing to Project Aura

Project Aura has a first local Windows tester beta. Feedback on avatar interaction, adaptation, accessibility, ChatGPT connectivity and clean-machine setup is welcome.

Before implementing a substantial feature, describe the user experience, the component it belongs to, and the smallest demonstrable outcome in an issue. Identify any application, hardware, or platform dependencies.

Keep proposed changes focused. Explain what changed and how it was checked. Distinguish working features from mockups and future plans. Do not include credentials, private scans, workplace data, or assets you do not have permission to share.

Contributions to this repository are made under its [MIT License](LICENSE).

Run `python -m unittest discover -s tests -v` before submitting changes; install `requirements-mcp.txt` to include the real protocol test. For UI changes run `python tools/gui_smoke.py` and inspect each tab. Include your OS, Python version and actual client version in compatibility reports. Use a temporary `--data` path for destructive tests. Do not attach your real preference database.
