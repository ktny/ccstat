// Performance measurement utilities

export class PerformanceTimer {
  private startTime: number = 0;
  private endTime: number = 0;

  start(): void {
    this.startTime = performance.now();
  }

  stop(): number {
    this.endTime = performance.now();
    return this.endTime - this.startTime;
  }

  get duration(): number {
    return this.endTime - this.startTime;
  }
}

export interface PerformanceMetrics {
  totalDuration: number;
  fileCount: number;
  eventCount: number;
  avgFileProcessingTime?: number;
  avgEventsPerFile?: number;
}

export function logPerformanceMetrics(label: string, metrics: PerformanceMetrics): void {
  if (process.env.NODE_ENV === 'development' || process.env.CCSTAT_DEBUG) {
    console.log(`[PERF] ${label}:`);
    console.log(`  Total duration: ${metrics.totalDuration.toFixed(2)}ms`);
    console.log(`  Files processed: ${metrics.fileCount}`);
    console.log(`  Events processed: ${metrics.eventCount}`);
    if (metrics.avgFileProcessingTime) {
      console.log(`  Avg file processing time: ${metrics.avgFileProcessingTime.toFixed(2)}ms`);
    }
    if (metrics.avgEventsPerFile) {
      console.log(`  Avg events per file: ${metrics.avgEventsPerFile.toFixed(1)}`);
    }
  }
}
