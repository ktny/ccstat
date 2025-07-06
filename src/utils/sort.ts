import { Timeline } from '../models/models';

export type SortField = 'project' | 'timeline' | 'events' | 'duration';
export type SortOrder = 'asc' | 'desc';

export interface SortOptions {
  field: SortField;
  order: SortOrder;
}

export function createSortOptions(field?: string, reverse?: boolean): SortOptions {
  const defaultField: SortField = 'timeline';
  const defaultOrder: SortOrder = 'asc';

  const validField = isValidSortField(field) ? field : defaultField;
  const order = reverse ? 'desc' : defaultOrder;

  return {
    field: validField,
    order: order,
  };
}

function isValidSortField(field?: string): field is SortField {
  return field === 'project' || field === 'timeline' || field === 'events' || field === 'duration';
}

export function sortTimelines(timelines: Timeline[], sortOptions: SortOptions): Timeline[] {
  const sorted = [...timelines];
  const { field, order } = sortOptions;

  const compare = (a: Timeline, b: Timeline): number => {
    let result: number;

    switch (field) {
      case 'project':
        result = a.projectName.localeCompare(b.projectName);
        break;

      case 'timeline':
        result = a.startTime.getTime() - b.startTime.getTime();
        break;

      case 'events':
        result = a.eventCount - b.eventCount;
        break;

      case 'duration':
        result = a.activeDuration - b.activeDuration;
        break;

      default:
        result = 0;
        break;
    }

    return order === 'desc' ? -result : result;
  };

  return sorted.sort(compare);
}
