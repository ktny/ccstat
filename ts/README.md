# ccstat (TypeScript Edition)

[![npm version](https://badge.fury.io/js/%40ktny%2Fccstat.svg)](https://badge.fury.io/js/%40ktny%2Fccstat)
[![TypeScript CI](https://github.com/ktny/ccstat/actions/workflows/typescript-ci.yml/badge.svg)](https://github.com/ktny/ccstat/actions/workflows/typescript-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

## ✨ Features

- 📊 **Timeline Visualization**: Interactive timeline showing project activity patterns
- 🔍 **Smart Analysis**: Automatically calculates active time based on message intervals (5-minute threshold)
- 🗂️ **Git Integration**: Automatically groups projects by Git repository
- 🌳 **Worktree Support**: Handles Git worktrees and shows parent-child relationships
- 🎨 **Beautiful UI**: Terminal-based UI with color-coded activity density
- ⚡ **Fast Performance**: File modification time optimization for large codebases
- 🔧 **Flexible Options**: Multiple time range options and display modes

## 🚀 Installation

### Via npm (Recommended)

```bash
# Install globally
npm install -g @ktny/ccstat

# Or use directly with npx
npx @ktny/ccstat
```

### Pre-built Binaries

Download pre-built binaries from the [releases page](https://github.com/ktny/ccstat/releases).

## 📖 Usage

### Basic Usage

```bash
# Show activity for the last 1 day (default)
ccstat

# Show activity for the last 7 days
ccstat --days 7

# Show activity for the last 6 hours
ccstat --hours 6
# or using short option
ccstat -H 6
```

### Advanced Options

```bash
# Worktree display (separate directories within the same repository)
ccstat --worktree

# Enable debug output
ccstat --debug

# Show help
ccstat --help
```

### Development Scripts

```bash
# Run in development mode
npm run dev

# Run with specific time ranges
npm run dev:days   # --days 2
npm run dev:hours  # --hours 6

# Build for production
npm run build

# Run tests and quality checks
npm run check
```

## 🏗️ Architecture

### Tech Stack

- **Language**: TypeScript
- **Runtime**: Node.js 18+
- **CLI Framework**: Commander.js
- **Terminal UI**: Ink (React-like components)
- **Git Integration**: simple-git
- **Type Validation**: Zod
- **Date Processing**: date-fns

### Project Structure

```
src/
├── cli/              # CLI entry point
│   └── index.ts      # Main CLI definition
├── core/             # Core business logic
│   ├── parser/       # Claude log parser
│   └── git/          # Git integration
├── ui/               # UI components (Ink)
│   ├── App.tsx
│   └── ProjectTable.tsx
├── models/           # Type definitions
└── utils/            # Utilities
```

## 📊 Output Example

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ 📊 Claude Project Timeline | 2025-07-03 16:49 - 2025-07-03 22:49 (6 hours) | │
│  3 projects                                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────╮
│                                                                              │
│ Project             Timeline | less ■■■■■ more      Events  Duration         │
│                                                                              │
│                     17  18   19  20   21   22                                │
│ ──────────────────────────────────────────────────────────────────────────   │
│ ccstat              ■■■■■■■■■■■■■■■■■■■■■■■■■■■■      1011       51m         │
│ web-project         ■■■■■■■■■■■■■■■                 245        23m         │
│ └─ mobile-app       ■■■■■■■                          67         12m         │
╰──────────────────────────────────────────────────────────────────────────────╯

Summary Statistics:
  - Total Projects: 3
  - Total Events: 1323
  - Total Duration: 86 minutes
```

## 🎯 Key Algorithms

### Active Duration Calculation

- Only counts time between consecutive events ≤ 5 minutes as active
- Excludes long breaks (> 5 minutes) to measure actual work time
- Minimum 5 minutes for single events
- Provides realistic work time estimates

### Project Grouping Logic

- **Default Mode**: Consolidates all directories within same Git repo
- **Worktree Mode**: Shows parent-child relationships for complex repos
- **Repository Detection**: Uses Git config parsing with fallback to directory names

### Timeline Visualization

- Maps event count to 5-level color scale for activity density
- Automatically selects appropriate time intervals based on range
- Character-based timeline bars using `■` symbols with color coding

## 🔧 Configuration

### Data Sources

ccstat reads Claude Code session logs from:
- `~/.claude/projects/*/*.jsonl` (primary)
- `~/.config/claude/projects/*/*.jsonl` (fallback)

### File Format

Each line in the JSONL files represents a session event:

```json
{
  "timestamp": "2025-07-03T12:34:56.789Z",
  "sessionId": "session-123",
  "cwd": "/home/user/project",
  "message": "user message",
  "usage": { "input_tokens": 100, "output_tokens": 50 }
}
```

## 🛠️ Development

### Prerequisites

- Node.js 18 or higher
- npm or pnpm

### Setup

```bash
# Clone the repository
git clone https://github.com/ktny/ccstat.git
cd ccstat/ts

# Install dependencies
npm install

# Run in development mode
npm run dev
```

### Available Scripts

```bash
npm run dev          # Development mode
npm run build        # Build for production
npm run test         # Run tests
npm run lint         # Lint code
npm run lint:fix     # Fix linting issues
npm run format       # Format code
npm run type-check   # TypeScript type checking
npm run check        # Run all quality checks
npm run clean        # Clean build artifacts
```

### Code Quality

The project uses:
- **ESLint** for code linting
- **Prettier** for code formatting
- **TypeScript** for type checking
- **Husky** for pre-commit hooks
- **lint-staged** for staged file processing

## 📦 Build & Release

### Building for Production

```bash
# Build TypeScript to JavaScript
npm run build

# Build standalone binaries
npm run package

# Complete production build
npm run build:prod
```

### Publishing to npm

```bash
# Publish to npm registry
npm publish
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Make your changes
4. Run quality checks (`npm run check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feat/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Ink](https://github.com/vadimdemedes/ink) for beautiful terminal UIs
- Inspired by the original Go version of ccstat
- Thanks to the Claude Code team for the session logging format

## 📞 Support

- 🐛 [Report Bug](https://github.com/ktny/ccstat/issues)
- 💡 [Request Feature](https://github.com/ktny/ccstat/issues)
- 📧 [Contact](https://github.com/ktny)

---

Made with ❤️ by [ktny](https://github.com/ktny)