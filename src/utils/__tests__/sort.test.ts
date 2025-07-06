import { createSortOptions, sortTimelines, SortField, SortOrder } from '../sort';
import { Timeline } from '../../models/events';

// Mock session timeline data for testing
const createMockTimeline = (
  projectName: string,
  startTime: Date,
  eventCount: number,
  activeDuration: number
): Timeline => ({
  projectName,
  directory: `/path/to/${projectName}`,
  repository: `repo-${projectName}`,
  events: [],
  eventCount,
  activeDuration,
  startTime,
  endTime: new Date(startTime.getTime() + activeDuration * 60000), // Convert minutes to ms
});

const mockTimelines: Timeline[] = [
  createMockTimeline('beta-project', new Date('2025-01-02T10:00:00Z'), 50, 30),
  createMockTimeline('alpha-project', new Date('2025-01-01T09:00:00Z'), 100, 60),
  createMockTimeline('gamma-project', new Date('2025-01-03T11:00:00Z'), 25, 90),
];

describe('sort utilities', () => {
  describe('createSortOptions', () => {
    it('should return default options when no parameters provided', () => {
      const result = createSortOptions();
      expect(result).toEqual({
        field: 'timeline',
        order: 'asc',
      });
    });

    it('should return default field when invalid field provided', () => {
      const result = createSortOptions('invalid-field');
      expect(result).toEqual({
        field: 'timeline',
        order: 'asc',
      });
    });

    it('should return specified valid field with asc order', () => {
      const result = createSortOptions('project');
      expect(result).toEqual({
        field: 'project',
        order: 'asc',
      });
    });

    it('should return desc order when reverse is true', () => {
      const result = createSortOptions('events', true);
      expect(result).toEqual({
        field: 'events',
        order: 'desc',
      });
    });

    it('should handle all valid sort fields', () => {
      const validFields: SortField[] = ['project', 'timeline', 'events', 'duration'];

      validFields.forEach(field => {
        const result = createSortOptions(field);
        expect(result.field).toBe(field);
        expect(result.order).toBe('asc');
      });
    });
  });

  describe('sortTimelines', () => {
    it('should sort by project name ascending', () => {
      const sortOptions = { field: 'project' as SortField, order: 'asc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => t.projectName)).toEqual([
        'alpha-project',
        'beta-project',
        'gamma-project',
      ]);
    });

    it('should sort by project name descending', () => {
      const sortOptions = { field: 'project' as SortField, order: 'desc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => t.projectName)).toEqual([
        'gamma-project',
        'beta-project',
        'alpha-project',
      ]);
    });

    it('should sort by timeline (startTime) ascending', () => {
      const sortOptions = { field: 'timeline' as SortField, order: 'asc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => t.projectName)).toEqual([
        'alpha-project', // 2025-01-01
        'beta-project', // 2025-01-02
        'gamma-project', // 2025-01-03
      ]);
    });

    it('should sort by timeline (startTime) descending', () => {
      const sortOptions = { field: 'timeline' as SortField, order: 'desc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => t.projectName)).toEqual([
        'gamma-project', // 2025-01-03
        'beta-project', // 2025-01-02
        'alpha-project', // 2025-01-01
      ]);
    });

    it('should sort by events ascending', () => {
      const sortOptions = { field: 'events' as SortField, order: 'asc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => ({ name: t.projectName, events: t.eventCount }))).toEqual([
        { name: 'gamma-project', events: 25 },
        { name: 'beta-project', events: 50 },
        { name: 'alpha-project', events: 100 },
      ]);
    });

    it('should sort by events descending', () => {
      const sortOptions = { field: 'events' as SortField, order: 'desc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => ({ name: t.projectName, events: t.eventCount }))).toEqual([
        { name: 'alpha-project', events: 100 },
        { name: 'beta-project', events: 50 },
        { name: 'gamma-project', events: 25 },
      ]);
    });

    it('should sort by duration ascending', () => {
      const sortOptions = { field: 'duration' as SortField, order: 'asc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => ({ name: t.projectName, duration: t.activeDuration }))).toEqual([
        { name: 'beta-project', duration: 30 },
        { name: 'alpha-project', duration: 60 },
        { name: 'gamma-project', duration: 90 },
      ]);
    });

    it('should sort by duration descending', () => {
      const sortOptions = { field: 'duration' as SortField, order: 'desc' as SortOrder };
      const result = sortTimelines(mockTimelines, sortOptions);

      expect(result.map(t => ({ name: t.projectName, duration: t.activeDuration }))).toEqual([
        { name: 'gamma-project', duration: 90 },
        { name: 'alpha-project', duration: 60 },
        { name: 'beta-project', duration: 30 },
      ]);
    });

    it('should not mutate the original array', () => {
      const originalTimelines = [...mockTimelines];
      const sortOptions = { field: 'project' as SortField, order: 'asc' as SortOrder };

      sortTimelines(mockTimelines, sortOptions);

      expect(mockTimelines).toEqual(originalTimelines);
    });
  });
});
