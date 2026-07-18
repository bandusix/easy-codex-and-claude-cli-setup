# Easy Codex and Claude CLI Setup
*Created by **[bandusix](https://github.com/bandusix)***

A foolproof, one-click GUI installer designed to set up the **Codex CLI** and **Claude Code CLI** across macOS and Windows with absolute zero configuration.

## 🚀 Features
- **True Cross-Platform**: Natively supports macOS (Apple Silicon M1/M2/M3 & Intel) and Windows (x64).
- **100% Offline Payload**: Bundles Node.js runtime, Claude Code NPM packages, and pre-compiled Codex binaries into a single executable. No network issues during installation!
- **Windows Codex Compilation**: Automatically compiles the missing Windows executable for Codex directly from source via GitHub Actions.
- **Zero Config**: Automatically manages PATH environments, symbolic links, and isolated directories without polluting your global system packages.

## 📥 Download & Install
Head over to the [Releases](https://github.com/bandusix/easy-codex-and-claude-cli-setup/releases) page to download the latest version:
- **macOS**: Download `AI_Tools_Installer_macOS.dmg`, double-click, and run the app.
- **Windows**: Download `AI_Tools_Installer_Windows.exe` and double-click.

## 🛠️ How It Works (For Developers)
This project uses **GitHub Actions** to automate the heavy lifting:
1. It downloads Node.js runtimes and Claude Code tarballs for all platforms.
2. It fetches the official pre-compiled Codex binaries for macOS.
3. It spins up a Windows runner, clones the Codex Rust repository, and compiles `codex.exe` from source.
4. Finally, it uses PyInstaller to package everything into a `.dmg` and `.exe` with a Tkinter GUI.

## 🤝 Contributing
Feel free to open issues or submit pull requests!

---
*Built with ❤️ for the AI developer community by bandusix.*
