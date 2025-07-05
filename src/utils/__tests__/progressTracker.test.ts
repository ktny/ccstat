import { ProgressTracker } from '../progressTracker';

describe('ProgressTracker', () => {
  it('should initialize with default values', () => {
    const tracker = new ProgressTracker();
    const update = tracker.getCurrentUpdate();

    expect(update.totalFiles).toBe(0);
    expect(update.processedFiles).toBe(0);
    expect(update.stage).toBe('discovering');
    expect(update.currentFile).toBeUndefined();
    expect(update.currentProject).toBeUndefined();
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

  it('should update stage correctly', () => {
    const tracker = new ProgressTracker();

    tracker.setStage('processing');
    expect(tracker.getCurrentUpdate().stage).toBe('processing');

    tracker.setStage('analyzing');
    expect(tracker.getCurrentUpdate().stage).toBe('analyzing');
  });

  it('should track current file and project', () => {
    const tracker = new ProgressTracker();

    tracker.setCurrentFile('/path/to/file.jsonl', 'my-project');
    const update = tracker.getCurrentUpdate();

    expect(update.currentFile).toBe('/path/to/file.jsonl');
    expect(update.currentProject).toBe('my-project');
  });

  it('should call callback when progress updates', () => {
    const callback = jest.fn();
    const tracker = new ProgressTracker(callback);

    tracker.setTotalFiles(5);
    expect(callback).toHaveBeenCalledWith(
      expect.objectContaining({
        totalFiles: 5,
        stage: 'processing',
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
    tracker.setCurrentFile('/path/file.jsonl', 'project');
    tracker.setStage('analyzing');

    tracker.reset();

    const update = tracker.getCurrentUpdate();
    expect(update.totalFiles).toBe(0);
    expect(update.processedFiles).toBe(0);
    expect(update.stage).toBe('discovering');
    expect(update.currentFile).toBeUndefined();
    expect(update.currentProject).toBeUndefined();
  });
});
