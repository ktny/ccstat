# ccmonitor

Claude Session Timeline - CLI tool for visualizing Claude session activity patterns.

## Overview

ccmonitor analyzes Claude Code session logs and provides timeline visualization of project activity patterns with:
- Project-wise activity timeline with colored density indicators
- Input/Output token usage statistics by project  
- Active time calculation based on message intervals (3-minute threshold)
- Git repository-based project grouping and integration

## Features

- 📊 **Timeline Visualization**: Color-coded ■ blocks indicating activity levels
- 🕒 **Active Duration**: Calculated based on 3-minute inactive threshold  
- 📈 **Activity Density**: Five-level density visualization (idle to very high)
- 🗂️ **Project Grouping**: Automatic grouping by Git repository
- 🧵 **Worktree Support**: Separate display for different worktree directories
- 📅 **Flexible Time Ranges**: Days (1+) or hours (1-24) with adaptive time axis
- 🔍 **Project Filtering**: Display only specific projects
- ⚡ **Performance Optimized**: File modification time filtering for fast loading

## Installation

### Build from Source (Go)

```bash
# Clone the repository
git clone https://github.com/ktny/ccmonitor.git
cd ccmonitor

# Build binary
make build

# Or build manually
go build -o bin/ccmonitor ./cmd/ccmonitor
```

### Direct Installation

```bash
# Install to $GOPATH/bin
make install

# Or install manually
go install ./cmd/ccmonitor
```

### Legacy Python Version

```bash
# Using uv (recommended)
uv sync
uv run ccmonitor

# Using pip
pip install -e .
ccmonitor
```

## Usage

### Go Version (Recommended)

```bash
# Basic usage (last 1 day)
./bin/ccmonitor

# Specify time range
./bin/ccmonitor --days 7        # Last 7 days
./bin/ccmonitor --hours 6       # Last 6 hours (overrides --days)

# Filter by project
./bin/ccmonitor --project myproject

# Show worktree mode (separate similar repos)
./bin/ccmonitor --worktree

# Combine options
./bin/ccmonitor --days 3 --project ccmonitor --worktree

# Using Makefile shortcuts
make run        # Build and run with defaults
make run-days   # Build and run with --days 2  
make run-hours  # Build and run with --hours 6
```

### Python Version (Legacy)

```bash
# Display activity for the last 1 day (default)
uv run ccmonitor

# Display activity for the last 7 days
uv run ccmonitor --days 7

# Display activity for the last 6 hours  
uv run ccmonitor --hours 6

# Filter display by specific project
uv run ccmonitor --project myproject

# Worktree display (separate directories within the same repository)
uv run ccmonitor --worktree

# Multiple option combinations
uv run ccmonitor --days 3 --project myproject --worktree
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