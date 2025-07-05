import { SessionTimeline } from '../../models/events';
import { format } from 'date-fns';

interface TimeAxisFormat {
  formatStr: string;
  interval: number; // milliseconds
  displayName: string;
}

// Determine appropriate time axis format based on duration
function determineTimeAxisFormat(durationMs: number): TimeAxisFormat {
  const hours = durationMs / (1000 * 60 * 60);
  const days = hours / 24;

  if (hours <= 2) {
    // 1-2 hours: 15-minute intervals with HH:MM format
    return {
      formatStr: 'HH:mm',
      interval: 15 * 60 * 1000, // 15 minutes
      displayName: 'minutes',
    };
  } else if (hours <= 4) {
    // 3-4 hours: 30-minute intervals with HH:MM format
    return {
      formatStr: 'HH:mm',
      interval: 30 * 60 * 1000, // 30 minutes
      displayName: 'minutes',
    };
  } else if (hours <= 8) {
    // 5-8 hours: 1-hour intervals with HH:MM format
    return {
      formatStr: 'HH:mm',
      interval: 60 * 60 * 1000, // 1 hour
      displayName: 'hours',
    };
  } else if (hours <= 12) {
    // 9-12 hours: 2-hour intervals with HH format
    return {
      formatStr: 'HH',
      interval: 2 * 60 * 60 * 1000, // 2 hours
      displayName: 'hours',
    };
  } else if (days <= 2) {
    // 13 hours - 2 days: 4-hour intervals with HH format
    return {
      formatStr: 'HH',
      interval: 4 * 60 * 60 * 1000, // 4 hours
      displayName: 'hours',
    };
  } else if (days <= 7) {
    // 3-7 days: daily display with MM/DD format
    return {
      formatStr: 'MM/dd',
      interval: 24 * 60 * 60 * 1000, // 1 day
      displayName: 'days',
    };
  } else if (days <= 14) {
    // 8-14 days: 2-day intervals
    return {
      formatStr: 'MM/dd',
      interval: 2 * 24 * 60 * 60 * 1000, // 2 days
      displayName: 'days',
    };
  } else if (days <= 30) {
    // 15-30 days: 3-day intervals
    return {
      formatStr: 'MM/dd',
      interval: 3 * 24 * 60 * 60 * 1000, // 3 days
      displayName: 'days',
    };
  } else if (days <= 90) {
    // 31-90 days: weekly display
    return {
      formatStr: 'MM/dd',
      interval: 7 * 24 * 60 * 60 * 1000, // 1 week
      displayName: 'weeks',
    };
  } else if (days <= 365) {
    // 91-365 days: monthly display
    return {
      formatStr: 'MMM',
      interval: 30 * 24 * 60 * 60 * 1000, // ~1 month
      displayName: 'months',
    };
  } else {
    // 365+ days: yearly display
    return {
      formatStr: 'yyyy',
      interval: 365 * 24 * 60 * 60 * 1000, // 1 year
      displayName: 'years',
    };
  }
}

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

  // Get appropriate time format and interval using adaptive logic
  const timeFormat = determineTimeAxisFormat(duration);
  const { formatStr, interval } = timeFormat;

  // Generate ticks
  const startTimestamp = startTime.getTime();
  let current = Math.ceil(startTimestamp / interval) * interval;

  // Collect all labels first to check for overlaps
  const labels: Array<{ position: number; label: string; timestamp: number }> = [];

  while (current <= endTime.getTime()) {
    const position = Math.floor(((current - startTimestamp) / duration) * width);
    if (position >= 0 && position < width) {
      const tickTime = new Date(current);
      const label = format(tickTime, formatStr);
      labels.push({ position, label, timestamp: current });
    }
    current += interval;
  }

  // Filter overlapping labels with smart fitting
  const filteredLabels = [];

  // Try to fit as many labels as possible by selecting every Nth label if needed
  const labelLength = labels.length > 0 ? labels[0].label.length : 5;
  const minSpaceNeeded = labelLength + 1; // label + 1 space
  const maxPossibleLabels = Math.floor(width / minSpaceNeeded);

  if (labels.length <= maxPossibleLabels) {
    // We can fit all labels, use normal positioning
    let lastEndPos = -1;

    for (const labelInfo of labels) {
      const startPos = Math.max(
        0,
        Math.min(
          width - labelInfo.label.length,
          labelInfo.position - Math.floor(labelInfo.label.length / 2)
        )
      );
      const endPos = startPos + labelInfo.label.length - 1;

      if (startPos > lastEndPos + 1 || lastEndPos === -1) {
        filteredLabels.push({ ...labelInfo, startPos });
        lastEndPos = endPos;
      }
    }
  } else {
    // Too many labels, select every Nth label to fit
    const step = Math.max(1, Math.floor(labels.length / maxPossibleLabels));
    let lastEndPos = -1;

    for (let i = 0; i < labels.length; i += step) {
      const labelInfo = labels[i];
      const startPos = Math.max(
        0,
        Math.min(
          width - labelInfo.label.length,
          labelInfo.position - Math.floor(labelInfo.label.length / 2)
        )
      );
      const endPos = startPos + labelInfo.label.length - 1;

      if (startPos > lastEndPos + 1 || lastEndPos === -1) {
        filteredLabels.push({ ...labelInfo, startPos });
        lastEndPos = endPos;
      }
    }
  }

  // Place filtered labels
  for (const { startPos, label } of filteredLabels) {
    for (let i = 0; i < label.length && startPos + i < width; i++) {
      axisChars[startPos + i] = label[i];
    }
  }

  return axisChars.join('');
}
