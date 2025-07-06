import { readdir, readFile, stat } from 'fs/promises';
import { join, dirname, basename } from 'path';
import { homedir } from 'os';
import { Event, EventSchema, Timeline } from '../../models/models';
import { getRepositoryName } from '../git';
import { ProgressTracker } from '../../utils/progressTracker';

const INACTIVE_THRESHOLD_MINUTES = 5; // Changed to 5 minutes to match Go version

// Repository cache to avoid redundant git operations
const repositoryCache = new Map<string, string>();

// Get cached repository name
function getCachedRepositoryName(directory: string): string {
  if (repositoryCache.has(directory)) {
    return repositoryCache.get(directory)!;
  }

  let repoName = getRepositoryName(directory);

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

export async function loadTimelines(
  startTime?: Date,
  endTime?: Date,
  projectNames?: string[],
  progressTracker?: ProgressTracker
): Promise<Timeline[]> {
  const filterOptions: FilterOptions = { projectNames };
  if (startTime && endTime) {
    filterOptions.startTime = startTime;
    filterOptions.endTime = endTime;
  }

  const events = await loadEventsFromProjects(filterOptions, progressTracker);

  const grouped = await groupEventsByRepositoryConsolidated(events);

  return Array.from(grouped.values());
}

interface FilterOptions {
  startTime?: Date;
  endTime?: Date;
  projectNames?: string[];
}

async function loadEventsFromProjects(
  filterOptions?: FilterOptions,
  progressTracker?: ProgressTracker
): Promise<Event[]> {
  // Check both possible directories
  const projectsDirs = [
    join(homedir(), '.claude', 'projects'),
    join(homedir(), '.config', 'claude', 'projects'),
  ];

  const allFilePaths: string[] = [];

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

      for (const file of files) {
        if (file.endsWith('.jsonl')) {
          const filePath = join(dirPath, file);
          allFilePaths.push(filePath);
        }
      }
    }
  }

  // Set total files count
  if (progressTracker) {
    progressTracker.setTotalFiles(allFilePaths.length);
  }

  // Process files with progress tracking
  const fileProcessingTasks: Promise<Event[]>[] = allFilePaths.map(filePath => {
    return parseJSONLFile(filePath, filterOptions, progressTracker);
  });

  // Process all files in parallel and flatten results
  // Use allSettled to allow individual file failures
  const results = await Promise.allSettled(fileProcessingTasks);

  // Filter successful results and flatten
  const allEventArrays = results
    .filter((result): result is PromiseFulfilledResult<Event[]> => result.status === 'fulfilled')
    .map(result => result.value);

  return allEventArrays.flat();
}

async function parseJSONLFile(
  filePath: string,
  filterOptions?: FilterOptions,
  progressTracker?: ProgressTracker
): Promise<Event[]> {
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
  const events: Event[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);

      // Fast check for required fields before expensive validation
      if (!data || typeof data !== 'object' || !data.timestamp || !data.sessionId) {
        continue;
      }

      // Validate and parse event
      const validationResult = EventSchema.safeParse(data);
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
function groupEventsByDirectory(events: Event[]): Map<string, Event[]> {
  const directoryEventMap = new Map<string, Event[]>();

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
  directoryEventMap: Map<string, Event[]>
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
function createTimeline(repoName: string, allRepoEvents: Event[]): Timeline {
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
  events: Event[]
): Promise<Map<string, Timeline>> {
  const directoryEventMap = groupEventsByDirectory(events);
  const repoDirectoryMap = mapDirectoriesToRepositories(directoryEventMap);
  const timelines = new Map<string, Timeline>();

  for (const [repoName, directories] of repoDirectoryMap.entries()) {
    const allRepoEvents: Event[] = [];

    for (const directory of directories) {
      const events = directoryEventMap.get(directory) || [];
      allRepoEvents.push(...events);
    }

    if (allRepoEvents.length === 0) continue;

    const timeline = createTimeline(repoName, allRepoEvents);
    timelines.set(repoName, timeline);
  }

  return timelines;
}

function calculateActiveDuration(events: Event[]): number {
  if (events.length <= 1) return 5; // Minimum 5 minutes for single event

  // Assume events are already sorted by timestamp
  let activeMinutes = 0;

  for (let i = 1; i < events.length; i++) {
    const prevTime = new Date(events[i - 1].timestamp);
    const currTime = new Date(events[i].timestamp);
    const intervalMinutes = (currTime.getTime() - prevTime.getTime()) / (1000 * 60);

    // Only count intervals up to the threshold as active time
    if (intervalMinutes <= INACTIVE_THRESHOLD_MINUTES) {
      activeMinutes += intervalMinutes;
    }
  }

  return Math.round(activeMinutes);
}
