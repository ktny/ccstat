import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';
import { SessionEvent, SessionEventSchema, SessionTimeline } from '../../models/events';
import { getRepositoryName } from '../git';

const CLAUDE_PROJECTS_DIR = join(homedir(), '.claude', 'projects');
const INACTIVE_THRESHOLD_MINUTES = 3;

export async function loadSessionsInTimeRange(
  startTime: Date,
  endTime: Date,
  worktree: boolean
): Promise<SessionTimeline[]> {
  const events = await loadAllEvents(startTime, endTime);
  const grouped = groupEventsByProject(events, worktree);
  return calculateTimelines(grouped);
}

async function loadAllEvents(startTime: Date, endTime: Date): Promise<SessionEvent[]> {
  const allEvents: SessionEvent[] = [];

  try {
    const dirs = await readdir(CLAUDE_PROJECTS_DIR);

    console.log(`Found ${dirs.length} directories in Claude projects folder.`);

    for (const dir of dirs) {
      const dirPath = join(CLAUDE_PROJECTS_DIR, dir);
      const files = await readdir(dirPath);

      console.log(`Processing directory: ${dir} (${files.length} files)`);

      for (const file of files) {
        if (file.endsWith('.jsonl')) {
          const filePath = join(dirPath, file);
          const events = await parseJSONLFile(filePath, startTime, endTime);
          allEvents.push(...events);
        }
      }
    }
  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      throw new Error(`Claude projects directory not found: ${CLAUDE_PROJECTS_DIR}`);
    }
    throw error;
  }

  return allEvents;
}

async function parseJSONLFile(
  filePath: string,
  startTime: Date,
  endTime: Date
): Promise<SessionEvent[]> {
  const content = await readFile(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const events: SessionEvent[] = [];

  for (const line of lines) {
    try {
      const data = JSON.parse(line);
      const event = SessionEventSchema.parse(data);
      const eventTime = new Date(event.timestamp);

      if (eventTime >= startTime && eventTime <= endTime) {
        events.push(event);
      }
    } catch (error) {
      // Skip invalid lines
    }
  }

  return events;
}

function groupEventsByProject(
  events: SessionEvent[],
  worktree: boolean
): Map<string, SessionEvent[]> {
  const grouped = new Map<string, SessionEvent[]>();

  for (const event of events) {
    const key = worktree ? event.cwd : (getRepositoryName(event.cwd) || event.cwd);

    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key)!.push(event);
  }

  return grouped;
}

function calculateTimelines(grouped: Map<string, SessionEvent[]>): SessionTimeline[] {
  const timelines: SessionTimeline[] = [];

  for (const [key, events] of grouped.entries()) {
    if (events.length === 0) continue;

    const sortedEvents = events.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const startTime = new Date(sortedEvents[0].timestamp);
    const endTime = new Date(sortedEvents[sortedEvents.length - 1].timestamp);
    const activeDuration = calculateActiveDuration(sortedEvents);

    timelines.push({
      projectName: key.split('/').pop() || key,
      directory: events[0].cwd,
      repository: getRepositoryName(events[0].cwd),
      events: sortedEvents,
      eventCount: events.length,
      activeDuration,
      startTime,
      endTime,
    });
  }

  return timelines.sort((a, b) => b.eventCount - a.eventCount);
}

function calculateActiveDuration(events: SessionEvent[]): number {
  if (events.length === 0) return 0;
  if (events.length === 1) return 5; // Minimum 5 minutes for single event

  let totalMinutes = 0;

  for (let i = 1; i < events.length; i++) {
    const prevTime = new Date(events[i - 1].timestamp);
    const currTime = new Date(events[i].timestamp);
    const diffMinutes = (currTime.getTime() - prevTime.getTime()) / (1000 * 60);

    if (diffMinutes <= INACTIVE_THRESHOLD_MINUTES) {
      totalMinutes += diffMinutes;
    }
  }

  return Math.round(totalMinutes);
}
