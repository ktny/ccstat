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
  .option('--color <theme>', 'color theme: blue, green, orange, purple, classic', 'green')
  .option(
    '--sort <option>',
    'sort by: project:asc, project:desc, created:asc, created:desc, events:asc, events:desc, duration:asc, duration:desc'
  )
  .parse(process.argv);

async function main() {
  const options = program.opts();

  const app = render(
    React.createElement(App, {
      days: options.hours ? undefined : parseInt(options.days),
      hours: options.hours ? parseInt(options.hours) : undefined,
      color: options.color || 'random',
      sort: options.sort,
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
