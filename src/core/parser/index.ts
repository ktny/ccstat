import { readdir, readFile, stat } from 'fs/promises';
import { join, dirname, basename } from 'path';
import { homedir } from 'os';
import { SessionEvent, SessionEventSchema, SessionTimeline } from '../../models/events';
import { getRepositoryName } from '../git';

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
  startTime: Date,
  endTime: Date
): Promise<SessionTimeline[]> {
  // Clear repository cache at the start of each execution
  clearRepositoryCache();

  const events = await loadAllEvents(startTime, endTime);
  const grouped = await groupEventsByRepositoryConsolidated(events);

  // Always use consolidated mode - sort by event count
  return Array.from(grouped.values()).sort((a, b) => b.eventCount - a.eventCount);
}

export async function loadAllSessions(): Promise<SessionTimeline[]> {
  // Clear repository cache at the start of each execution
  clearRepositoryCache();

  const events = await loadAllEventsWithoutTimeFilter();
  const grouped = await groupEventsByRepositoryConsolidated(events);

  // Always use consolidated mode - sort by event count
  return Array.from(grouped.values()).sort((a, b) => b.eventCount - a.eventCount);
}

async function loadAllEvents(startTime: Date, endTime: Date): Promise<SessionEvent[]> {
  const allEvents: SessionEvent[] = [];

  // Check both possible directories
  const projectsDirs = [
    join(homedir(), '.claude', 'projects'),
    join(homedir(), '.config', 'claude', 'projects'),
  ];

  let foundAnyDir = false;

  for (const projectsDir of projectsDirs) {
    try {
      const dirStat = await stat(projectsDir);
      if (!dirStat.isDirectory()) continue;

      foundAnyDir = true;

      const dirs = await readdir(projectsDir);

      for (const dir of dirs) {
        const dirPath = join(projectsDir, dir);
        try {
          const files = await readdir(dirPath);

          for (const file of files) {
            if (file.endsWith('.jsonl')) {
              const filePath = join(dirPath, file);

              // parseJSONLFile already checks modification time, so just call it
              const events = await parseJSONLFile(filePath, startTime, endTime);
              allEvents.push(...events);
            }
          }
        } catch (error) {
          // Skip inaccessible directories
          continue;
        }
      }
    } catch (error) {
      // Directory doesn't exist, try the next one
      continue;
    }
  }

  if (!foundAnyDir) {
    throw new Error(`Claude projects directory not found. Checked: ${projectsDirs.join(', ')}`);
  }

  return allEvents;
}

async function loadAllEventsWithoutTimeFilter(): Promise<SessionEvent[]> {
  const allEvents: SessionEvent[] = [];

  // Check both possible directories
  const projectsDirs = [
    join(homedir(), '.claude', 'projects'),
    join(homedir(), '.config', 'claude', 'projects'),
  ];

  let foundAnyDir = false;

  for (const projectsDir of projectsDirs) {
    try {
      const dirStat = await stat(projectsDir);
      if (!dirStat.isDirectory()) continue;

      foundAnyDir = true;

      const dirs = await readdir(projectsDir);

      for (const dir of dirs) {
        const dirPath = join(projectsDir, dir);
        try {
          const files = await readdir(dirPath);

          for (const file of files) {
            if (file.endsWith('.jsonl')) {
              const filePath = join(dirPath, file);

              // Parse all events without time filtering
              const events = await parseJSONLFileWithoutTimeFilter(filePath);
              allEvents.push(...events);
            }
          }
        } catch (error) {
          // Skip inaccessible directories
          continue;
        }
      }
    } catch (error) {
      // Directory doesn't exist, try the next one
      continue;
    }
  }

  if (!foundAnyDir) {
    throw new Error(`Claude projects directory not found. Checked: ${projectsDirs.join(', ')}`);
  }

  return allEvents;
}

async function parseJSONLFile(
  filePath: string,
  startTime: Date,
  endTime: Date
): Promise<SessionEvent[]> {
  // Check file modification time for performance optimization
  const stats = await stat(filePath);
  if (stats.mtime < startTime) {
    return [];
  }

  const content = await readFile(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const events: SessionEvent[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);

      // Validate and parse event
      const validationResult = SessionEventSchema.safeParse(data);
      if (!validationResult.success) {
        continue;
      }

      const event = validationResult.data;
      const eventTime = new Date(event.timestamp);

      // Convert to local time
      const localEventTime = new Date(eventTime.toLocaleString());

      if (localEventTime >= startTime && localEventTime <= endTime) {
        events.push({
          ...event,
          timestamp: eventTime.toISOString(),
        });
      }
    } catch (error) {
      // Skip invalid lines
      continue;
    }
  }

  return events;
}

async function parseJSONLFileWithoutTimeFilter(filePath: string): Promise<SessionEvent[]> {
  const content = await readFile(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const events: SessionEvent[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);

      // Validate and parse event
      const validationResult = SessionEventSchema.safeParse(data);
      if (!validationResult.success) {
        continue;
      }

      const event = validationResult.data;
      const eventTime = new Date(event.timestamp);

      events.push({
        ...event,
        timestamp: eventTime.toISOString(),
      });
    } catch (error) {
      // Skip invalid lines
      continue;
    }
  }

  return events;
}

// Main grouping function for consolidated mode (default)
async function groupEventsByRepositoryConsolidated(
  events: SessionEvent[]
): Promise<Map<string, SessionTimeline>> {
  const directoryEventMap = new Map<string, SessionEvent[]>();
  const repoDirectoryMap = new Map<string, string[]>();

  // Group events by directory first
  for (const event of events) {
    const directory = event.cwd || 'unknown';
    if (!directoryEventMap.has(directory)) {
      directoryEventMap.set(directory, []);
    }
    directoryEventMap.get(directory)!.push(event);
  }

  // Process each directory to get repository information
  for (const directory of directoryEventMap.keys()) {
    const repoName = getCachedRepositoryName(directory);

    if (!repoDirectoryMap.has(repoName)) {
      repoDirectoryMap.set(repoName, []);
    }
    repoDirectoryMap.get(repoName)!.push(directory);
  }

  const timelines = new Map<string, SessionTimeline>();

  for (const [repoName, directories] of repoDirectoryMap.entries()) {
    const allRepoEvents: SessionEvent[] = [];

    for (const directory of directories) {
      const events = directoryEventMap.get(directory) || [];
      allRepoEvents.push(...events);
    }

    if (allRepoEvents.length === 0) continue;

    // Sort events by timestamp
    allRepoEvents.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

    const timeline: SessionTimeline = {
      projectName: repoName,
      directory: '',
      repository: repoName,
      events: allRepoEvents,
      eventCount: allRepoEvents.length,
      activeDuration: calculateActiveDuration(allRepoEvents),
      startTime: new Date(allRepoEvents[0].timestamp),
      endTime: new Date(allRepoEvents[allRepoEvents.length - 1].timestamp),
    };

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
