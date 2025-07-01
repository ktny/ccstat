<div align="center">
  <img src="assets/logo.png" alt="ccstat logo" width="140" />
</div>

# ccstat

> Visualize your Claude Code session activity timeline — fast, beautiful, and insightful!

![Go](https://img.shields.io/badge/go-%2300ADD8.svg?style=for-the-badge&logo=go&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/ktny/ccstat?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/ktny/ccstat/total?style=for-the-badge)

## ✨ What is ccstat?

ccstat is a powerful CLI tool that analyzes your Claude Code session history and transforms it into beautiful timeline visualizations. Track your coding patterns and gain insights into your development workflow.

![demo](assets/demo.png)

### 🎯 Key Features

- 📈 **Timeline Visualization** — Color-coded activity blocks showing your coding patterns
- 📁 **Git Integration** — Automatically groups projects by repository
- 🕐 **Flexible Time Ranges** — View activity by days (1+) or hours (1-24)
- ⚡ **High Performance** — Optimized file processing for fast results

## 🚀 Installation

Install with a single command:

```bash
# Install latest version
curl -fsSL https://ktny.github.io/ccstat/install.sh | sh

# Install specific version
curl -fsSL https://ktny.github.io/ccstat/install.sh | sh -s -- --version v0.1.3
```

The installer automatically:
- Detects your OS and architecture
- Installs to `/usr/local/bin` (with sudo) or `~/.local/bin` (without sudo)

## 📖 Usage

### Basic Commands

```bash
# View last 24 hours of activity
ccstat

# View last 7 days
ccstat --days 7

# View last 6 hours
ccstat --hours 6

# Filter by specific project
ccstat --project myproject

# Show worktree view (separate repos)
ccstat --worktree

# Combine options
ccstat --days 3 --project myproject --worktree
```

## 🖥️ Supported Platforms

- Linux (x86_64, ARM64)
- macOS (Intel, Apple Silicon)
- **Note**: Windows is not currently supported

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for the Claude Code community</sub>
</div>
