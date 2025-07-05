export interface ProgressUpdate {
  totalFiles: number;
  processedFiles: number;
  currentFile?: string;
  currentProject?: string;
  stage: 'discovering' | 'processing' | 'analyzing' | 'complete';
}

export type ProgressCallback = (update: ProgressUpdate) => void;

export class ProgressTracker {
  private totalFiles: number = 0;
  private processedFiles: number = 0;
  private currentFile?: string;
  private currentProject?: string;
  private stage: ProgressUpdate['stage'] = 'discovering';
  private callback?: ProgressCallback;

  constructor(callback?: ProgressCallback) {
    this.callback = callback;
  }

  setTotalFiles(total: number): void {
    this.totalFiles = total;
    this.stage = 'processing';
    this.notifyCallback();
  }

  setCurrentFile(filePath: string, projectName?: string): void {
    this.currentFile = filePath;
    this.currentProject = projectName;
    this.notifyCallback();
  }

  incrementProcessedFiles(): void {
    this.processedFiles++;
    this.notifyCallback();
  }

  setStage(stage: ProgressUpdate['stage']): void {
    this.stage = stage;
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
      currentFile: this.currentFile,
      currentProject: this.currentProject,
      stage: this.stage,
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
    this.currentFile = undefined;
    this.currentProject = undefined;
    this.stage = 'discovering';
    this.notifyCallback();
  }
}
