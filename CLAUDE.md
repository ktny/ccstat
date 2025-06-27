# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ccmonitor is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

### Key Features
- Parses session information from Claude Code log files (~/.claude/projects/)
- Visualizes project activity patterns in timeline format
- Aggregates and displays Input/Output token usage by project
- Automatically calculates active time based on message intervals (1-minute threshold)
- Automatically integrates and groups projects by Git repository

## Development Environment Setup

```bash
# Install uv (first time only)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Development install (editable mode)
uv pip install -e .
```

## Command Reference

### Execution Commands
```bash
# Basic execution (last 1 day)
ccmonitor

# Display activity for the last N days
ccmonitor --days 7

# Filter display by specific project
ccmonitor --project myproject

# Worktree display (separate directories within the same repository)
ccmonitor --worktree

# Multiple option combinations
ccmonitor --days 3 --project myproject --worktree

# Display help
ccmonitor --help
```

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
uv run pytest tests/test_claude_logs.py::TestCalculateActiveDuration

# Run ccmonitor in development environment
uv run ccmonitor
uv run ccmonitor --days 7 --worktree
```

## Architecture

### Core Structure
```
ccmonitor/
├── __main__.py          # Entry point
├── timeline_monitor.py  # Main monitoring and control logic
├── claude_logs.py       # Claude log file analysis
├── timeline_ui.py       # Rich UI display components
├── git_utils.py         # Git repository information retrieval
└── utils.py            # Utility functions (removed)
```

### Major Components

#### claude_logs.py - Log Analysis Engine
- Parses Claude Code session logs (~/.claude/projects/**.jsonl)
- `SessionEvent`: Individual message events (timestamp, tokens, content, etc.)
- `SessionTimeline`: Session aggregation by project (total tokens, active duration, etc.)
- `calculate_active_duration()`: Active time calculation with 1-minute threshold
- `calculate_token_totals()`: Input/output token aggregation

#### timeline_ui.py - UI Display Layer
- Beautiful terminal display using Rich library
- Project Activity table: Project name, timeline visualization, Events count, Input/Output tokens, Duration
- Activity density color coding (low activity → high activity with increasing color intensity)
- Time axis display (hourly for single day, daily for multiple days)

#### timeline_monitor.py - Control Layer
- CLI option processing (--days, --project, --worktree)
- Log loading process control and UI display management
- Project filtering functionality

#### git_utils.py - Project Integration
- Retrieves Git repository information for directories
- Integrates and groups different directories within the same repository as projects

### Data Flow
1. `timeline_monitor.py` parses CLI options
2. `claude_logs.py` loads JSONL files from ~/.claude/projects/
3. Parses session events and extracts token and timestamp information
4. `git_utils.py` performs project integration and grouping
5. Executes active time and token aggregation
6. `timeline_ui.py` provides visualization and display using Rich

### Important Dependencies
- **Rich**: Beautiful terminal UI (tables, color coding, panels)
- **Click**: Command-line argument processing
- **pathlib/json**: Log file loading and parsing

### Configuration and Data Sources
- **Input Data**: `~/.claude/projects/*/*.jsonl` (Claude Code session logs)
- **Data Format**: Each line is a JSON event (timestamp, sessionId, cwd, message, usage, etc.)
- **Token Information**: Extracts `input_tokens` and `output_tokens` from the `usage` field of assistant messages

### Active Time Calculation Logic
- Only counts time as active when message intervals are within 1 minute
- Excludes long breaks (>1 minute), measuring only actual work time
- Treats single events as a minimum of 5 minutes

## Development Guidelines

### TDD (Test-Driven Development)
- Follow test-driven development principles
- Create tests first when adding new features, then implement
- Update related tests first when modifying existing features

### Token Information Handling
- cache_creation_input_tokens and cache_read_input_tokens are not included in input_tokens
- Only assistant messages have token information (user messages are 0)
- Token display uses thousands separators (1,000 format), displays "-" for 0

### Project Integration Logic
- Groups same projects by detecting Git repositories
- With --worktree option, displays directories separately even within the same repository
- Shows parent-child relationships (└─ indicates child projects)

## Custom Commands

### `/project:worktree-task`
A custom slash command that creates a new branch with git worktree under `.worktree` and creates a PR after task completion.

#### Usage
1. Execute `/project:worktree-task`
2. Input task description
3. A new worktree branch is automatically created
4. Provide implementation instructions
5. After completion, automatically executes commit, push, and PR creation

#### Prerequisites
- GitHub CLI must be set up
- Must have push permissions to remote repository

#### Directory Structure
```
.worktree/
├── feat-task-name-1221-1430/  # Each task's worktree directory
└── .gitignore                 # .worktree/ is already added to .gitignore
```