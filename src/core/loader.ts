import type { CLIOptions, SessionTimeline, TimeRange } from '@/models';
import { loadSessionsInTimeRange } from './parser/session';

export async function loadSessions(
  timeRange: TimeRange,
  options: CLIOptions,
): Promise<SessionTimeline[]> {
  // Load all sessions in the time range
  const sessions = await loadSessionsInTimeRange(timeRange, options);

  // Filter by project if specified
  if (options.project) {
    const projectFilter = options.project.toLowerCase();
    return sessions.filter((session) =>
      session.project.toLowerCase().includes(projectFilter),
    );
  }

  return sessions;
}
