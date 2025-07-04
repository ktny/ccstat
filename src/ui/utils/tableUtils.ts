import { SessionTimeline } from '../../models/events';
import { format } from 'date-fns';

// Calculate optimal project column width
export function calculateProjectWidth(timelines: SessionTimeline[]): number {
  const minWidth = 20;
  const maxWidth = 30;

  if (timelines.length === 0) return minWidth;

  let maxNameLength = 0;
  for (const timeline of timelines) {
    let displayName = timeline.projectName;
    if (timeline.isChild) {
      displayName = ' └─' + timeline.projectName;
    }
    if (displayName.length > maxNameLength) {
      maxNameLength = displayName.length;
    }
  }

  const calculatedWidth = maxNameLength + 2;
  return Math.max(minWidth, Math.min(maxWidth, calculatedWidth));
}

// Create time axis with tick marks
export function createTimeAxis(startTime: Date, endTime: Date, width: number): string {
  const duration = endTime.getTime() - startTime.getTime();
  const axisChars = new Array(width).fill(' ');

  // Determine appropriate time format and interval
  const hours = duration / (1000 * 60 * 60);
  let interval: number;
  let formatStr: string;

  if (hours <= 2) {
    interval = 15 * 60 * 1000; // 15 minutes
    formatStr = 'HH:mm';
  } else if (hours <= 8) {
    interval = 60 * 60 * 1000; // 1 hour
    formatStr = 'HH';
  } else if (hours <= 48) {
    interval = 4 * 60 * 60 * 1000; // 4 hours
    formatStr = 'HH';
  } else {
    interval = 24 * 60 * 60 * 1000; // 1 day
    formatStr = 'MM/dd';
  }

  // Generate ticks
  const startTimestamp = startTime.getTime();
  let current = Math.ceil(startTimestamp / interval) * interval;

  while (current <= endTime.getTime()) {
    const position = Math.floor(((current - startTimestamp) / duration) * width);
    if (position >= 0 && position < width) {
      const tickTime = new Date(current);
      const label = format(tickTime, formatStr);

      // Place label centered on position
      const startPos = Math.max(
        0,
        Math.min(width - label.length, position - Math.floor(label.length / 2))
      );
      for (let i = 0; i < label.length && startPos + i < width; i++) {
        axisChars[startPos + i] = label[i];
      }
    }
    current += interval;
  }

  return axisChars.join('');
}
