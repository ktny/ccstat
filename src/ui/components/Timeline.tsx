import React from 'react';
import { Box, Text } from 'ink';
import type { SessionTimeline, TimeRange } from '@/models';
import { formatDuration } from '@/utils/time';

interface TimelineProps {
  sessions: SessionTimeline[];
  timeRange: TimeRange;
}

export const Timeline: React.FC<TimelineProps> = ({ sessions, timeRange }) => {
  if (sessions.length === 0) {
    return null;
  }

  const totalDuration = sessions.reduce((sum, session) => sum + session.activeDuration, 0);
  const totalEvents = sessions.reduce((sum, session) => sum + session.events.length, 0);

  return (
    <Box flexDirection="column" marginTop={1}>
      <Box>
        <Text bold underline>
          Activity Summary
        </Text>
      </Box>

      <Box marginTop={1} flexDirection="column">
        <Box>
          <Text>
            <Text color="green">Total Active Time:</Text> {formatDuration(totalDuration)}
          </Text>
        </Box>
        <Box>
          <Text>
            <Text color="yellow">Total Events:</Text> {totalEvents}
          </Text>
        </Box>
        <Box>
          <Text>
            <Text color="blue">Time Period:</Text> {formatTimeRange(timeRange)}
          </Text>
        </Box>
      </Box>

      <Box marginTop={1} flexDirection="column">
        <Text bold>Activity Breakdown:</Text>
        {sessions.map((session, index) => (
          <TimelineBar
            key={index}
            session={session}
            maxDuration={Math.max(...sessions.map((s) => s.activeDuration))}
          />
        ))}
      </Box>
    </Box>
  );
};

interface TimelineBarProps {
  session: SessionTimeline;
  maxDuration: number;
}

const TimelineBar: React.FC<TimelineBarProps> = ({ session, maxDuration }) => {
  const barWidth = 40; // Maximum bar width in characters
  const relativeWidth = Math.max(1, Math.round((session.activeDuration / maxDuration) * barWidth));
  const bar = '■'.repeat(relativeWidth);

  // Color based on activity level
  let color = 'gray';
  const activityRatio = session.activeDuration / maxDuration;
  if (activityRatio > 0.8) color = 'red';
  else if (activityRatio > 0.6) color = 'yellow';
  else if (activityRatio > 0.4) color = 'green';
  else if (activityRatio > 0.2) color = 'blue';

  return (
    <Box>
      <Box width={20}>
        <Text color="cyan">{session.project.slice(0, 18)}</Text>
      </Box>
      <Box width={42}>
        <Text color={color}>{bar}</Text>
      </Box>
      <Box>
        <Text dimColor>{formatDuration(session.activeDuration)}</Text>
      </Box>
    </Box>
  );
};

function formatTimeRange(range: TimeRange): string {
  const start = range.start.toLocaleDateString();
  const end = range.end.toLocaleDateString();

  if (start === end) {
    return `${start} (${range.start.toLocaleTimeString()} - ${range.end.toLocaleTimeString()})`;
  }

  return `${start} - ${end}`;
}
