import { readFile } from 'fs/promises';
import { join, dirname, basename } from 'path';
import { existsSync } from 'fs';

export function getRepositoryName(directory: string): string | null {
  const gitConfig = findGitConfig(directory);
  if (!gitConfig) {
    return null;
  }
  
  try {
    const configContent = readFileSync(gitConfig);
    const remoteUrl = extractRemoteUrl(configContent);
    if (remoteUrl) {
      return extractRepoName(remoteUrl);
    }
  } catch (error) {
    // Fallback to directory name
  }
  
  return basename(dirname(gitConfig));
}

function findGitConfig(directory: string): string | null {
  let currentDir = directory;
  
  while (currentDir !== '/' && currentDir) {
    const gitConfigPath = join(currentDir, '.git', 'config');
    if (existsSync(gitConfigPath)) {
      return gitConfigPath;
    }
    
    // Check for worktree
    const gitFilePath = join(currentDir, '.git');
    if (existsSync(gitFilePath)) {
      try {
        const gitFileContent = readFileSync(gitFilePath);
        const worktreeMatch = gitFileContent.match(/gitdir: (.+)/);
        if (worktreeMatch) {
          const worktreeGitDir = worktreeMatch[1];
          const worktreeConfigPath = join(worktreeGitDir, 'config');
          if (existsSync(worktreeConfigPath)) {
            return worktreeConfigPath;
          }
        }
      } catch (error) {
        // Continue searching
      }
    }
    
    currentDir = dirname(currentDir);
  }
  
  return null;
}

function readFileSync(filePath: string): string {
  const fs = require('fs');
  return fs.readFileSync(filePath, 'utf-8');
}

function extractRemoteUrl(configContent: string): string | null {
  const lines = configContent.split('\n');
  let inRemoteSection = false;
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    if (trimmed.startsWith('[remote')) {
      inRemoteSection = true;
    } else if (trimmed.startsWith('[')) {
      inRemoteSection = false;
    } else if (inRemoteSection && trimmed.startsWith('url =')) {
      return trimmed.substring(5).trim();
    }
  }
  
  return null;
}

function extractRepoName(url: string): string {
  // Handle SSH URLs (git@github.com:owner/repo.git)
  const sshMatch = url.match(/git@[^:]+:([^/]+\/[^.]+)/);
  if (sshMatch) {
    return sshMatch[1];
  }
  
  // Handle HTTPS URLs (https://github.com/owner/repo.git)
  const httpsMatch = url.match(/https?:\/\/[^/]+\/([^/]+\/[^.]+)/);
  if (httpsMatch) {
    return httpsMatch[1];
  }
  
  // Fallback: extract last two path components
  const parts = url.split('/');
  if (parts.length >= 2) {
    const repo = parts[parts.length - 1].replace(/\.git$/, '');
    const owner = parts[parts.length - 2];
    return `${owner}/${repo}`;
  }
  
  return url;
}