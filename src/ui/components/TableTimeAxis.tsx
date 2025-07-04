import React from 'react';
import { Box, Text } from 'ink';
import { createTimeAxis } from '../utils/tableUtils';

interface TableTimeAxisProps {
  startTime: Date;
  endTime: Date;
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
}

export const TableTimeAxis: React.FC<TableTimeAxisProps> = ({
  startTime,
  endTime,
  projectWidth,
  timelineWidth,
  eventsWidth,
  durationWidth,
}) => {
  return (
    <Box paddingX={1} paddingTop={1}>
      <Box width={projectWidth}>
        <Text> </Text>
      </Box>
      <Box width={timelineWidth}>
        <Text>{createTimeAxis(startTime, endTime, timelineWidth - 2)}</Text>
      </Box>
      <Box width={eventsWidth}>
        <Text> </Text>
      </Box>
      <Box width={durationWidth}>
        <Text> </Text>
      </Box>
    </Box>
  );
};
