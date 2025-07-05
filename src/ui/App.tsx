import React, { useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import { SessionTimeline } from '../models/events';
import { loadSessionsInTimeRange, loadAllSessions } from '../core/parser';
import { ProjectTable } from './ProjectTable';
import { ColorTheme } from './colorThemes';

interface AppProps {
  days?: number;
  hours?: number;
  color: ColorTheme;
  sort?: string;
  reverse?: boolean;
  allTime?: boolean;
  project?: string[];
}

export const App: React.FC<AppProps> = ({
  days = 1,
  hours,
  color,
  sort,
  reverse,
  allTime,
  project = [],
}) => {
  const [timelines, setTimelines] = useState<SessionTimeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        let sessions: SessionTimeline[];

        // Pass project filtering to parser level for performance optimization
        const projectNames = project.length > 0 ? project : undefined;

        if (allTime) {
          // Load all sessions without time filtering
          sessions = await loadAllSessions(projectNames);
        } else {
          // Load sessions with time range filtering
          const now = new Date();
          const startTime = new Date();

          if (hours) {
            startTime.setHours(now.getHours() - hours);
          } else {
            startTime.setDate(now.getDate() - days);
          }

          sessions = await loadSessionsInTimeRange(startTime, now, projectNames);
        }

        setTimelines(sessions);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [days, hours, allTime, project]);

  if (loading) {
    return <Text>Loading Claude sessions...</Text>;
  }

  if (error) {
    return <Text color="red">Error: {error}</Text>;
  }

  return (
    <Box flexDirection="column">
      <ProjectTable
        timelines={timelines}
        days={days}
        hours={hours}
        color={color}
        sort={sort}
        reverse={reverse}
        allTime={allTime}
        project={project}
      />
    </Box>
  );
};
