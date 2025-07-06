import { loadTimelines } from '../index';

describe('All-time functionality', () => {
  describe('loadTimelines', () => {
    it('should load timelines without time filtering', async () => {
      // This test verifies that loadTimelines function exists and can be called
      // The actual data loading will depend on the user's environment
      expect(typeof loadTimelines).toBe('function');

      try {
        const timelines = await loadTimelines();
        expect(Array.isArray(timelines)).toBe(true);

        // Each timeline should have required properties
        timelines.forEach(timeline => {
          expect(timeline).toHaveProperty('projectName');
          expect(timeline).toHaveProperty('events');
          expect(timeline).toHaveProperty('eventCount');
          expect(timeline).toHaveProperty('activeDuration');
          expect(timeline).toHaveProperty('startTime');
          expect(timeline).toHaveProperty('endTime');
          expect(typeof timeline.projectName).toBe('string');
          expect(typeof timeline.eventCount).toBe('number');
          expect(typeof timeline.activeDuration).toBe('number');
          expect(timeline.startTime instanceof Date).toBe(true);
          expect(timeline.endTime instanceof Date).toBe(true);
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

    it('should potentially return more timelines than time-restricted version', async () => {
      try {
        const allTimelines = await loadTimelines();

        // Test with a very restrictive time range (1 hour ago)
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        const restrictedTimelines = await loadTimelines(oneHourAgo, now);

        // All-time should return the same or more timelines
        expect(allTimelines.length).toBeGreaterThanOrEqual(restrictedTimelines.length);
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
