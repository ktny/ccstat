import React from 'react';
import { Box, Text } from 'ink';
import type { SessionTimeline, TimeRange } from '@/models';
import { formatDuration } from '@/utils/time';

interface TimelineProps {
  sessions: SessionTimeline[];
  timeRange: TimeRange;
}

// Activity density levels with colors (Ink-compatible)
const ACTIVITY_LEVELS = [
  'gray',      // No activity
  'gray',      // Very low activity  
  'yellow',    // Low activity
  'green',     // Medium activity
  'greenBright', // High activity
] as const;

interface TimeSlot {
  hour: number;
  eventCount: number;
  activityLevel: number;
}

export const Timeline: React.FC<TimelineProps> = ({ sessions, timeRange }) => {
  // Generate timeline for each session
  const sessionTimelines = sessions.map(session => {
    const timeline = generateHourlyTimeline(session, timeRange);
    return {
      session,
      timeline,
    };
  });

  // Calculate time axis labels (every 4 hours)
  const timeLabels = [];
  for (let hour = 0; hour <= 24; hour += 4) {
    timeLabels.push(hour.toString().padStart(2, '0'));
  }

  // Calculate column widths
  const maxProjectNameLength = Math.max(...sessions.map(s => s.project.length));
  const projectColumnWidth = Math.max(maxProjectNameLength, 12);
  const timelineWidth = 40; // Fixed timeline width
  const eventsColumnWidth = 8;
  const durationColumnWidth = 10;

  return (
    <Box flexDirection="column">
      {/* Header row with time labels */}
      <Box>
        <Box width={projectColumnWidth}>
          <Text bold color="cyan">Project</Text>
        </Box>
        <Box width={timelineWidth} marginLeft={2}>
          <Text bold color="cyan">Timeline | less </Text>
          <Text backgroundColor="green" color="black">■</Text>
          <Text bold color="cyan"> more</Text>
        </Box>
        <Box width={eventsColumnWidth} marginLeft={2}>
          <Text bold color="cyan">Events</Text>
        </Box>
        <Box width={durationColumnWidth} marginLeft={2}>
          <Text bold color="cyan">Duration</Text>
        </Box>
      </Box>

      {/* Time axis labels */}
      <Box>
        <Box width={projectColumnWidth}>
          {/* Empty space for project names */}
        </Box>
        <Box width={timelineWidth} marginLeft={2}>
          <Text dimColor>
            {timeLabels.map((label, index) => (
              <Text key={index}>
                {label}{index < timeLabels.length - 1 ? '      ' : ''}
              </Text>
            ))}
          </Text>
        </Box>
      </Box>

      {/* Session timelines */}
      {sessionTimelines.map(({ session, timeline }, index) => (
        <Box key={index}>
          {/* Project name */}
          <Box width={projectColumnWidth}>
            <Text>{session.project}</Text>
          </Box>
          
          {/* Timeline visualization */}
          <Box width={timelineWidth} marginLeft={2}>
            <Text>
              {timeline.map((slot, slotIndex) => {
                const color = ACTIVITY_LEVELS[slot.activityLevel] || 'gray';
                return (
                  <Text key={slotIndex} color={color}>■</Text>
                );
              })}
            </Text>
          </Box>

          {/* Events count */}
          <Box width={eventsColumnWidth} marginLeft={2}>
            <Text>{session.events.length}</Text>
          </Box>

          {/* Duration */}
          <Box width={durationColumnWidth} marginLeft={2}>
            <Text>{formatDuration(session.activeDuration)}</Text>
          </Box>
        </Box>
      ))}
    </Box>
  );
};

function generateHourlyTimeline(session: SessionTimeline, timeRange: TimeRange): TimeSlot[] {
  const timeline: TimeSlot[] = [];
  
  // Create 40 time slots to match the visual width
  const totalMinutes = (timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60);
  const minutesPerSlot = totalMinutes / 40;

  for (let i = 0; i < 40; i++) {
    const slotStart = new Date(timeRange.start.getTime() + i * minutesPerSlot * 60 * 1000);
    const slotEnd = new Date(timeRange.start.getTime() + (i + 1) * minutesPerSlot * 60 * 1000);
    
    // Count events in this time slot
    const eventsInSlot = session.events.filter(event => {
      const eventTime = new Date(event.timestamp);
      return eventTime >= slotStart && eventTime < slotEnd;
    });

    const eventCount = eventsInSlot.length;
    const activityLevel = calculateActivityLevel(eventCount);

    timeline.push({
      hour: slotStart.getHours(),
      eventCount,
      activityLevel,
    });
  }

  return timeline;
}

function calculateActivityLevel(eventCount: number): number {
  if (eventCount === 0) return 0;
  if (eventCount <= 2) return 1;
  if (eventCount <= 5) return 2;
  if (eventCount <= 10) return 3;
  return 4; // High activity
}