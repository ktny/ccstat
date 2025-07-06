import React, { useMemo } from 'react';
import { Box, Text, useStdout } from 'ink';
import { Timeline } from '../models/events';
import { ColorTheme, getColorScheme, getBorderColor } from './colorThemes';
import { calculateProjectWidth } from './utils/tableUtils';
import { TitleRow } from './components/TitleRow';
import { HeaderRow } from './components/HeaderRow';
import { TableTimeAxis } from './components/TableTimeAxis';
import { ProjectRow } from './components/ProjectRow';
import { SummaryStatistics } from './components/SummaryStatistics';
import { sortTimelines, createSortOptions } from '../utils/sort';

interface ProjectTableProps {
  timelines: Timeline[];
  days?: number;
  hours?: number;
  color: ColorTheme;
  sort?: string;
  reverse?: boolean;
  allTime?: boolean;
  project?: string[];
}

export const ProjectTable: React.FC<ProjectTableProps> = ({
  timelines,
  days,
  hours,
  color,
  sort,
  reverse,
  allTime,
  project = [],
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
    const message =
      project.length > 0
        ? `🔍 No Claude sessions found for project(s): ${project.join(', ')}`
        : '🔍 No Claude sessions found in the specified time range';
    return <Text>{message}</Text>;
  }

  const totalEvents = sortedTimelines.reduce((sum, t) => sum + t.eventCount, 0);
  const totalDuration = sortedTimelines.reduce((sum, t) => sum + t.activeDuration, 0);

  const { startTime, endTime, timeRangeText } = useMemo(() => {
    if (allTime) {
      // Calculate actual time range from the data
      if (sortedTimelines.length === 0) {
        const now = new Date();
        return {
          startTime: now,
          endTime: now,
          timeRangeText: 'all time',
        };
      }

      const allStartTimes = sortedTimelines.map(t => t.startTime);
      const allEndTimes = sortedTimelines.map(t => t.endTime);

      return {
        startTime: new Date(Math.min(...allStartTimes.map(t => t.getTime()))),
        endTime: new Date(Math.max(...allEndTimes.map(t => t.getTime()))),
        timeRangeText: 'all time',
      };
    } else {
      // Use provided time range
      const endTime = new Date();
      const startTime = new Date();

      if (hours) {
        startTime.setHours(endTime.getHours() - hours);
      } else {
        startTime.setDate(endTime.getDate() - (days || 1));
      }

      return {
        startTime,
        endTime,
        timeRangeText: hours ? `${hours} hours` : `${days || 1} days`,
      };
    }
  }, [allTime, sortedTimelines, hours, days]);

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
