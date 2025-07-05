# Changelog

All notable changes to the TypeScript edition of ccstat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-03

### Added

#### Phase 5: Release Preparation

- =� **Complete build and packaging setup**
  - Production-ready build scripts using TypeScript Compiler
  - Standalone binary generation with pkg
  - npm package publishing configuration
  - Pre-publish quality checks and validation

- =� **Comprehensive documentation**
  - Detailed README with installation and usage instructions
  - Architecture documentation and API reference
  - Contributing guidelines and development setup
  - Changelog for version tracking

- =� **Release infrastructure**
  - npm scoped package configuration (@ktny/ccstat)
  - GitHub Actions CI/CD for automated testing
  - Pre-built binary distribution setup
  - Version management and release workflow

#### Phase 4: Development Environment (Issue #60)

- � **Enhanced development tooling**
  - EditorConfig for consistent coding styles
  - Husky + lint-staged for pre-commit hooks
  - VSCode workspace settings and extensions
  - Comprehensive npm scripts (lint:fix, check, clean)

#### Phase 3: UI Implementation

- <� **Beautiful terminal UI with Ink**
  - React-like component architecture
  - Timeline visualization with 5-level activity density
  - Responsive design adapting to terminal width
  - Color-coded project activity patterns
  - Summary statistics and project hierarchies

#### Phase 2: Core Features

- =
  **Complete session analysis engine**
  - JSONL file parsing with large buffer support
  - Smart duration calculation (5-minute inactivity threshold)
  - File modification time optimization
  - Multiple Claude projects directory support

- =� **Advanced Git integration**
  - Repository detection and worktree support
  - Parent-child project relationships
  - SSH and HTTPS Git URL parsing
  - Intelligent project grouping algorithms

#### Phase 1: Foundation

- <� **TypeScript project architecture**
  - Modern ESNext module system
  - Strict TypeScript configuration
  - Jest testing framework setup
  - ESLint + Prettier code quality tools

- =� **CLI framework**
  - Commander.js for argument parsing
  - Multiple time range options (days/hours)
  - Debug mode and help system
  - Cross-platform compatibility

### Technical Details

- **Runtime**: Node.js 18+ with ESM modules
- **UI Framework**: Ink 4.x for terminal rendering
- **Type Safety**: Full TypeScript coverage with Zod validation
- **Build System**: TypeScript Compiler with production optimizations
- **Package Manager**: npm with lock file support
- **Code Quality**: ESLint, Prettier, Husky pre-commit hooks

### Migration from Go Version

This TypeScript edition provides:

-  **Full feature parity** with the original Go version
-  **Enhanced UI** with better color coding and formatting
-  **Improved performance** with file modification time optimization
-  **Better error handling** and user feedback
-  **Modern development** experience with TypeScript

### Performance Improvements

- **File scanning optimization**: Skip processing files older than start time
- **Memory efficiency**: Streaming JSONL parsing for large files
- **Caching**: Repository information caching to reduce Git operations
- **Responsive UI**: Dynamic terminal width adaptation

### Dependencies

#### Production Dependencies

- `commander` ^12.0.0 - CLI argument parsing
- `ink` ^4.4.1 - Terminal UI framework
- `react` ^18.2.0 - Component architecture
- `simple-git` ^3.0.0 - Git repository operations
- `zod` ^3.22.0 - Runtime type validation
- `date-fns` ^3.3.1 - Date manipulation utilities
- `chalk` ^5.3.0 - Terminal string styling

#### Development Dependencies

- `typescript` ^5.3.0 - TypeScript compiler
- `@typescript-eslint/*` ^7.0.0 - TypeScript ESLint rules
- `eslint` ^8.57.0 - JavaScript/TypeScript linting
- `prettier` ^3.2.0 - Code formatting
- `jest` ^29.7.0 - Testing framework
- `husky` ^9.1.7 - Git hooks management
- `lint-staged` ^16.1.2 - Staged files processing
- `pkg` ^5.8.1 - Binary packaging
- `tsx` ^4.7.0 - TypeScript execution

## [0.x.x] - Development Phases

### [0.3.0] - Phase 3: UI Implementation

- Terminal UI components with Ink
- Timeline visualization
- Project table display
- Responsive design

### [0.2.0] - Phase 2: Core Features

- JSONL parser implementation
- Session analysis logic
- Git integration
- Duration calculation algorithms

### [0.1.0] - Phase 1: Foundation

- TypeScript project setup
- CLI framework with Commander.js
- Development environment
- Basic project structure

---

For detailed information about each phase, see the [project documentation](README.md) and [GitHub issues](https://github.com/ktny/ccstat/issues).
