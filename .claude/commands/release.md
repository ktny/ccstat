---
name: project:release
description: Automate the release process for ccstat
---

## Usage

This command automates the release process for ccstat, including version updates and GitHub release creation.

## Steps

1. First, I'll ensure we're on the main branch with a clean working directory
2. You'll be prompted to enter the new version number (format: vX.Y.Z)
3. I'll update version references in README.md
4. Create and push a version update commit
5. Create and push a git tag to trigger the GitHub Actions release workflow

## What I'll do

1. **Check prerequisites:**
   - Verify we're on the main branch
   - Ensure working directory is clean
   - Confirm all PRs are merged

2. **Update version references:**
   - Update installation commands in README.md
   - Replace old version with new version

3. **Create release commit:**
   - Commit message: `fix: update installation instructions to use version vX.Y.Z`
   - Push to main branch

4. **Create and push tag:**
   - Create lightweight tag with version number
   - Push tag to trigger GitHub Actions

5. **GitHub Actions will automatically:**
   - Build binaries for multiple platforms (Linux/macOS, amd64/arm64)
   - Create GitHub release with auto-generated release notes
   - Upload binary artifacts

## Version numbering guidelines

- Follow semantic versioning: `vMAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes and minor improvements
- Always prefix with 'v' (e.g., v0.1.4, not 0.1.4)

## Prerequisites

- All PRs for the release must be merged to main branch
- You must have git push permissions to the repository
- GitHub Actions must be properly configured (`.github/workflows/release.yml`)