<div align="center">
  <img src="assets/logo.png" alt="ccstat logo" width="140" />
</div>

# ccstat

> Visualize your Claude Code session activity timeline — fast, beautiful, and insightful!

[![npm version](https://badge.fury.io/js/ccstat.svg)](https://badge.fury.io/js/ccstat)
![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)

## ✨ What is ccstat?

ccstat is a powerful CLI tool that analyzes your Claude Code session history and transforms it into beautiful timeline visualizations. Track your coding patterns and gain insights into your development workflow.

![demo](assets/demo.png)

### 🎯 Key Features

- 📈 **Timeline Visualization** — Color-coded activity blocks showing your coding patterns
- 📁 **Git Integration** — Automatically groups projects by repository
- 🕐 **Flexible Time Ranges** — View activity by days (1+) or hours (1-24)

## 🚀 Installation

Install with a single command:

```sh
# Using npx
npx ccstat

# Using bunx (recommended for speed)
bunx ccstat
```

## 📖 Usage

### Basic Commands

```bash
# View last 24 hours of activity
npx ccstat

# View all period
npx ccstat -a

# View last 7 days
npx ccstat --days 7

# View last 6 hours
npx ccstat --hours 6

# View sorted events descending
npx ccstat --sort events --reverse -a

# View ocean color
npx ccstat --color ocean
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for the Claude Code community</sub>
</div>
