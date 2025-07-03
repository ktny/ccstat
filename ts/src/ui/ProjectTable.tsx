import React from 'react';
import { Box, Text, useStdout } from 'ink';
import { SessionTimeline } from '../models/events';
import { format } from 'date-fns';

interface ProjectTableProps {
  timelines: SessionTimeline[];
  days?: number;
  hours?: number;
}

// Activity density colors (using standard terminal colors)
const ACTIVITY_COLORS = [
  'dim',      // No activity
  'yellow',   // Low activity
  'cyan',     // Medium-low activity
  'green',    // Medium-high activity
  'red',      // High activity
];

// Calculate optimal project column width
function calculateProjectWidth(timelines: SessionTimeline[]): number {
  const minWidth = 20;
  const maxWidth = 30;
  
  if (timelines.length === 0) return minWidth;
  
  let maxNameLength = 0;
  for (const timeline of timelines) {
    let displayName = timeline.projectName;
    if (timeline.isChild) {
      displayName = ' └─' + timeline.projectName;
    }
    if (displayName.length > maxNameLength) {
      maxNameLength = displayName.length;
    }
  }
  
  const calculatedWidth = maxNameLength + 2;
  return Math.max(minWidth, Math.min(maxWidth, calculatedWidth));
}

// Create time axis with tick marks
function createTimeAxis(startTime: Date, endTime: Date, width: number): string {
  const duration = endTime.getTime() - startTime.getTime();
  const axisChars = new Array(width).fill(' ');
  
  // Determine appropriate time format and interval
  const hours = duration / (1000 * 60 * 60);
  let interval: number;
  let formatStr: string;
  
  if (hours <= 2) {
    interval = 15 * 60 * 1000; // 15 minutes
    formatStr = 'HH:mm';
  } else if (hours <= 8) {
    interval = 60 * 60 * 1000; // 1 hour
    formatStr = 'HH';
  } else if (hours <= 48) {
    interval = 4 * 60 * 60 * 1000; // 4 hours
    formatStr = 'HH';
  } else {
    interval = 24 * 60 * 60 * 1000; // 1 day
    formatStr = 'MM/dd';
  }
  
  // Generate ticks
  const startTimestamp = startTime.getTime();
  let current = Math.ceil(startTimestamp / interval) * interval;
  
  while (current <= endTime.getTime()) {
    const position = Math.floor(((current - startTimestamp) / duration) * width);
    if (position >= 0 && position < width) {
      const tickTime = new Date(current);
      const label = format(tickTime, formatStr);
      
      // Place label centered on position
      const startPos = Math.max(0, Math.min(width - label.length, position - Math.floor(label.length / 2)));
      for (let i = 0; i < label.length && startPos + i < width; i++) {
        axisChars[startPos + i] = label[i];
      }
    }
    current += interval;
  }
  
  return axisChars.join('');
}

export const ProjectTable: React.FC<ProjectTableProps> = ({ timelines, days, hours }) => {
  const { stdout } = useStdout();
  const terminalWidth = stdout?.columns || 80;
  
  if (timelines.length === 0) {
    return <Text>🔍 No Claude sessions found in the specified time range</Text>;
  }

  const totalEvents = timelines.reduce((sum, t) => sum + t.eventCount, 0);
  const totalDuration = timelines.reduce((sum, t) => sum + t.activeDuration, 0);
  
  const startTime = new Date();
  const endTime = new Date();
  
  if (hours) {
    startTime.setHours(endTime.getHours() - hours);
  } else {
    startTime.setDate(endTime.getDate() - (days || 1));
  }

  const timeRangeText = hours 
    ? `${hours} hours`
    : `${days || 1} days`;

  // Calculate responsive column widths
  const projectWidth = calculateProjectWidth(timelines);
  const eventsWidth = 8;
  const durationWidth = 10;
  const timelineWidth = Math.max(25, terminalWidth - projectWidth - eventsWidth - durationWidth - 12);

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" paddingX={1}>
        <Text>
          📊 Claude Project Timeline | {format(startTime, 'yyyy-MM-dd HH:mm')} - {format(endTime, 'yyyy-MM-dd HH:mm')} ({timeRangeText}) | {timelines.length} projects
        </Text>
      </Box>
      
      <Box marginTop={1} borderStyle="round" flexDirection="column">
        {/* Header row */}
        <Box paddingX={1} paddingY={1}>
          <Box width={projectWidth}>
            <Text bold color="cyan">Project</Text>
          </Box>
          <Box width={timelineWidth}>
            <Text bold>Timeline | less <Text color="dim">■</Text><Text color="yellow">■</Text><Text color="cyan">■</Text><Text color="green">■</Text><Text color="red">■</Text> more</Text>
          </Box>
          <Box width={eventsWidth} justifyContent="flex-end">
            <Text bold color="cyan">Events</Text>
          </Box>
          <Box width={durationWidth} justifyContent="flex-end">
            <Text bold color="yellow">Duration</Text>
          </Box>
        </Box>
        
        {/* Time axis row */}
        <Box paddingX={1}>
          <Box width={projectWidth}>
            <Text> </Text>
          </Box>
          <Box width={timelineWidth}>
            <Text color="dim">{createTimeAxis(startTime, endTime, timelineWidth - 2)}</Text>
          </Box>
          <Box width={eventsWidth}>
            <Text> </Text>
          </Box>
          <Box width={durationWidth}>
            <Text> </Text>
          </Box>
        </Box>
        
        {/* Separator */}
        <Box paddingX={1}>
          <Text dimColor>{'─'.repeat(terminalWidth - 6)}</Text>
        </Box>
        
        {/* Data rows */}
        {timelines.map((timeline, index) => (
          <ProjectRow 
            key={index} 
            timeline={timeline} 
            startTime={startTime} 
            endTime={endTime}
            projectWidth={projectWidth}
            timelineWidth={timelineWidth}
            eventsWidth={eventsWidth}
            durationWidth={durationWidth}
          />
        ))}
      </Box>
      
      <Box marginTop={1}>
        <Text>
          Summary Statistics:{'\n'}
          {'  '}- Total Projects: {timelines.length}{'\n'}
          {'  '}- Total Events: {totalEvents}{'\n'}
          {'  '}- Total Duration: {totalDuration} minutes
        </Text>
      </Box>
    </Box>
  );
};

interface ProjectRowProps {
  timeline: SessionTimeline;
  startTime: Date;
  endTime: Date;
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
}

const ProjectRow: React.FC<ProjectRowProps> = ({ 
  timeline, 
  startTime, 
  endTime, 
  projectWidth, 
  timelineWidth, 
  eventsWidth, 
  durationWidth 
}) => {
  const projectName = timeline.isChild 
    ? ` └─${timeline.projectName}`
    : timeline.projectName;
  
  const truncatedName = projectName.length > projectWidth - 2 
    ? projectName.substring(0, projectWidth - 5) + '…'
    : projectName;

  return (
    <Box paddingX={1}>
      <Box width={projectWidth}>
        <Text>{truncatedName}</Text>
      </Box>
      <Box width={timelineWidth}>
        <TimelineBar 
          timeline={timeline} 
          startTime={startTime} 
          endTime={endTime} 
          width={timelineWidth - 2} 
        />
      </Box>
      <Box width={eventsWidth} justifyContent="flex-end">
        <Text>{timeline.eventCount}</Text>
      </Box>
      <Box width={durationWidth} justifyContent="flex-end">
        <Text>{timeline.activeDuration}m</Text>
      </Box>
    </Box>
  );
};

interface TimelineBarProps {
  timeline: SessionTimeline;
  startTime: Date;
  endTime: Date;
  width: number;
}

const TimelineBar: React.FC<TimelineBarProps> = ({ timeline, startTime, endTime, width }) => {
  const totalDuration = endTime.getTime() - startTime.getTime();
  const activityCounts = new Array(width).fill(0);
  
  // Count events per time position
  for (const event of timeline.events) {
    const eventTime = new Date(event.timestamp);
    const eventOffset = eventTime.getTime() - startTime.getTime();
    const position = Math.floor((eventOffset / totalDuration) * width);
    
    // Clamp position to valid range
    const clampedPosition = Math.max(0, Math.min(width - 1, position));
    activityCounts[clampedPosition]++;
  }
  
  // Find max activity for normalization
  const maxActivity = Math.max(...activityCounts, 1);
  
  // Create timeline elements with density-based coloring
  const timelineElements: React.ReactNode[] = [];
  
  for (let i = 0; i < width; i++) {
    const count = activityCounts[i];
    
    if (count === 0) {
      // No activity
      timelineElements.push(
        <Text key={i} color="dim">■</Text>
      );
    } else {
      // Calculate density level (1-4 scale mapped to our colors)
      const densityLevel = Math.min(4, Math.floor((count / maxActivity) * 4) + 1);
      const colorIndex = densityLevel;
      const color = ACTIVITY_COLORS[colorIndex];
      
      timelineElements.push(
        <Text key={i} color={color}>■</Text>
      );
    }
  }
  
  return <>{timelineElements}</>;
};