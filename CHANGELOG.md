# Changelog

## v1.0.10
- Housekeeping release: commit messages from this point on no longer include an AI co-author trailer.

## v1.0.9
- Added a small, low-key credit line to the installer window ("Released under the MIT License · Copyright © 2026 bandusix"), clickable to open the license on GitHub.

## v1.0.8
- Added Gemini CLI, Kimi Code CLI, and Lark/Feishu CLI, bringing the installer to 5 supported tools.
- Refactored the shared Node.js runtime extraction so it only happens once regardless of how many Node-based tools are selected.

## v1.0.7
- Redesigned the installer UI: Fluent Design styling on Windows, macOS-native styling on macOS, hand-drawn on a Tkinter canvas.
- Added English / Simplified Chinese / Traditional Chinese support with automatic locale detection.
- Installation now runs on a background thread so the window stays responsive.

## v1.0.6
- Fixed GitHub release creation failing with a 403 by granting `contents: write` to the release job.

## v1.0.5
- Windows Codex CLI is now downloaded as a prebuilt binary from the official release instead of being compiled from source in CI, cutting Windows build time from ~30 minutes to under a minute.

## v1.0.0 – v1.0.4
- Initial releases: offline installer for Codex CLI and Claude Code CLI on macOS and Windows.
