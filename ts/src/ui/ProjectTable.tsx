import React from 'react';
import { Box, Text } from 'ink';
import { SessionTimeline } from '../models/events';
import { format } from 'date-fns';

interface ProjectTableProps {
  timelines: SessionTimeline[];
  days?: number;
  hours?: number;
}

export const ProjectTable: React.FC<ProjectTableProps> = ({ timelines, days, hours }) => {
  if (timelines.length === 0) {
    return <Text>No activity found in the specified time range.</Text>;
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

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" paddingX={1}>
        <Text>
          📊 Claude Project Timeline | {format(startTime, 'yyyy-MM-dd HH:mm')} - {format(endTime, 'yyyy-MM-dd HH:mm')} ({timeRangeText}) | {timelines.length} projects
        </Text>
      </Box>
      
      <Box marginTop={1} borderStyle="round" flexDirection="column">
        <Box paddingX={1} paddingY={1}>
          <Box width={25}>
            <Text>Project</Text>
          </Box>
          <Box width={30}>
            <Text>Timeline</Text>
          </Box>
          <Box width={10} justifyContent="flex-end">
            <Text>Events</Text>
          </Box>
          <Box width={10} justifyContent="flex-end">
            <Text>Duration</Text>
          </Box>
        </Box>
        
        <Box paddingX={1}>
          <Text dimColor>{'─'.repeat(70)}</Text>
        </Box>
        
        {timelines.map((timeline, index) => (
          <ProjectRow key={index} timeline={timeline} startTime={startTime} endTime={endTime} />
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
}

const ProjectRow: React.FC<ProjectRowProps> = ({ timeline, startTime, endTime }) => {
  const projectName = timeline.isChild 
    ? `└─ ${timeline.projectName}`
    : timeline.projectName;
  
  const truncatedName = projectName.length > 23 
    ? projectName.substring(0, 20) + '…'
    : projectName;

  return (
    <Box paddingX={1}>
      <Box width={25}>
        <Text>{truncatedName}</Text>
      </Box>
      <Box width={30}>
        <TimelineBar timeline={timeline} startTime={startTime} endTime={endTime} />
      </Box>
      <Box width={10} justifyContent="flex-end">
        <Text>{timeline.eventCount}</Text>
      </Box>
      <Box width={10} justifyContent="flex-end">
        <Text>{timeline.activeDuration}m</Text>
      </Box>
    </Box>
  );
};

interface TimelineBarProps {
  timeline: SessionTimeline;
  startTime: Date;
  endTime: Date;
}

const TimelineBar: React.FC<TimelineBarProps> = ({ timeline, startTime, endTime }) => {
  const totalMinutes = (endTime.getTime() - startTime.getTime()) / (1000 * 60);
  const barWidth = 24;
  const minutesPerSlot = totalMinutes / barWidth;
  
  const activityLevels = new Array(barWidth).fill(0);
  
  for (const event of timeline.events) {
    const eventTime = new Date(event.timestamp);
    const minutesFromStart = (eventTime.getTime() - startTime.getTime()) / (1000 * 60);
    const slot = Math.floor(minutesFromStart / minutesPerSlot);
    
    if (slot >= 0 && slot < barWidth) {
      activityLevels[slot]++;
    }
  }
  
  const maxActivity = Math.max(...activityLevels);
  const bar = activityLevels.map(level => {
    if (level === 0) return ' ';
    
    const intensity = maxActivity > 0 ? level / maxActivity : 0;
    if (intensity > 0.8) return '■';
    if (intensity > 0.6) return '■';
    if (intensity > 0.4) return '■';
    if (intensity > 0.2) return '■';
    return '■';
  }).join('');
  
  return <Text>{bar}</Text>;
};