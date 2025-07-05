import { join } from 'path';
import { existsSync, readFileSync, statSync } from 'fs';

export function getRepositoryName(directory: string): string | null {
  try {
    const gitPath = join(directory, '.git');

    console.log(gitPath);

    // Check if .git exists
    if (!existsSync(gitPath)) {
      return null;
    }

    const stats = statSync(gitPath);
    let configFile: string;

    if (!stats.isDirectory()) {
      // Handle git worktree case where .git is a file
      const gitContent = readFileSync(gitPath, 'utf-8').trim();

      if (gitContent.startsWith('gitdir: ')) {
        const actualGitDir = gitContent.substring(8); // Remove "gitdir: " prefix

        // For worktree, check if commondir exists to find main git dir
        const commondirFile = join(actualGitDir, 'commondir');
        if (existsSync(commondirFile)) {
          const commonContent = readFileSync(commondirFile, 'utf-8').trim();
          const mainGitDir = join(actualGitDir, commonContent);
          configFile = join(mainGitDir, 'config');
        } else {
          configFile = join(actualGitDir, 'config');
        }
      } else {
        return null;
      }
    } else {
      // Regular git repository
      configFile = join(gitPath, 'config');
    }

    // Check if config file exists
    if (!existsSync(configFile)) {
      return null;
    }

    // Read config file
    const content = readFileSync(configFile, 'utf-8');
    return extractRepoNameFromConfig(content);
  } catch (error) {
    return null;
  }
}

function extractRepoNameFromConfig(content: string): string | null {
  const lines = content.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();

    // Look for URL lines
    const urlMatch = trimmed.match(/url\s*=\s*(.+)/);
    if (urlMatch) {
      const url = urlMatch[1].trim();
      const repoName = extractRepoNameFromURL(url);
      if (repoName) {
        return repoName;
      }
    }
  }

  return null;
}

function extractRepoNameFromURL(url: string): string | null {
  // SSH format: git@github.com:user/repo.git or git@github.com:user/repo
  const sshMatch = url.match(/[^:/]+\/([^/]+?)(?:\.git)?$/);
  if (sshMatch) {
    return sshMatch[1];
  }

  // HTTPS format: https://github.com/user/repo.git or https://github.com/user/repo
  const httpsMatch = url.match(/\/([^/]+?)(?:\.git)?$/);
  if (httpsMatch) {
    return httpsMatch[1];
  }

  return null;
}
