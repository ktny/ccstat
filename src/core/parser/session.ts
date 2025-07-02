import type { CLIOptions, MessageEvent, SessionTimeline, TimeRange } from '@/models';
import { findJSONLFiles } from '@/utils/fs';
import { parseFilesInParallel } from './jsonl';
import { getRepositoryName } from '@/core/git/repository';
import { calculateActiveDuration, getSessionTimeRange } from '@/core/analyzer/duration';

export async function loadSessionsInTimeRange(
  timeRange: TimeRange,
  options: CLIOptions,
): Promise<SessionTimeline[]> {
  // Find all JSONL files in the time range
  const jsonlFiles = await findJSONLFiles(timeRange);

  if (jsonlFiles.length === 0) {
    if (options.debug) {
      console.error('No JSONL files found in time range');
    }
    return [];
  }

  if (options.debug) {
    console.error(`Found ${jsonlFiles.length} JSONL files to parse`);
  }

  // Parse all files in parallel
  const allEvents = await parseFilesInParallel(jsonlFiles, timeRange, options.debug);

  if (allEvents.length === 0) {
    return [];
  }

  // Group events by project/directory
  const groupedEvents = await groupEventsByProject(allEvents, options);

  // Convert to SessionTimeline objects
  const timelines: SessionTimeline[] = [];

  for (const [projectKey, events] of groupedEvents.entries()) {
    const { start, end } = getSessionTimeRange(events);
    const activeDuration = calculateActiveDuration(events);

    // Extract project name and directory from the key
    const parts = projectKey.split('::');
    const projectName = parts[0] || 'unknown';
    const directory = parts[1] || '';

    // Check for parent project relationship (worktree mode)
    const repoInfo = await getRepositoryName(directory);
    const parentProject =
      repoInfo.isWorktree && !options.worktree ? repoInfo.parentRepo : undefined;

    timelines.push({
      project: projectName,
      directory,
      events,
      activeDuration,
      startTime: start,
      endTime: end,
      parentProject,
    });
  }

  // Sort by start time
  return timelines.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
}

async function groupEventsByProject(
  events: MessageEvent[],
  options: CLIOptions,
): Promise<Map<string, MessageEvent[]>> {
  const grouped = new Map<string, MessageEvent[]>();

  // Group events by directory first
  const byDirectory = new Map<string, MessageEvent[]>();
  for (const event of events) {
    const dir = event.cwd;
    if (!byDirectory.has(dir)) {
      byDirectory.set(dir, []);
    }
    byDirectory.get(dir)!.push(event);
  }

  // Then group by repository if not in worktree mode
  for (const [directory, dirEvents] of byDirectory.entries()) {
    const repoInfo = await getRepositoryName(directory);

    let projectKey: string;
    if (options.worktree || !repoInfo.isWorktree) {
      // Use repository name as project, or directory name if not in git repo
      projectKey = `${repoInfo.name}::${directory}`;
    } else {
      // Group by parent repository
      const parentName = repoInfo.parentRepo || repoInfo.name;
      projectKey = `${parentName}::${repoInfo.path}`;
    }

    if (!grouped.has(projectKey)) {
      grouped.set(projectKey, []);
    }
    grouped.get(projectKey)!.push(...dirEvents);
  }

  return grouped;
}
