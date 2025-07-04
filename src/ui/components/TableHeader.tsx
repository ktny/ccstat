import React from 'react';
import { Box, Text } from 'ink';
import { format } from 'date-fns';

interface TableHeaderProps {
  startTime: Date;
  endTime: Date;
  timeRangeText: string;
  projectCount: number;
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
  activityColors: (string | ((text: string) => string))[];
}

export const TableHeader: React.FC<TableHeaderProps> = ({
  startTime,
  endTime,
  timeRangeText,
  projectCount,
  projectWidth,
  timelineWidth,
  eventsWidth,
  durationWidth,
  activityColors,
}) => {
  return (
    <>
      {/* Title row */}
      <Box paddingX={1}>
        <Text>
          🤖 Claude Working Timeline | {format(startTime, 'yyyy-MM-dd HH:mm')} -{' '}
          {format(endTime, 'yyyy-MM-dd HH:mm')} ({timeRangeText}) | {projectCount} projects
        </Text>
      </Box>

      {/* Header row */}
      <Box paddingX={1}>
        <Box width={projectWidth}>
          <Text bold>Project</Text>
        </Box>
        <Box width={timelineWidth}>
          <Text bold color="whiteBright">
            <Text>Timeline | less </Text>
            {activityColors.map((color, index) => {
              if (typeof color === 'function') {
                return <Text key={index}>{color('■')}</Text>;
              }
              return (
                <Text key={index} color={color}>
                  ■
                </Text>
              );
            })}
            <Text> more</Text>
          </Text>
        </Box>
        <Box width={eventsWidth} justifyContent="flex-end">
          <Text bold>Events</Text>
        </Box>
        <Box width={durationWidth} justifyContent="flex-end">
          <Text bold color="yellow">
            Duration
          </Text>
        </Box>
      </Box>
    </>
  );
};
