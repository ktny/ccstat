# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ccstat is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

**Implementation**: TypeScript - Modern, feature-rich implementation with React-based terminal UI.

### Key Features

- Parses session information from Claude Code log files (~/.claude/projects/)
- Visualizes project activity patterns in timeline format
- Automatically calculates active time based on message intervals (5-minute threshold)
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

## Command Reference

```bash
# Basic execution (last 1 day)
npx @ktny/ccstat
# or if installed globally
ccstat

# Display activity for the last N days
ccstat --days 7

# Display activity for the last N hours
ccstat --hours 6

# Show all session history across all time periods
ccstat --all-time

# Filter by project names (space-separated)
ccstat --project project1 project2

# Sort by different fields with optional reverse order
ccstat --sort project --reverse
ccstat --sort events
ccstat --sort duration
ccstat --sort timeline  # default

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

### Development Commands

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

## Architecture

### Project Structure

```
src/
├── cli/              # CLI entry point
│   └── index.ts     # Main CLI definition
├── core/            # Core business logic
│   ├── parser/      # Claude log parsing
│   └── git/         # Git integration
├── ui/              # UI components (Ink)
│   ├── App.tsx
│   ├── ProjectTable.tsx
│   └── components/  # UI components
├── models/          # Type definitions
│   └── events.ts
└── utils/           # Utilities
```

### Major Components

- **CLI**: Commander.js for argument parsing
- **UI**: Ink (React-like) for terminal interfaces
- **Parser**: JSONL parsing with event filtering and parallel processing
- **Git**: simple-git for repository integration
- **Models**: Zod schemas for type validation

## Development Guidelines

### Code Quality and Formatting

- **MANDATORY**: Run `npm run check` before committing
- **MANDATORY**: All ESLint warnings must be fixed
- Use TypeScript strict mode
- Follow React/Ink patterns for UI components
- Use Zod for runtime type validation

### Testing

- Run `npm run test` to execute all tests
- Use Jest for unit testing
- Test components using Ink testing utilities
- Follow test-driven development where possible

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

# Ensure all quality checks pass
npm run check

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

## Configuration and Data Sources

### Input Data

ccstat reads Claude Code session logs from:

- `~/.claude/projects/*/*.jsonl` (primary)
- `~/.config/claude/projects/*/*.jsonl` (fallback)

### Data Format

The application parses JSONL format:

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
- **Assets**: Shared assets (logos, documentation) in project root

### CI/CD

- **Main CI**: Tests TypeScript implementation (`.github/workflows/ci.yml`)
- **Release CI**: Automated npm publishing (`.github/workflows/release.yml`)
- Runs on pushes and PRs affecting code

## Release Management

### Automated Release Process

This project uses **semantic-release** for automated versioning and npm publishing:

#### Release Configuration

- **File**: `.releaserc.json`
- **Trigger**: Git tags pushed to repository (`v*`)
- **Workflow**: `.github/workflows/release.yml`

#### Release Steps

1. **Tag Creation**: Push a tag to trigger release

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Automated Process**:
   - Analyzes commit messages using Conventional Commits
   - Determines next version (major/minor/patch)
   - Updates package.json version
   - Publishes to npmjs.com
   - Creates GitHub release
   - Generates/updates CHANGELOG.md

#### Conventional Commits

Follow these patterns for automatic versioning:

```bash
# Patch version (1.0.0 → 1.0.1)
git commit -m "fix: resolve issue description"

# Minor version (1.0.0 → 1.1.0)
git commit -m "feat: add new feature"

# Major version (1.0.0 → 2.0.0)
git commit -m "feat!: breaking change"
# or
git commit -m "feat: add feature

BREAKING CHANGE: describe breaking change"
```

#### Prerequisites

- **NPM_TOKEN**: Set in GitHub repository secrets for npm publishing
- **Proper commit messages**: Follow Conventional Commits format
