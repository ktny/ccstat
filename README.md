# ccmonitor

Claude Session Timeline - CLI tool for visualizing Claude session activity patterns

## Overview

`ccmonitor` is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format. It reads information from Claude Code log files (~/.claude/projects/) and analyzes and displays activity patterns and active time for each project.

## Features

- 📊 **Project Activity Display**: Visual timeline display of each project's activity status
- 🕒 **Active Time Calculation**: Automatic calculation of actual work time based on message intervals
- 📈 **Activity Density Visualization**: Color-coded display based on activity density
- 🗂️ **Project Integration**: Automatic project grouping by Git repository
- 🧵 **Worktree Display**: Hierarchical display of different directories within the same repository
- 📅 **Period Filter**: Display activity history for specified number of days or hours
- 🔍 **Project Filter**: Display only specific projects

## Installation

### Development Environment Setup with uv (Recommended)

```bash
# Install uv (first time only)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# Install dependencies
uv sync

# Development install (editable mode)
uv pip install -e .
```

### Using pip

```bash
# Clone repository
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# Install dependencies
pip install -r requirements.txt

# Or development install
pip install -e .
```

## Usage

### Basic Usage

```bash
# Display activity for the last 1 day (default)
ccmonitor

# Display activity for the last 7 days
ccmonitor --days 7
ccmonitor -d 7

# Display activity for the last 6 hours
ccmonitor --hours 6
ccmonitor -t 6

# Filter display by specific project
ccmonitor --project myproject
ccmonitor -p myproject

# Worktree display (separate directories within the same repository)
ccmonitor --worktree
ccmonitor -w

# Multiple option combinations
ccmonitor --days 3 --project myproject --worktree
ccmonitor -d 3 -p myproject -w

# Display help
ccmonitor --help
ccmonitor -h

# Display version
ccmonitor --version
ccmonitor -v
```

### Display Content Explanation

#### Project Activity Table
- **Project**: Project name (Git repository name or directory name)
- **Timeline**: Chronological activity status (color-coded by activity density)
- **Events**: Number of messages in session
- **Duration**: Active work time (in minutes)

#### Activity Density Color Coding
- ■ (bright black): Low activity
- ■ (green): Moderate activity
- ■ (yellow-orange): High activity
- ■ (red): Very high activity

#### Time Axis
- Hours display: Minute/hour intervals (15min, 30min, 1h, 2h, 3h, 4h based on range)
- Single day display: Hour intervals (0, 6, 12, 18 hours)
- Multiple days display: Date intervals

### Active Time Calculation

Only time periods where message intervals are within 1 minute are calculated as active time. Long breaks are excluded, measuring only actual work time.

## Development

### Development Commands

```bash
# Code formatting and linting
uv run ruff check .       # Lint check
uv run ruff check . --fix # Auto-fix
uv run ruff format .      # Code formatting

# Type checking
uv run pyright

# Test execution
uv run pytest                    # Run all tests
uv run pytest -v               # Verbose output
uv run pytest --cov=ccmonitor  # With coverage

# Run single test file
uv run pytest tests/test_claude_logs.py

# Run ccmonitor in development environment
uv run ccmonitor
uv run ccmonitor -d 7 -w
```

### Architecture

```
ccmonitor/
├── __main__.py          # Entry point
├── timeline_monitor.py  # Main monitoring and control logic
├── claude_logs.py       # Claude log file analysis
├── timeline_ui.py       # Rich UI display components
├── git_utils.py         # Git repository information retrieval
└── utils.py            # Utility functions
```

#### Major Components
- **claude_logs.py**: Analyzes JSONL files in `~/.claude/projects/` and extracts session information
- **timeline_ui.py**: Beautiful terminal display using Rich library
- **git_utils.py**: Retrieves Git repository information for directories and groups projects

### Data Sources

ccmonitor reads data from the following files:
- `~/.claude/projects/*/**.jsonl`: Claude Code session logs
- Each JSONL file contains timestamps, session IDs, working directories, message content, etc.

## Requirements

- Python 3.12+
- Claude Code (for log file generation)
- Git (recommended for project integration functionality)

## License

This project is published under the MIT License.