# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ccstat is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

**Available Implementations**:

- **TypeScript** (primary): Modern, feature-rich implementation in project root
- **Go** (secondary): High-performance implementation in `/go` directory

**Development Priority**: TypeScript version is the main implementation and should be prioritized for new features and development.

### Key Features

- Parses session information from Claude Code log files (~/.claude/projects/)
- Visualizes project activity patterns in timeline format
- Automatically calculates active time based on message intervals (5-minute threshold for TypeScript, 3-minute for Go)
- Automatically integrates and groups projects by Git repository

## Development Environment Setup

### TypeScript Development (Primary)

```bash
# Install dependencies
npm ci

# Run in development mode
npm run dev

# Build the project
npm run build

# Run tests and quality checks
npm run check
```

### Go Development (Secondary)

```bash
# Build the project (from /go directory)
cd go && make build

# Or build manually
cd go && go build -o bin/ccstat ./cmd/ccstat

# Install to $GOPATH/bin
cd go && make install
```

## Command Reference

### TypeScript Version Commands

```bash
# Basic execution (last 1 day)
npx @ktny/ccstat
# or if installed globally
ccstat

# Display activity for the last N days
ccstat --days 7

# Display activity for the last N hours
ccstat --hours 6

# Worktree display (separate directories within the same repository)
ccstat --worktree

# Development commands
npm run dev           # Run in development mode
npm run dev:days      # Run with --days 2
npm run dev:hours     # Run with --hours 6
npm run build         # Build for production
npm run test          # Run tests
npm run check         # Run all quality checks
```

### Go Version Commands

```bash
# Basic execution (last 1 day) - from /go directory
./bin/ccstat

# Display activity for the last N days
./bin/ccstat --days 7

# Display activity for the last N hours
./bin/ccstat --hours 6
# or using short option
./bin/ccstat -H 6

# Worktree display (separate directories within the same repository)
./bin/ccstat --worktree

# Using Makefile shortcuts (from /go directory)
make run        # Build and run with defaults
make run-days   # Build and run with --days 2
make run-hours  # Build and run with -H 6

# Display help
./bin/ccstat --help
```

### Development Commands

#### TypeScript Version

```bash
# Code formatting and linting
npm run format
npm run lint
npm run lint:fix

# Type checking
npm run type-check

# Build and test
npm run build
npm run test

# Run specific tests
npm run test -- --testNamePattern="parser"

# Clean build artifacts
npm run clean
```

#### Go Version

```bash
# Code formatting (ALWAYS run before committing)
cd go && go fmt ./...

# Code linting
cd go && golangci-lint run

# Build and test
cd go && make build
cd go && make test

# Run specific tests
cd go && go test ./cmd/ccstat/
cd go && go test ./internal/claude/

# Clean build artifacts
cd go && make clean
```

## Architecture

### TypeScript Version Structure

```
src/
├── cli/              # CLI entry point
│   └── index.ts     # Main CLI definition
├── core/            # Core business logic
│   ├── analyzer/    # Session analysis
│   ├── parser/      # Claude log parsing
│   └── git/         # Git integration
├── ui/              # UI components (Ink)
│   ├── App.tsx
│   └── ProjectTable.tsx
├── models/          # Type definitions
│   └── events.ts
└── utils/           # Utilities
```

### Go Version Structure

```
go/
├── cmd/ccstat/              # Main application entry point
│   ├── main.go             # CLI interface & main execution logic
│   └── main_test.go        # Basic integration tests
├── internal/               # Internal packages
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

#### TypeScript Version

- **CLI**: Commander.js for argument parsing
- **UI**: Ink (React-like) for terminal interfaces
- **Parser**: JSONL parsing with event filtering
- **Git**: simple-git for repository integration
- **Models**: Zod schemas for type validation

#### Go Version

- **CLI**: Cobra for argument parsing
- **UI**: Lipgloss for styled terminal output
- **Parser**: Native Go JSONL parsing with concurrent processing
- **Git**: Native Git config parsing
- **Models**: Go structs for data representation

## Development Guidelines

### Code Quality and Formatting

#### TypeScript Version

- **MANDATORY**: Run `npm run check` before committing
- **MANDATORY**: All ESLint warnings must be fixed
- Use TypeScript strict mode
- Follow React/Ink patterns for UI components
- Use Zod for runtime type validation

#### Go Version

- **MANDATORY**: Always run `go fmt ./...` before committing any Go code
- **MANDATORY**: Run `golangci-lint run` and fix all issues before committing
- Follow Go standard conventions for naming, structure, and documentation
- Use meaningful package and variable names
- Add comments for exported functions and types

### Testing

#### TypeScript Version

- Run `npm run test` to execute all tests
- Use Jest for unit testing
- Test components using Ink testing utilities
- Follow test-driven development where possible

#### Go Version

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

# For TypeScript development
npm run check  # Ensure all quality checks pass

# For Go development
cd go && go fmt ./... && golangci-lint run

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

## Version Selection Guidelines

### When to Use TypeScript Version

- Default choice for most development
- UI/UX improvements
- New features development
- Cross-platform compatibility
- npm package distribution

### When to Use Go Version

- Performance-critical scenarios
- Large log file processing
- Memory-constrained environments
- Single binary distribution
- System integration

## Configuration and Data Sources

### Input Data

- **TypeScript**: `~/.claude/projects/*/*.jsonl` and `~/.config/claude/projects/*/*.jsonl`
- **Go**: `~/.claude/projects/*/*.jsonl`

### Data Format

Both versions parse the same JSONL format:

```json
{
  "timestamp": "2025-07-03T12:34:56.789Z",
  "sessionId": "session-123",
  "cwd": "/home/user/project",
  "message": "user message",
  "usage": { "input_tokens": 100, "output_tokens": 50 }
}
```

## Important Notes

### File Organization

- **TypeScript files**: Located in project root
- **Go files**: Located in `/go` directory
- Both versions maintain their own README.md files
- Shared assets (logos, documentation) in project root

### CI/CD

- **Main CI**: Tests TypeScript version (`.github/workflows/ci.yml`)
- **Go CI**: Tests Go version (`.github/workflows/go-ci.yml`)
- Both run on pushes and PRs affecting their respective code

### Development Focus

- **Primary development**: TypeScript version
- **Maintenance**: Go version receives bug fixes and critical updates
- **Feature parity**: Not required, each version can have unique features based on their strengths
