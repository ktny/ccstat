import { ProgressTracker } from '../progressTracker';

describe('ProgressTracker', () => {
  it('should initialize with default values', () => {
    const tracker = new ProgressTracker();
    const update = tracker.getCurrentUpdate();

    expect(update.totalFiles).toBe(0);
    expect(update.processedFiles).toBe(0);
  });

  it('should calculate progress percentage correctly', () => {
    const tracker = new ProgressTracker();

    expect(tracker.getProgressPercentage()).toBe(0);

    tracker.setTotalFiles(10);
    expect(tracker.getProgressPercentage()).toBe(0);

    tracker.incrementProcessedFiles();
    expect(tracker.getProgressPercentage()).toBe(10);

    tracker.incrementProcessedFiles();
    tracker.incrementProcessedFiles();
    expect(tracker.getProgressPercentage()).toBe(30);
  });

  it('should call callback when progress updates', () => {
    const callback = jest.fn();
    const tracker = new ProgressTracker(callback);

    tracker.setTotalFiles(5);
    expect(callback).toHaveBeenCalledWith(
      expect.objectContaining({
        totalFiles: 5,
      })
    );

    tracker.incrementProcessedFiles();
    expect(callback).toHaveBeenCalledWith(
      expect.objectContaining({
        processedFiles: 1,
      })
    );
  });

  it('should reset all values', () => {
    const tracker = new ProgressTracker();

    tracker.setTotalFiles(10);
    tracker.incrementProcessedFiles();

    tracker.reset();

    const update = tracker.getCurrentUpdate();
    expect(update.totalFiles).toBe(0);
    expect(update.processedFiles).toBe(0);
  });
});
