#!/usr/bin/env node
import { Command } from 'commander';
import { render } from 'ink';
import React from 'react';
import { App } from '../ui/App';

const program = new Command();

program
  .name('ccstat')
  .description('Analyze Claude Code session history and visualize project activity patterns')
  .version('1.0.0')
  .option('-d, --days <number>', 'display activity for the last N days', '1')
  .option('-H, --hours <number>', 'display activity for the last N hours')
  .option('--worktree', 'display directories separately even within the same repository')
  .option('--color <theme>', 'color theme: blue, green, red, purple, yellow, cyan, classic, random', 'random')
  .option('--debug', 'enable debug output')
  .parse(process.argv);

async function main() {
  const options = program.opts();

  const app = render(
    React.createElement(App, {
      days: options.hours ? undefined : parseInt(options.days),
      hours: options.hours ? parseInt(options.hours) : undefined,
      worktree: options.worktree || false,
      color: options.color || 'random',
      debug: options.debug || false,
    })
  );

  try {
    await app.waitUntilExit();
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
