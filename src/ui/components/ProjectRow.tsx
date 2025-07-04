import React from 'react';
import { Box, Text } from 'ink';
import { SessionTimeline } from '../../models/events';
import { TimelineBar } from './TimelineBar';

interface ProjectRowProps {
  timeline: SessionTimeline;
  startTime: Date;
  endTime: Date;
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
  activityColors: (string | ((text: string) => string))[];
}

export const ProjectRow: React.FC<ProjectRowProps> = ({
  timeline,
  startTime,
  endTime,
  projectWidth,
  timelineWidth,
  eventsWidth,
  durationWidth,
  activityColors,
}) => {
  const projectName = timeline.isChild ? ` └─${timeline.projectName}` : timeline.projectName;

  const truncatedName =
    projectName.length > projectWidth - 2
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
          activityColors={activityColors}
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
