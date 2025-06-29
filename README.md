# 📊 ccmonitor

> Visualize your Claude Code session activity patterns — fast, beautiful, and insightful!

![Go](https://img.shields.io/badge/go-%2300ADD8.svg?style=for-the-badge&logo=go&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/ktny/ccmonitor?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/ktny/ccmonitor/total?style=for-the-badge)

## ✨ What is ccmonitor?

ccmonitor is a powerful CLI tool that analyzes your Claude Code session history and transforms it into beautiful timeline visualizations. Track your coding patterns, monitor token usage, and gain insights into your development workflow.

### 🎯 Key Features

- 📈 **Timeline Visualization** — Color-coded activity blocks showing your coding patterns
- ⏱️ **Smart Duration Tracking** — Calculates active work time with intelligent break detection
- 🎨 **Activity Density** — Five-level visual density indicators from idle to very high
- 📁 **Git Integration** — Automatically groups projects by repository
- 🌳 **Worktree Support** — Separate visualization for different worktree directories
- 📊 **Token Analytics** — Track input/output token usage across projects
- 🕐 **Flexible Time Ranges** — View activity by days (1+) or hours (1-24)
- 🔍 **Project Filtering** — Focus on specific projects
- ⚡ **High Performance** — Optimized file processing for fast results

## 🚀 Installation

### Option 1: Download Pre-built Binary (Recommended)

Download the latest release binary for your platform from [GitHub Releases](https://github.com/ktny/ccmonitor/releases):

```bash
# Linux (x86_64)
wget https://github.com/ktny/ccmonitor/releases/download/v0.1.0/ccmonitor-v0.1.0-linux-amd64
chmod +x ccmonitor-v0.1.0-linux-amd64
sudo mv ccmonitor-v0.1.0-linux-amd64 /usr/local/bin/ccmonitor

# macOS (Apple Silicon)
wget https://github.com/ktny/ccmonitor/releases/download/v0.1.0/ccmonitor-v0.1.0-darwin-arm64
chmod +x ccmonitor-v0.1.0-darwin-arm64
sudo mv ccmonitor-v0.1.0-darwin-arm64 /usr/local/bin/ccmonitor

# macOS (Intel)
wget https://github.com/ktny/ccmonitor/releases/download/v0.1.0/ccmonitor-v0.1.0-darwin-amd64
chmod +x ccmonitor-v0.1.0-darwin-amd64
sudo mv ccmonitor-v0.1.0-darwin-amd64 /usr/local/bin/ccmonitor

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/ktny/ccmonitor/releases/download/v0.1.0/ccmonitor-v0.1.0-windows-amd64.exe" -OutFile "ccmonitor.exe"
```

### Option 2: Go Install (Latest Stable)

```bash
go install github.com/ktny/ccmonitor/cmd/ccmonitor@v0.1.0
```

### Option 3: Build from Source

```bash
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor
make build
./bin/ccmonitor
```

### Option 4: Development Installation

```bash
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor
make install  # Installs to $GOPATH/bin
```

## 📖 Usage

### Basic Commands

```bash
# View last 24 hours of activity
ccmonitor

# View last 7 days
ccmonitor --days 7

# View last 6 hours
ccmonitor --hours 6
# or using short option
ccmonitor -H 6

# Filter by specific project
ccmonitor --project myproject

# Show worktree view (separate repos)
ccmonitor --worktree

# Combine options
ccmonitor --days 3 --project ccmonitor --worktree
```

### Understanding the Output

#### 📊 Project Activity Table
- **Project**: Git repository name or directory name
- **Timeline**: Visual activity timeline with color-coded density
- **Events**: Number of messages in the session
- **Tokens**: Input/Output token usage statistics
- **Duration**: Active work time in minutes

#### 🎨 Activity Color Coding
- **■** (gray): Minimal activity
- **■** (green): Low activity  
- **■** (yellow): Moderate activity
- **■** (orange): High activity
- **■** (red): Very high activity

#### ⏰ Time Axis Display
- **Hours view**: 15min/30min/1h/2h/3h/4h intervals
- **Single day**: Hour markers (0, 6, 12, 18)
- **Multiple days**: Date intervals

### 🧠 Smart Features

**Active Time Calculation**: Only counts periods where message intervals are ≤1 minute as active time, excluding long breaks to measure actual work time.

**Git Integration**: Automatically detects and groups projects by Git repository, showing parent-child relationships for complex project structures.

## 📋 Requirements

- **Go 1.21+** for building from source
- **Claude Code** for generating session logs
- **Git** (recommended) for project integration features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for the Claude Code community</sub>
</div>