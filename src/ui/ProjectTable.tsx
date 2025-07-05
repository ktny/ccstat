import React, { useMemo } from 'react';
import { Box, Text, useStdout } from 'ink';
import { SessionTimeline } from '../models/events';
import { ColorTheme, getColorScheme, getBorderColor } from './colorThemes';
import { calculateProjectWidth } from './utils/tableUtils';
import { TitleRow } from './components/TitleRow';
import { HeaderRow } from './components/HeaderRow';
import { TableTimeAxis } from './components/TableTimeAxis';
import { ProjectRow } from './components/ProjectRow';
import { SummaryStatistics } from './components/SummaryStatistics';
import { sortTimelines, createSortOptions } from '../utils/sort';

interface ProjectTableProps {
  timelines: SessionTimeline[];
  days?: number;
  hours?: number;
  color: ColorTheme;
  sort?: string;
  reverse?: boolean;
}

export const ProjectTable: React.FC<ProjectTableProps> = ({
  timelines,
  days,
  hours,
  color,
  sort,
  reverse,
}) => {
  const { stdout } = useStdout();
  const terminalWidth = stdout?.columns || 80;

  const colorScheme = useMemo(() => getColorScheme(color), [color]);
  const activityColors = colorScheme.colors;
  const borderColor = useMemo(() => getBorderColor(color), [color]);

  // Apply sorting
  const sortedTimelines = useMemo(() => {
    const sortOptions = createSortOptions(sort, reverse);
    return sortTimelines(timelines, sortOptions);
  }, [timelines, sort, reverse]);

  if (sortedTimelines.length === 0) {
    return <Text>🔍 No Claude sessions found in the specified time range</Text>;
  }

  const totalEvents = sortedTimelines.reduce((sum, t) => sum + t.eventCount, 0);
  const totalDuration = sortedTimelines.reduce((sum, t) => sum + t.activeDuration, 0);

  const startTime = new Date();
  const endTime = new Date();

  if (hours) {
    startTime.setHours(endTime.getHours() - hours);
  } else {
    startTime.setDate(endTime.getDate() - (days || 1));
  }

  const timeRangeText = hours ? `${hours} hours` : `${days || 1} days`;

  // Calculate responsive column widths
  const projectWidth = calculateProjectWidth(sortedTimelines);
  const eventsWidth = 8;
  const durationWidth = 10;
  const timelineWidth = Math.max(
    25,
    terminalWidth - projectWidth - eventsWidth - durationWidth - 12
  );

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" flexDirection="column" borderColor={borderColor} paddingX={1}>
        <TitleRow
          startTime={startTime}
          endTime={endTime}
          timeRangeText={timeRangeText}
          projectCount={sortedTimelines.length}
        />

        <HeaderRow
          projectWidth={projectWidth}
          timelineWidth={timelineWidth}
          eventsWidth={eventsWidth}
          durationWidth={durationWidth}
          activityColors={activityColors}
        />

        <TableTimeAxis
          startTime={startTime}
          endTime={endTime}
          projectWidth={projectWidth}
          timelineWidth={timelineWidth}
          eventsWidth={eventsWidth}
          durationWidth={durationWidth}
        />

        {/* Data rows */}
        {sortedTimelines.map((timeline, index) => (
          <ProjectRow
            key={index}
            timeline={timeline}
            startTime={startTime}
            endTime={endTime}
            projectWidth={projectWidth}
            timelineWidth={timelineWidth}
            eventsWidth={eventsWidth}
            durationWidth={durationWidth}
            activityColors={activityColors}
          />
        ))}
      </Box>

      <SummaryStatistics
        projectCount={sortedTimelines.length}
        totalEvents={totalEvents}
        totalDuration={totalDuration}
      />
    </Box>
  );
};
