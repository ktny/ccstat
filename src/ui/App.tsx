import React from 'react';
import { Box, Text } from 'ink';
import type { CLIOptions, SessionTimeline, TimeRange } from '@/models';
import { Timeline } from './components/Timeline';
import { ProjectTable } from './components/ProjectTable';

interface AppProps {
  sessions: SessionTimeline[];
  timeRange: TimeRange;
  options: CLIOptions;
}

export const App: React.FC<AppProps> = ({ sessions, timeRange, options }) => {
  const hasActivity = sessions.length > 0;

  return (
    <Box flexDirection="column">
      <Box marginBottom={1}>
        <Text color="green" bold>
          ccstat - Claude Code Session Timeline
        </Text>
      </Box>

      {hasActivity ? (
        <Box flexDirection="column">
          <Timeline sessions={sessions} timeRange={timeRange} />
          <ProjectTable sessions={sessions} showWorktree={options.worktree} />

          {options.project && (
            <Box marginTop={1}>
              <Text dimColor>Filtered by project: {options.project}</Text>
            </Box>
          )}

          {options.debug && (
            <Box marginTop={1}>
              <Text dimColor>Debug mode enabled</Text>
            </Box>
          )}
        </Box>
      ) : (
        <Box flexDirection="column">
          <Text dimColor>No activity found in the specified time range.</Text>
          <Box marginTop={1}>
            <Text dimColor>
              Time range: {timeRange.start.toLocaleString()} to {timeRange.end.toLocaleString()}
            </Text>
          </Box>
          {options.debug && (
            <Box marginTop={1}>
              <Text dimColor>Checked directory: ~/.claude/projects/</Text>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};
