import { SessionTimeline } from '../../models/events';

// Helper function to simulate project filtering logic (exact match with case sensitivity)
function filterProjectsByNames(
  timelines: SessionTimeline[],
  projectNames: string[]
): SessionTimeline[] {
  if (projectNames.length === 0) {
    return timelines;
  }

  // Exact match with case sensitivity
  return timelines.filter(session => projectNames.some(filter => session.projectName === filter));
}

describe('Project filtering logic', () => {
  const mockTimelines: SessionTimeline[] = [
    {
      projectName: 'project-alpha',
      directory: '/path/to/alpha',
      repository: 'alpha-repo',
      events: [],
      eventCount: 100,
      activeDuration: 60,
      startTime: new Date('2025-01-01T10:00:00Z'),
      endTime: new Date('2025-01-01T11:00:00Z'),
    },
    {
      projectName: 'project-beta',
      directory: '/path/to/beta',
      repository: 'beta-repo',
      events: [],
      eventCount: 200,
      activeDuration: 120,
      startTime: new Date('2025-01-01T11:00:00Z'),
      endTime: new Date('2025-01-01T12:00:00Z'),
    },
    {
      projectName: 'other-project',
      directory: '/path/to/other',
      repository: 'other-repo',
      events: [],
      eventCount: 50,
      activeDuration: 30,
      startTime: new Date('2025-01-01T12:00:00Z'),
      endTime: new Date('2025-01-01T13:00:00Z'),
    },
    {
      projectName: 'MyProject',
      directory: '/path/to/myproject',
      repository: 'my-repo',
      events: [],
      eventCount: 75,
      activeDuration: 45,
      startTime: new Date('2025-01-01T13:00:00Z'),
      endTime: new Date('2025-01-01T14:00:00Z'),
    },
  ];

  describe('filterProjectsByNames', () => {
    it('should return all projects when no filter is specified', () => {
      const result = filterProjectsByNames(mockTimelines, []);
      expect(result).toHaveLength(4);
      expect(result).toEqual(mockTimelines);
    });

    it('should filter by exact project name match', () => {
      const result = filterProjectsByNames(mockTimelines, ['project-alpha']);
      expect(result).toHaveLength(1);
      expect(result[0].projectName).toBe('project-alpha');
    });

    it('should filter by multiple project names', () => {
      const result = filterProjectsByNames(mockTimelines, ['project-alpha', 'project-beta']);
      expect(result).toHaveLength(2);
      expect(result.map(t => t.projectName)).toEqual(['project-alpha', 'project-beta']);
    });

    it('should be case-sensitive (not match different case)', () => {
      const result = filterProjectsByNames(mockTimelines, ['PROJECT-ALPHA']);
      expect(result).toHaveLength(0); // Should not match due to case sensitivity
    });

    it('should be case-sensitive with mixed case projects', () => {
      const result = filterProjectsByNames(mockTimelines, ['MyProject']);
      expect(result).toHaveLength(1);
      expect(result[0].projectName).toBe('MyProject');

      // Should not match lowercase
      const result2 = filterProjectsByNames(mockTimelines, ['myproject']);
      expect(result2).toHaveLength(0);
    });

    it('should require exact match (not partial)', () => {
      const result = filterProjectsByNames(mockTimelines, ['project']);
      expect(result).toHaveLength(0); // Should not match any because "project" is not an exact match
    });

    it('should return empty array when no projects match', () => {
      const result = filterProjectsByNames(mockTimelines, ['nonexistent']);
      expect(result).toHaveLength(0);
    });

    it('should handle mixed existing and non-existing project names', () => {
      const result = filterProjectsByNames(mockTimelines, ['project-alpha', 'nonexistent']);
      expect(result).toHaveLength(1);
      expect(result[0].projectName).toBe('project-alpha');
    });

    it('should handle multiple exact matches', () => {
      const result = filterProjectsByNames(mockTimelines, ['project-alpha', 'MyProject']);
      expect(result).toHaveLength(2);
      const projectNames = result.map(t => t.projectName);
      expect(projectNames).toContain('project-alpha');
      expect(projectNames).toContain('MyProject');
    });

    it('should maintain original order of filtered results', () => {
      const result = filterProjectsByNames(mockTimelines, ['other-project', 'project-alpha']);
      const projectNames = result.map(t => t.projectName);
      expect(projectNames).toEqual(['project-alpha', 'other-project']); // Order based on original array order
    });

    it('should handle empty string filter', () => {
      const result = filterProjectsByNames(mockTimelines, ['']);
      expect(result).toHaveLength(0); // Empty string should not match any projects
    });

    it('should handle whitespace in project filters', () => {
      const result = filterProjectsByNames(mockTimelines, [' project ']);
      expect(result).toHaveLength(0); // Whitespace-padded filter doesn't match any project names
    });
  });
});
