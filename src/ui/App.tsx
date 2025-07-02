import React from 'react';
import { Box, Text } from 'ink';
import type { CLIOptions, SessionTimeline, TimeRange } from '@/models';
import { Timeline } from './components/Timeline';

interface AppProps {
  sessions: SessionTimeline[];
  timeRange: TimeRange;
  options: CLIOptions;
}

export const App: React.FC<AppProps> = ({ sessions, timeRange, options }) => {
  const hasActivity = sessions.length > 0;

  if (!hasActivity) {
    return (
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
    );
  }

  // Calculate summary statistics
  const totalProjects = sessions.length;
  const totalEvents = sessions.reduce((sum, session) => sum + session.events.length, 0);
  const totalDuration = sessions.reduce((sum, session) => sum + session.activeDuration, 0);

  // Format time range
  const formatDateTime = (date: Date) => {
    return date.toLocaleDateString('en-CA') + ' ' + date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const timeRangeText = getDurationText(timeRange);
  const headerText = `Claude Project Timeline | ${formatDateTime(timeRange.start)} - ${formatDateTime(timeRange.end)} (${timeRangeText}) | ${totalProjects} projects`;

  return (
    <Box flexDirection="column">
      {/* Header with border */}
      <Box 
        borderStyle="round" 
        borderColor="cyan" 
        paddingX={1}
        marginBottom={1}
      >
        <Text>🔔 {headerText}</Text>
      </Box>

      {/* Timeline visualization */}
      <Timeline sessions={sessions} timeRange={timeRange} />

      {/* Summary statistics */}
      <Box flexDirection="column" marginTop={1}>
        <Text bold underline>Summary Statistics:</Text>
        <Text>- Total Projects: {totalProjects}</Text>
        <Text>- Total Events: {totalEvents}</Text>
        <Text>- Total Duration: {Math.round(totalDuration / 60)} minutes</Text>
      </Box>

      {/* Optional information */}
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
  );
};

function getDurationText(timeRange: TimeRange): string {
  const diffMs = timeRange.end.getTime() - timeRange.start.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  const diffDays = diffMs / (1000 * 60 * 60 * 24);

  if (diffDays >= 1) {
    const days = Math.round(diffDays);
    return `${days} day${days > 1 ? 's' : ''}`;
  } else {
    const hours = Math.round(diffHours);
    return `${hours} hour${hours > 1 ? 's' : ''}`;
  }
}