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
    '--sort <field>',
    'sort by field: project, timeline, events, duration (default: timeline)',
    'timeline'
  )
  .option('--reverse', 'reverse sort order (default: ascending)')
  .option('--all-time', 'display all session history across all time periods')
  .option('-p, --project <names...>', 'filter by project names (space-separated)')
  .parse(process.argv);

async function main() {
  const options = program.opts();

  const app = render(
    React.createElement(App, {
      days: options.hours ? undefined : parseInt(options.days),
      hours: options.hours ? parseInt(options.hours) : undefined,
      color: options.color,
      sort: options.sort,
      reverse: options.reverse || false,
      allTime: options.allTime || false,
      project: options.project || [],
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
