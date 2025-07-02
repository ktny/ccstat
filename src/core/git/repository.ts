import { promises as fs } from 'fs';
import { dirname, join, basename } from 'path';
import { simpleGit } from 'simple-git';

interface RepositoryInfo {
  name: string;
  path: string;
  isWorktree: boolean;
  parentRepo?: string | undefined;
}

const repoCache = new Map<string, RepositoryInfo>();

export async function getRepositoryName(directoryPath: string): Promise<RepositoryInfo> {
  // Check cache first
  if (repoCache.has(directoryPath)) {
    return repoCache.get(directoryPath)!;
  }

  try {
    const git = simpleGit(directoryPath);

    // Check if this directory is in a git repository
    const isRepo = await git.checkIsRepo();
    if (!isRepo) {
      const fallback = {
        name: basename(directoryPath),
        path: directoryPath,
        isWorktree: false,
      };
      repoCache.set(directoryPath, fallback);
      return fallback;
    }

    // Get the root directory of the git repository
    const rootDir = await git.revparse(['--show-toplevel']);

    // Check for .git file (indicates worktree)
    const gitPath = join(directoryPath, '.git');
    let isWorktree = false;
    let parentRepo: string | undefined;

    try {
      const gitStat = await fs.stat(gitPath);
      if (gitStat.isFile()) {
        // This is a worktree - read the .git file to find parent
        const gitContent = await fs.readFile(gitPath, 'utf8');
        const match = gitContent.match(/gitdir: (.+)/);
        if (match && match[1]) {
          isWorktree = true;
          // Extract parent repository name from worktree git directory
          const worktreeGitDir = match[1].trim();
          const parentGitDir = dirname(worktreeGitDir);
          if (parentGitDir.endsWith('/.git')) {
            parentRepo = basename(dirname(parentGitDir));
          }
        }
      }
    } catch {
      // Not a worktree or can't read .git file
    }

    // Try to get repository name from remote origin
    let repoName: string;
    try {
      const remotes = await git.getRemotes(true);
      const origin = remotes.find((remote) => remote.name === 'origin');

      if (origin?.refs.fetch) {
        repoName = extractRepoNameFromURL(origin.refs.fetch);
      } else {
        // Fall back to directory name
        repoName = basename(rootDir);
      }
    } catch {
      // Fall back to directory name if remote detection fails
      repoName = basename(rootDir);
    }

    const repoInfo: RepositoryInfo = {
      name: repoName,
      path: rootDir,
      isWorktree,
      parentRepo,
    };

    repoCache.set(directoryPath, repoInfo);
    return repoInfo;
  } catch (error) {
    // If git operations fail, fall back to directory name
    const fallback = {
      name: basename(directoryPath),
      path: directoryPath,
      isWorktree: false,
    };
    repoCache.set(directoryPath, fallback);
    return fallback;
  }
}

function extractRepoNameFromURL(url: string): string {
  // Handle various Git URL formats
  // SSH: git@github.com:user/repo.git
  // HTTPS: https://github.com/user/repo.git
  // Remove .git suffix and extract repo name

  let repoPath = url;

  // Remove .git suffix
  if (repoPath.endsWith('.git')) {
    repoPath = repoPath.slice(0, -4);
  }

  // Extract the last part of the path (repository name)
  if (repoPath.includes('/')) {
    const parts = repoPath.split('/');
    const lastPart = parts[parts.length - 1];
    return lastPart || 'unknown';
  }

  // Handle SSH format
  if (repoPath.includes(':')) {
    const parts = repoPath.split(':');
    const pathPart = parts[parts.length - 1];
    if (!pathPart) return 'unknown';
    return pathPart.split('/').pop() || 'unknown';
  }

  return 'unknown';
}

export function clearRepositoryCache(): void {
  repoCache.clear();
}
