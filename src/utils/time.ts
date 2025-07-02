import { subDays, subHours } from 'date-fns';
import type { CLIOptions, TimeRange } from '@/models';

export function getTimeRange(options: CLIOptions): TimeRange {
  const now = new Date();
  let start: Date;

  if (options.hours) {
    start = subHours(now, Number(options.hours));
  } else {
    const days = options.days ? Number(options.days) : 1;
    start = subDays(now, days);
  }

  return {
    start,
    end: now,
  };
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export function isWithinTimeRange(timestamp: string, range: TimeRange): boolean {
  const time = new Date(timestamp);
  return time >= range.start && time <= range.end;
}
