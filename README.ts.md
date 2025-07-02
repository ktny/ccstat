# ccstat (TypeScript Version)

> ⚠️ This is the TypeScript rewrite of ccstat. The original Go version is being phased out.

## Overview

ccstat is a CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

## Tech Stack

- **Language**: TypeScript
- **CLI Framework**: Commander.js
- **Terminal UI**: Ink (React-based)
- **Git Integration**: simple-git
- **Build Tool**: esbuild
- **Package Manager**: npm/yarn/pnpm

## Installation

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run in development mode
npm run dev
```

## Development

```bash
# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run typecheck
```

## Project Structure

```
src/
├── cli/         # CLI entry point (Commander.js)
├── core/        # Core business logic
│   ├── parser/  # Claude log parser
│   ├── git/     # Git integration
│   └── analyzer/# Timeline analysis
├── ui/          # UI components (Ink/React)
├── models/      # TypeScript types
└── utils/       # Utilities
```

## Migration Status

See [Issue #53](https://github.com/ktny/ccstat/issues/53) for the migration progress.

## License

MIT