#!/usr/bin/env node
import { Command } from 'commander';
import { render } from 'ink';
import React from 'react';
import { App } from '../ui/App';
import { isValidColorTheme, COLOR_THEME_VALUES } from '../ui/colorThemes';

const program = new Command();

program
  .name('ccstat')
  .description('Analyze Claude Code session history and visualize project activity patterns')
  .option('-d, --days <number>', 'display activity for the last N days', '1')
  .option('-H, --hours <number>', 'display activity for the last N hours')
  .option('-c, --color <theme>', 'color theme: forest, ocean, sunset, violet', 'forest')
  .option('-s --sort <field>', 'sort by field: project, timeline, events, duration', 'timeline')
  .option('-r, --reverse', 'reverse sort order (default: ascending)')
  .option('-p, --project <names...>', 'filter by project names (space-separated)')
  .option('-a, --all-time', 'display all session history across all time periods')
  .version('2.0.5')
  .parse(process.argv);

async function main() {
  const options = program.opts();

  // Validate color theme
  if (!isValidColorTheme(options.color)) {
    console.error(`Error: Invalid color theme '${options.color}'.`);
    console.error(`Available color themes: ${COLOR_THEME_VALUES.join(', ')}`);
    process.exit(1);
  }

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
