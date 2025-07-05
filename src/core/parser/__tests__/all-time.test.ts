import { loadAllSessions, loadSessionsInTimeRange } from '../index';

describe('All-time functionality', () => {
  describe('loadAllSessions', () => {
    it('should load sessions without time filtering', async () => {
      // This test verifies that loadAllSessions function exists and can be called
      // The actual data loading will depend on the user's environment
      expect(typeof loadAllSessions).toBe('function');

      try {
        const sessions = await loadAllSessions();
        expect(Array.isArray(sessions)).toBe(true);

        // Each session should have required properties
        sessions.forEach(session => {
          expect(session).toHaveProperty('projectName');
          expect(session).toHaveProperty('events');
          expect(session).toHaveProperty('eventCount');
          expect(session).toHaveProperty('activeDuration');
          expect(session).toHaveProperty('startTime');
          expect(session).toHaveProperty('endTime');
          expect(typeof session.eventCount).toBe('number');
          expect(typeof session.activeDuration).toBe('number');
          expect(session.startTime instanceof Date).toBe(true);
          expect(session.endTime instanceof Date).toBe(true);
        });
      } catch (error) {
        // If no Claude data is available, that's expected in test environment
        if (
          error instanceof Error &&
          error.message.includes('Claude projects directory not found')
        ) {
          expect(error.message).toContain('Claude projects directory not found');
        } else {
          throw error;
        }
      }
    });

    it('should potentially return more sessions than time-restricted version', async () => {
      try {
        const allSessions = await loadAllSessions();

        // Test with a very restrictive time range (1 hour ago)
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        const restrictedSessions = await loadSessionsInTimeRange(oneHourAgo, now);

        // All-time should return the same or more sessions
        expect(allSessions.length).toBeGreaterThanOrEqual(restrictedSessions.length);
      } catch (error) {
        // If no Claude data is available, that's expected in test environment
        if (
          error instanceof Error &&
          error.message.includes('Claude projects directory not found')
        ) {
          expect(error.message).toContain('Claude projects directory not found');
        } else {
          throw error;
        }
      }
    });
  });
});
