import { readdir, readFile, stat } from 'fs/promises';
import { join, dirname, basename, relative } from 'path';
import { homedir } from 'os';
import { existsSync } from 'fs';
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
  endTime: Date,
  worktree: boolean
): Promise<SessionTimeline[]> {
  // Clear repository cache at the start of each execution
  clearRepositoryCache();

  const events = await loadAllEvents(startTime, endTime);
  const grouped = worktree
    ? await groupEventsByRepositoryWithChildren(events)
    : await groupEventsByRepositoryConsolidated(events);

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

// Worktree mode implementation with parent-child support
async function groupEventsByRepositoryWithChildren(
  events: SessionEvent[]
): Promise<Map<string, SessionTimeline>> {
  const directoryMap = new Map<string, SessionEvent[]>();
  const repoMap = new Map<string, Map<string, SessionEvent[]>>();

  // Group events by directory
  for (const event of events) {
    const directory = event.cwd || 'unknown';
    if (!directoryMap.has(directory)) {
      directoryMap.set(directory, []);
    }
    directoryMap.get(directory)!.push(event);
  }

  // Group directories by repository
  for (const [directory, directoryEvents] of directoryMap.entries()) {
    const repoName = getCachedRepositoryName(directory);

    if (!repoMap.has(repoName)) {
      repoMap.set(repoName, new Map());
    }
    repoMap.get(repoName)!.set(directory, directoryEvents);
  }

  const timelines = new Map<string, SessionTimeline>();

  for (const [repoName, repoDirs] of repoMap.entries()) {
    const directories = Array.from(repoDirs.keys());

    if (directories.length === 1) {
      // Single directory - create simple timeline
      const directory = directories[0];
      const events = repoDirs.get(directory)!;

      if (events.length === 0) continue;

      events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      const timeline: SessionTimeline = {
        projectName: repoName,
        directory,
        repository: repoName,
        events,
        eventCount: events.length,
        activeDuration: calculateActiveDuration(events),
        startTime: new Date(events[0].timestamp),
        endTime: new Date(events[events.length - 1].timestamp),
      };

      timelines.set(`${repoName}_${directory}`, timeline);
    } else {
      // Multiple directories - create parent and children
      const mainDir = findMainRepositoryDirectory(directories);

      // Create parent timeline
      if (repoDirs.has(mainDir)) {
        const mainEvents = repoDirs.get(mainDir)!;
        if (mainEvents.length > 0) {
          mainEvents.sort(
            (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          );

          const parentTimeline: SessionTimeline = {
            projectName: repoName,
            directory: mainDir,
            repository: repoName,
            events: mainEvents,
            eventCount: mainEvents.length,
            activeDuration: calculateActiveDuration(mainEvents),
            startTime: new Date(mainEvents[0].timestamp),
            endTime: new Date(mainEvents[mainEvents.length - 1].timestamp),
          };

          timelines.set(repoName, parentTimeline);
        }
      }

      // Create child timelines
      for (const [directory, events] of repoDirs.entries()) {
        if (directory === mainDir || events.length === 0) continue;

        events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

        const childName = generateChildProjectName(directory, mainDir);

        const childTimeline: SessionTimeline = {
          projectName: childName,
          directory,
          repository: repoName,
          isChild: true,
          events,
          eventCount: events.length,
          activeDuration: calculateActiveDuration(events),
          startTime: new Date(events[0].timestamp),
          endTime: new Date(events[events.length - 1].timestamp),
        };

        timelines.set(`${repoName}_${directory}`, childTimeline);
      }
    }
  }

  return sortTimelinesWithHierarchy(timelines);
}

// Find the main repository directory
function findMainRepositoryDirectory(directories: string[]): string {
  if (directories.length === 0) return '';

  // Sort by path length
  directories.sort((a, b) => a.length - b.length);

  // Prefer directories with .git
  for (const dir of directories) {
    if (existsSync(join(dir, '.git'))) {
      return dir;
    }
  }

  return directories[0];
}

// Generate meaningful child project name
function generateChildProjectName(childDir: string, parentDir: string): string {
  try {
    let relPath = relative(parentDir, childDir);
    relPath = relPath.replace(/^\.worktree\//, '');
    relPath = relPath.replace(/^\.git\/worktrees\//, '');

    const parts = relPath.split('/');
    if (parts.length > 0 && parts[parts.length - 1]) {
      return parts[parts.length - 1];
    }
  } catch (error) {
    // Fallback to basename
  }

  return basename(childDir);
}

// Sort timelines maintaining parent-child hierarchy
function sortTimelinesWithHierarchy(
  timelines: Map<string, SessionTimeline>
): Map<string, SessionTimeline> {
  const parentProjects: SessionTimeline[] = [];
  const childProjectsMap = new Map<string, SessionTimeline[]>();

  // Separate parents and children
  for (const timeline of timelines.values()) {
    if (!timeline.isChild) {
      parentProjects.push(timeline);
    } else {
      const parentName = timeline.repository!;
      if (!childProjectsMap.has(parentName)) {
        childProjectsMap.set(parentName, []);
      }
      childProjectsMap.get(parentName)!.push(timeline);
    }
  }

  // Sort parents by event count
  parentProjects.sort((a, b) => b.eventCount - a.eventCount);

  // Sort children within each parent
  for (const children of childProjectsMap.values()) {
    children.sort((a, b) => b.eventCount - a.eventCount);
  }

  // Build sorted result
  const sorted = new Map<string, SessionTimeline>();

  for (const parent of parentProjects) {
    sorted.set(parent.projectName, parent);

    const children = childProjectsMap.get(parent.projectName) || [];
    for (const child of children) {
      sorted.set(`${parent.projectName}_${child.directory}`, child);
    }
  }

  return sorted;
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
