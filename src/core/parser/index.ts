import { readdir, readFile, stat } from 'fs/promises';
import { join, dirname, basename } from 'path';
import { homedir } from 'os';
import { SessionEvent, SessionEventSchema, SessionTimeline } from '../../models/events';
import { getRepositoryName } from '../git';
import { ProgressTracker } from '../../utils/progressTracker';

const INACTIVE_THRESHOLD_MINUTES = 5; // Changed to 5 minutes to match Go version

// Repository cache to avoid redundant git operations
const repositoryCache = new Map<string, string>();

// Clear cache at the start of each execution
function clearRepositoryCache(): void {
  repositoryCache.clear();
}

// Get cached repository name
function getCachedRepositoryName(directory: string): string {
  if (repositoryCache.has(directory)) {
    return repositoryCache.get(directory)!;
  }

  let repoName = getRepositoryName(directory);

  console.log({ repoName });

  if (!repoName) {
    // Try to find parent repository
    repoName = findParentRepository(directory);
    if (!repoName) {
      repoName = basename(directory);
    }
  }

  if (repoName) {
    repositoryCache.set(directory, repoName);
  }

  return repoName;
}

// Find parent repository by walking up the directory tree
function findParentRepository(directory: string): string | null {
  let currentDir = directory;

  while (currentDir !== '/' && currentDir !== '.') {
    const parentDir = dirname(currentDir);

    if (parentDir === currentDir) {
      break;
    }

    if (repositoryCache.has(parentDir)) {
      const repoName = repositoryCache.get(parentDir)!;
      if (repoName) {
        repositoryCache.set(directory, repoName);
        return repoName;
      }
    } else {
      const repoName = getRepositoryName(parentDir);
      if (repoName) {
        repositoryCache.set(parentDir, repoName);
        repositoryCache.set(directory, repoName);
        return repoName;
      }
    }

    currentDir = parentDir;
  }

  return null;
}

export async function loadSessionsInTimeRange(
  startTime?: Date,
  endTime?: Date,
  projectNames?: string[],
  progressTracker?: ProgressTracker
): Promise<SessionTimeline[]> {
  // Clear repository cache at the start of each execution
  clearRepositoryCache();

  const filterOptions: FilterOptions = { projectNames };
  if (startTime && endTime) {
    filterOptions.startTime = startTime;
    filterOptions.endTime = endTime;
  }

  const events = await loadEventsFromProjects(filterOptions, progressTracker);

  const grouped = await groupEventsByRepositoryConsolidated(events);

  return Array.from(grouped.values());
}

export async function loadAllSessions(
  projectNames?: string[],
  progressTracker?: ProgressTracker
): Promise<SessionTimeline[]> {
  return loadSessionsInTimeRange(undefined, undefined, projectNames, progressTracker);
}

interface FilterOptions {
  startTime?: Date;
  endTime?: Date;
  projectNames?: string[];
}

async function loadEventsFromProjects(
  filterOptions?: FilterOptions,
  progressTracker?: ProgressTracker
): Promise<SessionEvent[]> {
  // Check both possible directories
  const projectsDirs = [
    join(homedir(), '.claude', 'projects'),
    join(homedir(), '.config', 'claude', 'projects'),
  ];

  const allFilePaths: { filePath: string; projectName: string }[] = [];

  for (const projectsDir of projectsDirs) {
    try {
      const dirStat = await stat(projectsDir);
      if (!dirStat.isDirectory()) continue;
    } catch (error) {
      continue;
    }

    const dirs = await readdir(projectsDir);

    for (const dir of dirs) {
      const dirPath = join(projectsDir, dir);

      let dirStats;
      try {
        dirStats = await stat(dirPath);
      } catch (error) {
        continue;
      }

      if (!dirStats.isDirectory()) continue;

      const files = await readdir(dirPath);

      // Early project filtering - check if directory should be processed
      const repoName = getCachedRepositoryName(dirPath);
      if (filterOptions?.projectNames?.length) {
        if (!filterOptions.projectNames.includes(repoName)) {
          continue; // Skip this entire directory
        }
      }

      for (const file of files) {
        if (file.endsWith('.jsonl')) {
          const filePath = join(dirPath, file);
          allFilePaths.push({ filePath, projectName: repoName });
        }
      }
    }
  }

  // Set total files count
  if (progressTracker) {
    progressTracker.setTotalFiles(allFilePaths.length);
  }

  // Process files with progress tracking
  const fileProcessingTasks: Promise<SessionEvent[]>[] = allFilePaths.map(({ filePath }) => {
    return parseJSONLFile(filePath, filterOptions, progressTracker);
  });

  // Process all files in parallel and flatten results
  const allEventArrays = await Promise.all(fileProcessingTasks);
  return allEventArrays.flat();
}

async function parseJSONLFile(
  filePath: string,
  filterOptions?: FilterOptions,
  progressTracker?: ProgressTracker
): Promise<SessionEvent[]> {
  // Check file modification time for performance optimization
  // Skip stat check for --all-time (when no time filter is specified)
  if (filterOptions && filterOptions.startTime && filterOptions.endTime) {
    const stats = await stat(filePath);
    if (stats.mtime < filterOptions.startTime) {
      return [];
    }
  }

  const content = await readFile(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const events: SessionEvent[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);

      // Fast check for required fields before expensive validation
      if (!data || typeof data !== 'object' || !data.timestamp || !data.sessionId) {
        continue;
      }

      // Validate and parse event
      const validationResult = SessionEventSchema.safeParse(data);
      if (!validationResult.success) {
        continue;
      }

      const event = validationResult.data;
      const eventTime = new Date(event.timestamp);

      // Apply time filtering if provided
      if (filterOptions && filterOptions.startTime && filterOptions.endTime) {
        // Convert to local time
        const localEventTime = new Date(eventTime.toLocaleString());

        if (localEventTime >= filterOptions.startTime && localEventTime <= filterOptions.endTime) {
          // Optimize object creation by directly modifying timestamp
          event.timestamp = eventTime.toISOString();
          events.push(event);
        }
      } else {
        // No time filtering, include all events
        // Optimize object creation by directly modifying timestamp
        event.timestamp = eventTime.toISOString();
        events.push(event);
      }
    } catch (error) {
      // Skip invalid lines
      continue;
    }
  }

  // Increment progress after processing file
  if (progressTracker) {
    progressTracker.incrementProcessedFiles();
  }

  return events;
}

// Group events by directory
function groupEventsByDirectory(events: SessionEvent[]): Map<string, SessionEvent[]> {
  const directoryEventMap = new Map<string, SessionEvent[]>();

  for (const event of events) {
    const directory = event.cwd || 'unknown';
    if (!directoryEventMap.has(directory)) {
      directoryEventMap.set(directory, []);
    }
    directoryEventMap.get(directory)!.push(event);
  }

  return directoryEventMap;
}

// Map directories to repositories
function mapDirectoriesToRepositories(
  directoryEventMap: Map<string, SessionEvent[]>
): Map<string, string[]> {
  const repoDirectoryMap = new Map<string, string[]>();

  for (const directory of directoryEventMap.keys()) {
    const repoName = getCachedRepositoryName(directory);

    if (!repoDirectoryMap.has(repoName)) {
      repoDirectoryMap.set(repoName, []);
    }
    repoDirectoryMap.get(repoName)!.push(directory);
  }

  return repoDirectoryMap;
}

// Create session timeline from repository events
function createSessionTimeline(repoName: string, allRepoEvents: SessionEvent[]): SessionTimeline {
  // Sort events by timestamp
  allRepoEvents.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return {
    projectName: repoName,
    directory: '',
    repository: repoName,
    events: allRepoEvents,
    eventCount: allRepoEvents.length,
    activeDuration: calculateActiveDuration(allRepoEvents),
    startTime: new Date(allRepoEvents[0].timestamp),
    endTime: new Date(allRepoEvents[allRepoEvents.length - 1].timestamp),
  };
}

// Main grouping function for consolidated mode (default)
async function groupEventsByRepositoryConsolidated(
  events: SessionEvent[]
): Promise<Map<string, SessionTimeline>> {
  const directoryEventMap = groupEventsByDirectory(events);
  const repoDirectoryMap = mapDirectoriesToRepositories(directoryEventMap);
  const timelines = new Map<string, SessionTimeline>();

  for (const [repoName, directories] of repoDirectoryMap.entries()) {
    const allRepoEvents: SessionEvent[] = [];

    for (const directory of directories) {
      const events = directoryEventMap.get(directory) || [];
      allRepoEvents.push(...events);
    }

    if (allRepoEvents.length === 0) continue;

    const timeline = createSessionTimeline(repoName, allRepoEvents);
    timelines.set(repoName, timeline);
  }

  return timelines;
}

function calculateActiveDuration(events: SessionEvent[]): number {
  if (events.length <= 1) return 5; // Minimum 5 minutes for single event

  // Sort events by timestamp
  const sortedEvents = events.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  let activeMinutes = 0;

  for (let i = 1; i < sortedEvents.length; i++) {
    const prevTime = new Date(sortedEvents[i - 1].timestamp);
    const currTime = new Date(sortedEvents[i].timestamp);
    const intervalMinutes = (currTime.getTime() - prevTime.getTime()) / (1000 * 60);

    // Only count intervals up to the threshold as active time
    if (intervalMinutes <= INACTIVE_THRESHOLD_MINUTES) {
      activeMinutes += intervalMinutes;
    }
  }

  return Math.round(activeMinutes);
}
