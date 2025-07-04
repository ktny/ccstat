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

interface ProjectTableProps {
  timelines: SessionTimeline[];
  days?: number;
  hours?: number;
  color: ColorTheme;
}

export const ProjectTable: React.FC<ProjectTableProps> = ({ timelines, days, hours, color }) => {
  const { stdout } = useStdout();
  const terminalWidth = stdout?.columns || 80;

  const colorScheme = useMemo(() => getColorScheme(color), [color]);
  const activityColors = colorScheme.colors;
  const borderColor = useMemo(() => getBorderColor(color), [color]);

  if (timelines.length === 0) {
    return <Text>🔍 No Claude sessions found in the specified time range</Text>;
  }

  const totalEvents = timelines.reduce((sum, t) => sum + t.eventCount, 0);
  const totalDuration = timelines.reduce((sum, t) => sum + t.activeDuration, 0);

  const startTime = new Date();
  const endTime = new Date();

  if (hours) {
    startTime.setHours(endTime.getHours() - hours);
  } else {
    startTime.setDate(endTime.getDate() - (days || 1));
  }

  const timeRangeText = hours ? `${hours} hours` : `${days || 1} days`;

  // Calculate responsive column widths
  const projectWidth = calculateProjectWidth(timelines);
  const eventsWidth = 8;
  const durationWidth = 10;
  const timelineWidth = Math.max(
    25,
    terminalWidth - projectWidth - eventsWidth - durationWidth - 12
  );

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" flexDirection="column" borderColor={borderColor}>
        <TitleRow
          startTime={startTime}
          endTime={endTime}
          timeRangeText={timeRangeText}
          projectCount={timelines.length}
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
        {timelines.map((timeline, index) => (
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
        projectCount={timelines.length}
        totalEvents={totalEvents}
        totalDuration={totalDuration}
      />
    </Box>
  );
};
