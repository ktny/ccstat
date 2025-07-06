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
  const directoryEventMap = await loadEvents(startTime, endTime, progressTracker);
  const grouped = await groupEventsByRepository(directoryEventMap, projectNames);

  return Array.from(grouped.values());
}

async function loadEvents(
  startTime?: Date,
  endTime?: Date,
  progressTracker?: ProgressTracker
): Promise<Map<string, Event[]>> {
  // Check both possible directories
  const projectsDirs = [
    join(homedir(), '.claude', 'projects'),
    join(homedir(), '.config', 'claude', 'projects'),
  ];

  const fileToDirectoryMap = new Map<string, string>();

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
          fileToDirectoryMap.set(filePath, dirPath);
        }
      }
    }
  }

  const allFilePaths = Array.from(fileToDirectoryMap.keys());

  // Set total files count
  if (progressTracker) {
    progressTracker.setTotalFiles(allFilePaths.length);
  }

  // Process files with progress tracking
  const fileProcessingTasks: Promise<Event[]>[] = allFilePaths.map(filePath => {
    return parseJSONLFile(filePath, startTime, endTime, progressTracker);
  });

  // Process all files in parallel
  const allEventArrays = await Promise.all(fileProcessingTasks);

  // Group events by directory
  const directoryEventMap = new Map<string, Event[]>();

  for (let i = 0; i < allFilePaths.length; i++) {
    const filePath = allFilePaths[i];
    const directoryPath = fileToDirectoryMap.get(filePath)!;
    const events = allEventArrays[i];

    if (events.length === 0) continue;

    const existingEvents = directoryEventMap.get(directoryPath) || [];
    directoryEventMap.set(directoryPath, [...existingEvents, ...events]);
  }

  return directoryEventMap;
}

async function parseJSONLFile(
  filePath: string,
  startTime?: Date,
  endTime?: Date,
  progressTracker?: ProgressTracker
): Promise<Event[]> {
  // Check file modification time for performance optimization
  // Skip stat check for --all-time (when no time filter is specified)
  if (startTime && endTime) {
    const stats = await stat(filePath);
    if (stats.mtime < startTime) {
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
      if (startTime && endTime) {
        // Convert to local time
        const localEventTime = new Date(eventTime.toLocaleString());

        if (localEventTime >= startTime && localEventTime <= endTime) {
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

// Map directories to repositories
function mapDirectoriesToRepositories(
  directoryEventMap: Map<string, Event[]>
): Map<string, string[]> {
  const repoDirectoryMap = new Map<string, string[]>();

  for (const [directory, events] of directoryEventMap.entries()) {
    let eventCwd: string | undefined;
    for (const event of events) {
      if (event.cwd) {
        eventCwd = event.cwd;
        break;
      }
    }

    const repoName = getCachedRepositoryName(eventCwd || directory);

    if (!repoDirectoryMap.has(repoName)) {
      repoDirectoryMap.set(repoName, []);
    }
    repoDirectoryMap.get(repoName)!.push(directory);
  }

  return repoDirectoryMap;
}

// Create session timeline from repository events
function createTimeline(repoName: string, repoEvents: Event[]): Timeline {
  // Sort events by timestamp
  repoEvents.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return {
    projectName: repoName,
    directory: '',
    repository: repoName,
    events: repoEvents,
    eventCount: repoEvents.length,
    activeDuration: calculateActiveDuration(repoEvents),
    startTime: new Date(repoEvents[0].timestamp),
    endTime: new Date(repoEvents[repoEvents.length - 1].timestamp),
  };
}

// Main grouping function for consolidated mode (default)
async function groupEventsByRepository(
  directoryEventMap: Map<string, Event[]>,
  projectNames?: string[]
): Promise<Map<string, Timeline>> {
  const repoDirectoryMap = mapDirectoriesToRepositories(directoryEventMap);
  const timelines = new Map<string, Timeline>();

  for (const [repoName, directories] of repoDirectoryMap.entries()) {
    // Filter by project names if specified
    if (projectNames && projectNames.length > 0) {
      if (!projectNames.includes(repoName)) {
        continue;
      }
    }

    const repoEvents: Event[] = [];

    for (const directory of directories) {
      const events = directoryEventMap.get(directory) || [];
      repoEvents.push(...events);
    }

    if (repoEvents.length === 0) continue;

    const timeline = createTimeline(repoName, repoEvents);
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
