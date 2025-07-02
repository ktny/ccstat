import { promises as fs } from 'fs';
import { join, resolve } from 'path';
import { homedir } from 'os';
import type { TimeRange } from '@/models';

export const CLAUDE_PROJECTS_DIR = join(homedir(), '.claude', 'projects');

export async function findJSONLFiles(timeRange: TimeRange): Promise<string[]> {
  try {
    const projectsDir = CLAUDE_PROJECTS_DIR;
    const entries = await fs.readdir(projectsDir, { withFileTypes: true });
    const jsonlFiles: string[] = [];

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const projectDir = join(projectsDir, entry.name);
        try {
          const projectFiles = await fs.readdir(projectDir);

          for (const file of projectFiles) {
            if (file.endsWith('.jsonl')) {
              const filePath = join(projectDir, file);

              // Pre-filter by file modification time for performance
              const stats = await fs.stat(filePath);
              if (stats.mtime >= timeRange.start) {
                jsonlFiles.push(filePath);
              }
            }
          }
        } catch (error) {
          // Skip directories we can't read
          continue;
        }
      }
    }

    return jsonlFiles.sort();
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return []; // Claude projects directory doesn't exist
    }
    throw error;
  }
}

export async function fileExists(path: string): Promise<boolean> {
  try {
    await fs.access(path);
    return true;
  } catch {
    return false;
  }
}

export function resolveHomePath(path: string): string {
  if (path.startsWith('~/')) {
    return resolve(homedir(), path.slice(2));
  }
  return resolve(path);
}
