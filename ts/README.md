# ccstat (TypeScript Version)

CLI tool that analyzes Claude Code session history and visualizes project activity patterns in a timeline format.

## Installation

```bash
cd ts
npm install
```

## Development

```bash
# Run in development mode
npm run dev

# Build the project
npm run build

# Run tests
npm test

# Lint and format
npm run lint
npm run format
```

## Usage

```bash
# Basic execution (last 1 day)
npm run dev

# Display activity for the last N days
npm run dev -- --days 7

# Display activity for the last N hours  
npm run dev -- --hours 6
```

## Project Structure

```
ts/
├── src/
│   ├── cli/         # CLI entry point
│   ├── core/        # Core business logic
│   ├── ui/          # Terminal UI components
│   ├── models/      # Type definitions
│   └── utils/       # Utilities
├── bin/             # Executable files
├── tests/           # Test files
└── dist/            # Build output
```