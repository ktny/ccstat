import React from 'react';
import { Text } from 'ink';
import { SessionTimeline } from '../../models/events';

interface TimelineBarProps {
  timeline: SessionTimeline;
  startTime: Date;
  endTime: Date;
  width: number;
  activityColors: (string | ((text: string) => string))[];
}

export const TimelineBar: React.FC<TimelineBarProps> = ({
  timeline,
  startTime,
  endTime,
  width,
  activityColors,
}) => {
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
        <Text key={i} color="gray">
          ■
        </Text>
      );
    } else {
      // Calculate density level (1-4 scale mapped to our colors)
      const densityLevel = Math.min(4, Math.floor((count / maxActivity) * 4) + 1);
      const colorIndex = densityLevel;
      const color = activityColors[colorIndex];

      if (typeof color === 'function') {
        timelineElements.push(<Text key={i}>{color('■')}</Text>);
      } else {
        timelineElements.push(
          <Text key={i} color={color}>
            ■
          </Text>
        );
      }
    }
  }

  return <>{timelineElements}</>;
};
