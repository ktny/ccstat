# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 💔 Breaking Changes
- **Project Rename**: `ccmonitor` → `ccstat` for better branding and clarity
  - Binary name changed from `ccmonitor` to `ccstat`
  - Module path changed from `github.com/ktny/ccmonitor` to `github.com/ktny/ccstat`
  - CLI command changed from `ccmonitor` to `ccstat`
  - Installation commands updated accordingly

### 📝 Documentation
- Updated all references from ccmonitor to ccstat in README and documentation
- Updated installation instructions with new binary names and URLs

## [0.1.0] - 2025-06-29

### 🎉 Initial Release

This is the first official release of ccmonitor, a CLI tool for visualizing Claude Code session activity patterns.

### ✨ Features

#### Core Functionality
- **Timeline Visualization** - Beautiful color-coded activity blocks showing coding patterns
- **Smart Duration Tracking** - Calculates active work time with intelligent break detection (1-minute threshold)
- **Activity Density Indicators** - Five-level visual density from idle to very high activity
- **Token Analytics** - Track input/output token usage across projects

#### Project Management
- **Git Integration** - Automatically groups projects by repository
- **Worktree Support** - Separate visualization for different worktree directories  
- **Project Filtering** - Focus on specific projects with `--project` flag
- **Parent-Child Relationships** - Visual indication of project hierarchies

#### Time Range Options
- **Flexible Time Ranges** - View activity by days (1+) or hours (1-24)
- **Intelligent Time Axis** - Adaptive time formatting:
  - 1-2 hours: 15-minute intervals with HH:MM format
  - 3-4 hours: 30-minute intervals with HH:MM format
  - 5-8 hours: 1-hour intervals with HH:MM format
  - 9-12 hours: 2-hour intervals with HH format
  - Longer periods: Daily/weekly/monthly formats

#### User Interface
- **Terminal Width Adaptation** - Responsive layout that uses full console width
- **Dynamic Column Widths** - Project, Events, and Duration columns adjust based on content
- **Rich Color Coding** - Activity density visualization with 5-color gradient
- **Clean Typography** - Beautiful terminal output using lipgloss styling

#### Performance & Reliability
- **High Performance** - Optimized file processing for fast results
- **Robust Error Handling** - Graceful handling of missing or corrupted session files
- **Cross-Platform** - Works on Linux, macOS, and Windows

### 🛠️ Technical Details

#### Installation Methods
- Build from source with `make build`
- Direct installation via `go install github.com/ktny/ccmonitor/cmd/ccmonitor@latest`
- Makefile-based installation to `$GOPATH/bin`

#### Command Line Interface
```bash
ccmonitor [flags]

Flags:
  -d, --days int       Number of days to look back (default: 1)
  -H, --hours int      Number of hours to look back (1-24, overrides --days)
  -p, --project string Filter by specific project
  -w, --worktree       Show projects as worktree (separate similar repos)
  -v, --version        Show version information
      --debug          Enable debug output for troubleshooting
```

#### Data Sources
- Reads Claude Code session logs from `~/.claude/projects/`
- Parses JSONL format session files
- Extracts timestamp, token usage, and project information

### 📋 Requirements

- Go 1.21+ for building from source
- Claude Code for generating session logs
- Git (recommended) for project integration features

### 🏗️ Architecture

- **Go-based implementation** - Primary development focus
- **Python legacy version** - Maintained for compatibility
- **Modular design** - Clean separation of concerns:
  - `internal/claude/` - Session data parsing and processing
  - `internal/ui/` - Terminal UI rendering with lipgloss
  - `pkg/models/` - Data models and structures
  - `cmd/ccstat/` - CLI interface and main application

[0.1.0]: https://github.com/ktny/ccstat/releases/tag/v0.1.0