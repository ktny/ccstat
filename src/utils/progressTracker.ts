export interface ProgressUpdate {
  totalFiles: number;
  processedFiles: number;
}

export type ProgressCallback = (update: ProgressUpdate) => void;

export class ProgressTracker {
  private totalFiles: number = 0;
  private processedFiles: number = 0;
  private callback?: ProgressCallback;

  constructor(callback?: ProgressCallback) {
    this.callback = callback;
  }

  setTotalFiles(total: number): void {
    this.totalFiles = total;
    this.notifyCallback();
  }

  incrementProcessedFiles(): void {
    this.processedFiles++;
    this.notifyCallback();
  }

  getProgressPercentage(): number {
    if (this.totalFiles === 0) return 0;
    return Math.round((this.processedFiles / this.totalFiles) * 100);
  }

  getCurrentUpdate(): ProgressUpdate {
    return {
      totalFiles: this.totalFiles,
      processedFiles: this.processedFiles,
    };
  }

  private notifyCallback(): void {
    if (this.callback) {
      try {
        this.callback(this.getCurrentUpdate());
      } catch (error) {
        // Silently ignore callback errors to prevent breaking the loading process
        console.warn('Progress callback error:', error);
      }
    }
  }

  reset(): void {
    this.totalFiles = 0;
    this.processedFiles = 0;
    this.notifyCallback();
  }
}
