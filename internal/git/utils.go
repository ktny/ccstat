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

	// Check if .git is a file (worktree case)
	fileInfo, err := os.Stat(gitPath)
	if err != nil {
		return ""
	}

	var configFile string

	if !fileInfo.IsDir() {
		// Handle git worktree case where .git is a file
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
	content, err := os.ReadFile(configFile)
	if err != nil {
		return ""
	}

	return extractRepoNameFromConfig(string(content))
}

// extractRepoNameFromConfig extracts repository name from git config content
func extractRepoNameFromConfig(content string) string {
	// Look for remote origin URL
	// Pattern matches lines like: url = git@github.com:user/repo.git
	// or: url = https://github.com/user/repo.git
	scanner := bufio.NewScanner(strings.NewReader(content))
	
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		
		// Look for URL lines
		urlRegex := regexp.MustCompile(`url\s*=\s*(.+)`)
		matches := urlRegex.FindStringSubmatch(line)
		
		if len(matches) > 1 {
			url := strings.TrimSpace(matches[1])
			
			// Extract repo name from various URL formats
			repoName := extractRepoNameFromURL(url)
			if repoName != "" {
				return repoName
			}
		}
	}
	
	return ""
}

// extractRepoNameFromURL extracts repository name from git URL
func extractRepoNameFromURL(url string) string {
	// SSH format: git@github.com:user/repo.git
	sshRegex := regexp.MustCompile(`[^:/]+/([^/]+?)(?:\.git)?$`)
	
	// HTTPS format: https://github.com/user/repo.git
	httpsRegex := regexp.MustCompile(`/([^/]+?)(?:\.git)?$`)
	
	// Try SSH pattern first
	if matches := sshRegex.FindStringSubmatch(url); len(matches) > 1 {
		return matches[1]
	}
	
	// Try HTTPS pattern
	if matches := httpsRegex.FindStringSubmatch(url); len(matches) > 1 {
		return matches[1]
	}
	
	return ""
}