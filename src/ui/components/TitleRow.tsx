import React from 'react';
import { Box, Text } from 'ink';
import { format } from 'date-fns';

interface TitleRowProps {
  startTime: Date;
  endTime: Date;
  timeRangeText: string;
  projectCount: number;
}

export const TitleRow: React.FC<TitleRowProps> = ({
  startTime,
  endTime,
  timeRangeText,
  projectCount,
}) => {
  return (
    <Box>
      <Text bold>
        ClaudeCode Working Timeline | {format(startTime, 'yyyy-MM-dd HH:mm')} -{' '}
        {format(endTime, 'yyyy-MM-dd HH:mm')} ({timeRangeText}) | {projectCount} projects
      </Text>
    </Box>
  );
};
