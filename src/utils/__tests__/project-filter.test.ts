import { SessionTimeline } from '../../models/events';

// Helper function to simulate project filtering logic
function filterProjectsByNames(
  timelines: SessionTimeline[],
  projectNames: string[]
): SessionTimeline[] {
  if (projectNames.length === 0) {
    return timelines;
  }

  const projectFilters = projectNames.map(p => p.toLowerCase());
  return timelines.filter(session =>
    projectFilters.some(filter => session.projectName.toLowerCase().includes(filter))
  );
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

    it('should support case-insensitive filtering', () => {
      const result = filterProjectsByNames(mockTimelines, ['PROJECT-ALPHA']);
      expect(result).toHaveLength(1);
      expect(result[0].projectName).toBe('project-alpha');
    });

    it('should support case-insensitive filtering with mixed case input', () => {
      const result = filterProjectsByNames(mockTimelines, ['myproject']);
      expect(result).toHaveLength(1);
      expect(result[0].projectName).toBe('MyProject');
    });

    it('should support partial matching', () => {
      const result = filterProjectsByNames(mockTimelines, ['project']);
      expect(result).toHaveLength(4); // All 4 projects contain "project"
      const projectNames = result.map(t => t.projectName);
      expect(projectNames).toContain('project-alpha');
      expect(projectNames).toContain('project-beta');
      expect(projectNames).toContain('other-project');
      expect(projectNames).toContain('MyProject'); // MyProject also contains "project"
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

    it('should handle multiple filters with overlapping matches', () => {
      const result = filterProjectsByNames(mockTimelines, ['project', 'alpha']);
      expect(result).toHaveLength(4); // All projects match either "project" or "alpha"
      const projectNames = result.map(t => t.projectName);
      expect(projectNames).toContain('project-alpha');
      expect(projectNames).toContain('project-beta');
      expect(projectNames).toContain('other-project');
      expect(projectNames).toContain('MyProject');
    });

    it('should maintain original order of filtered results', () => {
      const result = filterProjectsByNames(mockTimelines, ['project']);
      const projectNames = result.map(t => t.projectName);
      expect(projectNames).toEqual(['project-alpha', 'project-beta', 'other-project', 'MyProject']);
    });

    it('should handle empty string filter', () => {
      const result = filterProjectsByNames(mockTimelines, ['']);
      expect(result).toHaveLength(4); // Empty string matches all projects
    });

    it('should handle whitespace in project filters', () => {
      const result = filterProjectsByNames(mockTimelines, [' project ']);
      expect(result).toHaveLength(0); // Whitespace-padded filter doesn't match any project names
    });
  });
});
