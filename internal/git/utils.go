package git

import (
	"bufio"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// GetRepositoryName extracts repository name from git config
func GetRepositoryName(directory string) string {
	gitPath := filepath.Join(directory, ".git")
	
	// Check if .git exists
	if _, err := os.Stat(gitPath); os.IsNotExist(err) {
		return ""
	}

	var configFile string

	// Handle git worktree case where .git is a file
	if fileInfo, err := os.Stat(gitPath); err == nil && !fileInfo.IsDir() {
		// Read gitdir path from .git file
		content, err := os.ReadFile(gitPath)
		if err != nil {
			return ""
		}

		gitContent := strings.TrimSpace(string(content))
		
		// Extract gitdir path (format: "gitdir: /path/to/actual/git/dir")
		if strings.HasPrefix(gitContent, "gitdir: ") {
			actualGitDir := gitContent[8:] // Remove "gitdir: " prefix
			
			// For worktree, check if commondir exists to find main git dir
			commondirFile := filepath.Join(actualGitDir, "commondir")
			if _, err := os.Stat(commondirFile); err == nil {
				commonContent, err := os.ReadFile(commondirFile)
				if err == nil {
					commonPath := strings.TrimSpace(string(commonContent))
					// Resolve relative path from worktree git dir
					mainGitDir := filepath.Join(actualGitDir, commonPath)
					configFile = filepath.Join(mainGitDir, "config")
				}
			} else {
				configFile = filepath.Join(actualGitDir, "config")
			}
		} else {
			return ""
		}
	} else {
		// Regular git repository
		configFile = filepath.Join(gitPath, "config")
	}

	// Check if config file exists
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		return ""
	}

	// Read config file
	file, err := os.Open(configFile)
	if err != nil {
		return ""
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	
	// Look for remote origin URL
	urlPattern := regexp.MustCompile(`url\s*=\s*(.+)`)
	
	for scanner.Scan() {
		line := scanner.Text()
		if matches := urlPattern.FindStringSubmatch(line); len(matches) > 1 {
			url := strings.TrimSpace(matches[1])
			
			// Extract repo name from various URL formats
			// SSH format: git@github.com:user/repo.git
			// HTTPS format: https://github.com/user/repo.git
			
			// SSH pattern
			sshPattern := regexp.MustCompile(`[^:/]+/([^/]+?)(?:\.git)?$`)
			if matches := sshPattern.FindStringSubmatch(url); len(matches) > 1 {
				return matches[1]
			}
			
			// HTTPS pattern
			httpsPattern := regexp.MustCompile(`/([^/]+?)(?:\.git)?$`)
			if matches := httpsPattern.FindStringSubmatch(url); len(matches) > 1 {
				return matches[1]
			}
		}
	}

	return ""
}