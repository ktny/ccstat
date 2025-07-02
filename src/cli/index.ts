#!/usr/bin/env node

// Disable react-devtools in production
process.env.CI = 'true';

import { Command } from 'commander';
import { render } from 'ink';
import React from 'react';
import type { CLIOptions } from '@/models';
import { App } from '@/ui/App';
import { loadSessions } from '@/core/loader';
import { getTimeRange } from '@/utils/time';

const VERSION = '2.0.0'; // TODO: Read from package.json

const program = new Command();

program
  .name('ccstat')
  .description('Analyze Claude Code session history and visualize project activity patterns')
  .version(VERSION, '-v, --version', 'Output the current version')
  .option('-d, --days <number>', 'Display activity for the last N days', '1')
  .option('-H, --hours <number>', 'Display activity for the last N hours')
  .option('-p, --project <name>', 'Filter display by specific project')
  .option('-w, --worktree', 'Show worktree directories separately', false)
  .option('--debug', 'Enable debug output', false)
  .action(async (options: CLIOptions) => {
    try {
      // Calculate time range
      const timeRange = getTimeRange(options);

      if (options.debug) {
        // eslint-disable-next-line no-console
        console.error(
          `Time range: ${timeRange.start.toISOString()} to ${timeRange.end.toISOString()}`,
        );
      }

      // Load sessions
      const sessions = await loadSessions(timeRange, options);

      if (sessions.length === 0) {
        // eslint-disable-next-line no-console
        console.log('No activity found in the specified time range.');
        process.exit(0);
      }

      // Render UI (disable devtools in production)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call
      const inkInstance = render(React.createElement(App, { sessions, timeRange, options }), {
        debug: false, // Disable react-devtools integration
      });

      // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
      await inkInstance.waitUntilExit();
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

program.parse();
