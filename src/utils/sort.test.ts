import { sortTimelines } from './sort';
import { SessionTimeline } from '../models/events';

describe('sortTimelines', () => {
  const mockTimelines: SessionTimeline[] = [
    {
      projectName: 'Project B',
      directory: '/path/to/project-b',
      repository: 'repo-b',
      events: [],
      eventCount: 5,
      activeDuration: 1000,
      startTime: new Date('2025-01-01T10:00:00Z'),
      endTime: new Date('2025-01-01T11:00:00Z'),
    },
    {
      projectName: 'Project A',
      directory: '/path/to/project-a',
      repository: 'repo-a',
      events: [],
      eventCount: 10,
      activeDuration: 2000,
      startTime: new Date('2025-01-01T09:00:00Z'),
      endTime: new Date('2025-01-01T10:00:00Z'),
    },
    {
      projectName: 'Project C',
      directory: '/path/to/project-c',
      repository: 'repo-c',
      events: [],
      eventCount: 3,
      activeDuration: 500,
      startTime: new Date('2025-01-01T11:00:00Z'),
      endTime: new Date('2025-01-01T12:00:00Z'),
    },
  ];

  describe('project name sorting', () => {
    it('should sort by project name ascending', () => {
      const result = sortTimelines(mockTimelines, 'project:asc');
      expect(result[0].projectName).toBe('Project A');
      expect(result[1].projectName).toBe('Project B');
      expect(result[2].projectName).toBe('Project C');
    });

    it('should sort by project name descending', () => {
      const result = sortTimelines(mockTimelines, 'project:desc');
      expect(result[0].projectName).toBe('Project C');
      expect(result[1].projectName).toBe('Project B');
      expect(result[2].projectName).toBe('Project A');
    });
  });

  describe('created time sorting', () => {
    it('should sort by created time ascending (oldest first)', () => {
      const result = sortTimelines(mockTimelines, 'created:asc');
      expect(result[0].projectName).toBe('Project A'); // 09:00
      expect(result[1].projectName).toBe('Project B'); // 10:00
      expect(result[2].projectName).toBe('Project C'); // 11:00
    });

    it('should sort by created time descending (newest first)', () => {
      const result = sortTimelines(mockTimelines, 'created:desc');
      expect(result[0].projectName).toBe('Project C'); // 11:00
      expect(result[1].projectName).toBe('Project B'); // 10:00
      expect(result[2].projectName).toBe('Project A'); // 09:00
    });
  });

  describe('events count sorting', () => {
    it('should sort by events count ascending', () => {
      const result = sortTimelines(mockTimelines, 'events:asc');
      expect(result[0].eventCount).toBe(3);
      expect(result[1].eventCount).toBe(5);
      expect(result[2].eventCount).toBe(10);
    });

    it('should sort by events count descending', () => {
      const result = sortTimelines(mockTimelines, 'events:desc');
      expect(result[0].eventCount).toBe(10);
      expect(result[1].eventCount).toBe(5);
      expect(result[2].eventCount).toBe(3);
    });
  });

  describe('duration sorting', () => {
    it('should sort by duration ascending', () => {
      const result = sortTimelines(mockTimelines, 'duration:asc');
      expect(result[0].activeDuration).toBe(500);
      expect(result[1].activeDuration).toBe(1000);
      expect(result[2].activeDuration).toBe(2000);
    });

    it('should sort by duration descending', () => {
      const result = sortTimelines(mockTimelines, 'duration:desc');
      expect(result[0].activeDuration).toBe(2000);
      expect(result[1].activeDuration).toBe(1000);
      expect(result[2].activeDuration).toBe(500);
    });
  });

  describe('edge cases', () => {
    it('should handle empty array', () => {
      const result = sortTimelines([], 'project:asc');
      expect(result).toEqual([]);
    });

    it('should handle single item array', () => {
      const singleItem = [mockTimelines[0]];
      const result = sortTimelines(singleItem, 'project:asc');
      expect(result).toEqual(singleItem);
    });

    it('should not mutate the original array', () => {
      const originalOrder = mockTimelines.map(t => t.projectName);
      sortTimelines(mockTimelines, 'project:asc');
      const afterSortOrder = mockTimelines.map(t => t.projectName);
      expect(afterSortOrder).toEqual(originalOrder);
    });
  });
});
