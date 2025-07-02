# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ccstat is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

**Implementation**: Go (primary and recommended for all development)

### Key Features
- Parses session information from Claude Code log files (~/.claude/projects/)
- Visualizes project activity patterns in timeline format
- Automatically calculates active time based on message intervals (3-minute threshold)
- Automatically integrates and groups projects by Git repository

## Development Environment Setup

### Go Development

```bash
# Build the project
make build

# Or build manually
go build -o bin/ccstat ./cmd/ccstat

# Install to $GOPATH/bin
make install
```

## Command Reference

### Execution Commands

```bash
# Basic execution (last 1 day)
./bin/ccstat

# Display activity for the last N days
./bin/ccstat --days 7

# Display activity for the last N hours
./bin/ccstat --hours 6
# or using short option
./bin/ccstat -H 6

# Worktree display (separate directories within the same repository)
./bin/ccstat --worktree

# Using Makefile shortcuts
make run        # Build and run with defaults
make run-days   # Build and run with --days 2
make run-hours  # Build and run with -H 6

# Display help
./bin/ccstat --help
```

### Development Commands

```bash
# Code formatting (ALWAYS run before committing)
go fmt ./...

# Code linting
golangci-lint run

# Build and test
make build
make test

# Run ccstat in development environment  
make run
make run-days   # --days 2
make run-hours  # --hours 6

# Clean build artifacts
make clean

# Run specific tests
go test ./cmd/ccstat/
go test ./internal/claude/
```

## Architecture

### Core Structure
```
ccstat/
├── cmd/ccstat/              # Main application entry point
│   ├── main.go             # CLI interface & main execution logic
│   └── main_test.go        # Basic integration tests
├── internal/               # Internal packages (not importable externally)
│   ├── claude/            # Claude log parsing & session analysis
│   │   ├── parser.go      # Core JSONL parsing & session grouping
│   │   └── parser_test.go # Unit tests for parser
│   ├── git/               # Git repository utilities
│   │   └── utils.go       # Git config parsing & repo name extraction
│   └── ui/                # User interface & visualization
│       └── table.go       # Terminal UI using lipgloss
├── pkg/models/            # Shared data models
│   └── events.go          # SessionEvent & SessionTimeline structs
└── Makefile              # Build automation
```

### Major Components

#### cmd/ccstat/main.go - CLI Entry Point
- Uses Cobra for CLI argument parsing
- Handles flags: --days, --hours, --worktree, --version, --debug
- Orchestrates the main data flow: parse CLI → load sessions → create UI → display

#### internal/claude/parser.go - Log Analysis Engine
- Parses Claude Code session logs (~/.claude/projects/*/*.jsonl)
- `ParseJSONLFile()`: Parses individual JSONL files with large buffer support
- `LoadSessionsInTimeRange()`: Main orchestrator for loading & filtering
- `CalculateActiveDuration()`: Smart duration calculation with 3-minute inactivity threshold
- `groupEventsByProject()`: Groups events by Git repository or directory

#### internal/git/utils.go - Git Integration
- Parses `.git/config` to extract repository names
- Handles both regular repos and git worktrees
- Supports SSH and HTTPS Git URLs with fallback to directory names

#### internal/ui/table.go - Terminal UI
- Uses Charmbracelet Lipgloss for styled terminal output
- Creates timeline visualization with 5-level activity density colors
- Adaptive time axis (15min intervals to yearly depending on range)
- Responsive design that adapts to terminal width

#### pkg/models/events.go - Data Models
- `SessionEvent`: Individual message events with timestamp, directory, content, etc.
- `SessionTimeline`: Aggregated timeline per project with events, duration, start/end times
- Supports parent-child project relationships for hierarchical display

### Data Flow
1. CLI parsing with Cobra processes command-line arguments
2. File discovery scans `~/.claude/projects/` for JSONL files
3. JSONL parsing extracts events with timestamp filtering
4. Project grouping by Git repository (consolidated or worktree mode)
5. Active duration calculation and event statistics
6. Terminal UI creation with colored timeline visualization
7. Styled output to terminal

### Key Algorithms

#### Active Duration Calculation
- Only counts time between consecutive events ≤ 3 minutes as active
- Excludes long breaks (> 3 minutes) to measure actual work time
- Minimum 5 minutes for single events
- Provides realistic work time estimates

#### Project Grouping Logic
- **Default Mode**: Consolidates all directories within same Git repo
- **Worktree Mode**: Shows parent-child relationships for complex repos
- **Repository Detection**: Uses Git config parsing with fallback to directory names

#### Timeline Visualization
- Maps event count to 5-level color scale for activity density
- Automatically selects appropriate time intervals based on range
- Character-based timeline bars using `■` symbols with color coding

### Important Dependencies
- **github.com/spf13/cobra**: CLI framework
- **github.com/charmbracelet/lipgloss**: Terminal styling
- **github.com/muesli/reflow**: Text wrapping utilities
- **golang.org/x/term**: Terminal size detection

### Configuration and Data Sources
- **Input Data**: `~/.claude/projects/*/*.jsonl` (Claude Code session logs)
- **Data Format**: Each line is a JSON event (timestamp, sessionId, cwd, message, usage, etc.)

## Development Guidelines

### Code Quality and Formatting
- **MANDATORY**: Always run `go fmt ./...` before committing any Go code
- **MANDATORY**: Run `golangci-lint run` and fix all issues before committing
- Follow Go standard conventions for naming, structure, and documentation
- Use meaningful package and variable names
- Add comments for exported functions and types

### Testing
- Run `go test ./...` to execute all tests
- Follow table-driven test patterns as seen in existing tests
- Add tests for new functionality, especially core parsing logic
- Test files follow `*_test.go` naming convention

### Project Integration Logic
- Groups same projects by detecting Git repositories
- With --worktree option, displays directories separately even within the same repository
- Shows parent-child relationships (└─ indicates child projects)

### Pull Request Guidelines

#### Creating Pull Requests
- **Always create separate branches for different features/fixes**
- Use descriptive branch names: `feat/feature-name`, `fix/issue-description`, `setup/tool-configuration`
- Ensure all linting and formatting checks pass before creating PR
- Write clear commit messages explaining the "why" not just the "what"
- Include relevant tests for new functionality

#### Branch Workflow
```bash
# Create a new feature branch
git checkout -b feat/new-feature

# Make changes and ensure formatting
go fmt ./...
golangci-lint run

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push and create PR
git push -u origin feat/new-feature
gh pr create --title "Add new feature" --body "Description of changes"
```

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

