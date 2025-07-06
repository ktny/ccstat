import React from 'react';
import { Box, Text } from 'ink';

interface HeaderRowProps {
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
  activityColors: (string | ((text: string) => string))[];
}

export const HeaderRow: React.FC<HeaderRowProps> = ({
  projectWidth,
  timelineWidth,
  eventsWidth,
  durationWidth,
  activityColors,
}) => {
  return (
    <Box paddingTop={1}>
      <Box width={projectWidth}>
        <Text bold>Project</Text>
      </Box>
      <Box width={timelineWidth}>
        <Text bold>
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
        <Text bold>Duration</Text>
      </Box>
    </Box>
  );
};
