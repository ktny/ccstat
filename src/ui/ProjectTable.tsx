import React, { useMemo } from 'react';
import { Box, Text, useStdout } from 'ink';
import { Timeline } from '../models/models';
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

  // Apply project filtering and sorting
  const filteredAndSortedTimelines = useMemo(() => {
    // Filter by project names if specified
    let filtered = timelines;
    if (project.length > 0) {
      filtered = timelines.filter(timeline => project.includes(timeline.projectName));
    }

    // Apply sorting
    const sortOptions = createSortOptions(sort, reverse);
    return sortTimelines(filtered, sortOptions);
  }, [timelines, project, sort, reverse]);

  if (filteredAndSortedTimelines.length === 0) {
    const message =
      project.length > 0
        ? `🔍 No Claude sessions found for project(s): ${project.join(', ')}`
        : '🔍 No Claude sessions found in the specified time range';
    return <Text>{message}</Text>;
  }

  const totalEvents = filteredAndSortedTimelines.reduce((sum, t) => sum + t.eventCount, 0);
  const totalDuration = filteredAndSortedTimelines.reduce((sum, t) => sum + t.activeDuration, 0);

  const { startTime, endTime, timeRangeText } = useMemo(() => {
    if (allTime) {
      // Calculate actual time range from the data
      if (filteredAndSortedTimelines.length === 0) {
        const now = new Date();
        return {
          startTime: now,
          endTime: now,
          timeRangeText: 'all time',
        };
      }

      const allStartTimes = filteredAndSortedTimelines.map(t => t.startTime);
      const allEndTimes = filteredAndSortedTimelines.map(t => t.endTime);

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
  }, [allTime, filteredAndSortedTimelines, hours, days]);

  // Calculate responsive column widths
  const projectWidth = calculateProjectWidth(filteredAndSortedTimelines);
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
          projectCount={filteredAndSortedTimelines.length}
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
        {filteredAndSortedTimelines.map((timeline, index) => (
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
        projectCount={filteredAndSortedTimelines.length}
        totalEvents={totalEvents}
        totalDuration={totalDuration}
      />
    </Box>
  );
};
