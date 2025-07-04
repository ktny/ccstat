import React from 'react';
import { Box, Text } from 'ink';

interface SummaryStatisticsProps {
  projectCount: number;
  totalEvents: number;
  totalDuration: number;
}

export const SummaryStatistics: React.FC<SummaryStatisticsProps> = ({
  projectCount,
  totalEvents,
  totalDuration,
}) => {
  return (
    <Box marginTop={1}>
      <Text>
        Summary Statistics:{'\n'}
        {'  '}- Total Projects: {projectCount}
        {'\n'}
        {'  '}- Total Events: {totalEvents}
        {'\n'}
        {'  '}- Total Duration: {totalDuration} minutes
      </Text>
    </Box>
  );
};
