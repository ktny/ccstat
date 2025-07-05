import React, { useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import { SessionTimeline } from '../models/events';
import { loadSessionsInTimeRange, loadAllSessions } from '../core/parser';
import { ProjectTable } from './ProjectTable';
import { ColorTheme } from './colorThemes';
import { LoadingScreen } from './components/LoadingScreen';
import { ProgressTracker, ProgressUpdate } from '../utils/progressTracker';

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
  const [progress, setProgress] = useState<ProgressUpdate>({
    totalFiles: 0,
    processedFiles: 0,
  });

  useEffect(() => {
    async function loadData() {
      try {
        // Create progress tracker
        const progressTracker = new ProgressTracker(update => {
          setProgress(update);
        });

        let sessions: SessionTimeline[];

        // Pass project filtering to parser level for performance optimization
        const projectNames = project.length > 0 ? project : undefined;

        if (allTime) {
          // Load all sessions without time filtering
          sessions = await loadAllSessions(projectNames, progressTracker);
        } else {
          // Load sessions with time range filtering
          const now = new Date();
          const startTime = new Date();

          if (hours) {
            startTime.setHours(now.getHours() - hours);
          } else {
            startTime.setDate(now.getDate() - days);
          }

          sessions = await loadSessionsInTimeRange(startTime, now, projectNames, progressTracker);
        }

        setTimelines(sessions);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        setError(errorMessage);

        // Reset progress on error
        setProgress({
          totalFiles: 0,
          processedFiles: 0,
        });
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [days, hours, allTime, project]);

  if (loading) {
    return <LoadingScreen progress={progress} />;
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
