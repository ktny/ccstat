import type { MessageEvent } from '@/models';

const INACTIVITY_THRESHOLD_MS = 3 * 60 * 1000; // 3 minutes in milliseconds
const MINIMUM_DURATION_MS = 5 * 60 * 1000; // 5 minutes minimum for single events

export function calculateActiveDuration(events: MessageEvent[]): number {
  if (events.length === 0) {
    return 0;
  }

  if (events.length === 1) {
    return MINIMUM_DURATION_MS / 1000; // Return 5 minutes for single events
  }

  // Sort events by timestamp to ensure proper ordering
  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  let totalActiveDuration = 0;

  for (let i = 0; i < sortedEvents.length - 1; i++) {
    const currentEvent = sortedEvents[i];
    const nextEvent = sortedEvents[i + 1];

    if (!currentEvent || !nextEvent) {
      continue;
    }

    const currentTime = new Date(currentEvent.timestamp).getTime();
    const nextTime = new Date(nextEvent.timestamp).getTime();
    const timeDiff = nextTime - currentTime;

    // Only count time between events if they're within the inactivity threshold
    if (timeDiff <= INACTIVITY_THRESHOLD_MS) {
      totalActiveDuration += timeDiff;
    }
  }

  // Ensure minimum duration
  return Math.max(totalActiveDuration / 1000, MINIMUM_DURATION_MS / 1000);
}

export function getSessionTimeRange(events: MessageEvent[]): { start: Date; end: Date } {
  if (events.length === 0) {
    const now = new Date();
    return { start: now, end: now };
  }

  const timestamps = events.map((event) => new Date(event.timestamp).getTime());
  const startTime = Math.min(...timestamps);
  const endTime = Math.max(...timestamps);

  return {
    start: new Date(startTime),
    end: new Date(endTime),
  };
}
