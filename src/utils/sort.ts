import { SessionTimeline } from '../models/events';

export type SortOption =
  | 'project:asc'
  | 'project:desc'
  | 'created:asc'
  | 'created:desc'
  | 'events:asc'
  | 'events:desc'
  | 'duration:asc'
  | 'duration:desc';

export function sortTimelines(
  timelines: SessionTimeline[],
  sortOption: SortOption
): SessionTimeline[] {
  const sorted = [...timelines];

  switch (sortOption) {
    case 'project:asc':
      return sorted.sort((a, b) => a.projectName.localeCompare(b.projectName));

    case 'project:desc':
      return sorted.sort((a, b) => b.projectName.localeCompare(a.projectName));

    case 'created:asc':
      return sorted.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());

    case 'created:desc':
      return sorted.sort((a, b) => b.startTime.getTime() - a.startTime.getTime());

    case 'events:asc':
      return sorted.sort((a, b) => a.eventCount - b.eventCount);

    case 'events:desc':
      return sorted.sort((a, b) => b.eventCount - a.eventCount);

    case 'duration:asc':
      return sorted.sort((a, b) => a.activeDuration - b.activeDuration);

    case 'duration:desc':
      return sorted.sort((a, b) => b.activeDuration - a.activeDuration);

    default:
      return sorted;
  }
}
