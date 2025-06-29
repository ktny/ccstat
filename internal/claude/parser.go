package claude

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/ktny/ccstat/internal/git"
	"github.com/ktny/ccstat/pkg/models"
)

// ParseJSONLFile parses a JSONL file and extracts session events
func ParseJSONLFile(filePath string, debug bool) ([]*models.SessionEvent, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = file.Close() // Ignore error in defer
	}()

	var events []*models.SessionEvent
	scanner := bufio.NewScanner(file)
	// Increase buffer size to handle large JSON lines (1MB)
	const maxScanTokenSize = 1024 * 1024
	buf := make([]byte, maxScanTokenSize)
	scanner.Buffer(buf, maxScanTokenSize)
	lineNum := 0
	skippedCount := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(line), &data); err != nil {
			// Skip malformed lines
			skippedCount++
			if debug && len(line) > 1000 {
				fmt.Printf("DEBUG: Skipped line %d due to JSON error (line length: %d): %v\n", lineNum, len(line), err)
			}
			continue
		}

		// Extract timestamp
		timestampStr, ok := data["timestamp"].(string)
		if !ok {
			skippedCount++
			continue
		}

		// Parse ISO format timestamp and convert to local time
		timestamp, err := time.Parse(time.RFC3339, timestampStr)
		if err != nil {
			skippedCount++
			continue
		}

		// Convert UTC to local timezone
		timestamp = timestamp.Local()

		// Extract message content and role
		var messageType string
		var rawMessage map[string]interface{}

		if message, ok := data["message"].(map[string]interface{}); ok {
			rawMessage = message
			if role, ok := message["role"].(string); ok {
				messageType = role
			}
		}

		if messageType == "" {
			if msgType, ok := data["type"].(string); ok {
				messageType = msgType
			} else {
				messageType = "unknown"
			}
		}

		event := &models.SessionEvent{
			Timestamp:   timestamp,
			SessionID:   getStringValue(data, "sessionId"),
			Directory:   getStringValue(data, "cwd"),
			MessageType: messageType,
			UUID:        getStringValue(data, "uuid"),
			RawMessage:  rawMessage,
		}

		// Create content preview
		event.CreateContentPreview()

		events = append(events, event)
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	// Debug: log if we skipped many lines
	if debug && skippedCount > 0 {
		fmt.Printf("DEBUG: File %s - Total lines: %d, Events parsed: %d, Skipped: %d\n",
			filepath.Base(filePath), lineNum, len(events), skippedCount)
	}

	return events, nil
}

// GetAllSessionFiles returns all Claude session JSONL files
func GetAllSessionFiles() ([]string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	// Check both possible directories
	projectsDirs := []string{
		filepath.Join(homeDir, ".claude", "projects"),
		filepath.Join(homeDir, ".config", "claude", "projects"),
	}

	var jsonlFiles []string

	for _, projectsDir := range projectsDirs {
		if _, err := os.Stat(projectsDir); os.IsNotExist(err) {
			continue
		}

		err = filepath.Walk(projectsDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if !info.IsDir() && strings.HasSuffix(path, ".jsonl") {
				jsonlFiles = append(jsonlFiles, path)
			}

			return nil
		})

		if err != nil {
			return nil, err
		}
	}

	return jsonlFiles, nil
}

// LoadSessionsInTimeRange loads all Claude sessions within a time range, grouped by project directory
func LoadSessionsInTimeRange(startTime, endTime time.Time, projectFilter string, threads bool, debug bool) ([]*models.SessionTimeline, error) {
	var allEvents []*models.SessionEvent

	// Get all JSONL files
	jsonlFiles, err := GetAllSessionFiles()
	if err != nil {
		return nil, err
	}

	if debug {
		fmt.Printf("DEBUG: Found %d JSONL files\n", len(jsonlFiles))
	}

	// Parse each file and collect events (with mtime filtering)
	for _, filePath := range jsonlFiles {
		// Check file modification time for performance optimization
		fileInfo, err := os.Stat(filePath)
		if err != nil {
			continue
		}

		// Skip files that were last modified before the start time
		if fileInfo.ModTime().Before(startTime) {
			continue
		}

		events, err := ParseJSONLFile(filePath, debug)
		if err != nil {
			continue // Skip files that can't be parsed
		}

		allEvents = append(allEvents, events...)
	}

	// Filter events by time range
	var filteredEvents []*models.SessionEvent
	for _, event := range allEvents {
		if !event.Timestamp.Before(startTime) && !event.Timestamp.After(endTime) {
			filteredEvents = append(filteredEvents, event)
		}
	}

	if debug {
		fmt.Printf("DEBUG: Total events parsed: %d\n", len(allEvents))
		fmt.Printf("DEBUG: Events after time filter: %d\n", len(filteredEvents))
		fmt.Printf("DEBUG: Time range: %s to %s\n", startTime.Format(time.RFC3339), endTime.Format(time.RFC3339))
		fmt.Printf("DEBUG: Project filter: '%s'\n", projectFilter)
	}

	// Sort events by timestamp
	sort.Slice(filteredEvents, func(i, j int) bool {
		return filteredEvents[i].Timestamp.Before(filteredEvents[j].Timestamp)
	})

	// Group events by project directory
	timelines, err := groupEventsByProject(filteredEvents, threads, debug)
	if err != nil {
		return nil, err
	}

	// Apply project filter if specified
	if projectFilter != "" {
		var filteredTimelines []*models.SessionTimeline
		for _, timeline := range timelines {
			if strings.Contains(strings.ToLower(timeline.ProjectName), strings.ToLower(projectFilter)) {
				filteredTimelines = append(filteredTimelines, timeline)
				if debug {
					fmt.Printf("DEBUG: Timeline '%s' matches filter '%s'\n", timeline.ProjectName, projectFilter)
				}
			} else if debug {
				fmt.Printf("DEBUG: Timeline '%s' does NOT match filter '%s'\n", timeline.ProjectName, projectFilter)
			}
		}
		if debug {
			fmt.Printf("DEBUG: Total timelines: %d, Filtered timelines: %d\n", len(timelines), len(filteredTimelines))
		}
		return filteredTimelines, nil
	}

	return timelines, nil
}

// CalculateActiveDuration calculates active work duration based on event intervals
func CalculateActiveDuration(events []*models.SessionEvent) int {
	if len(events) <= 1 {
		return 5 // Minimum 5 minutes for single event
	}

	// Sort events by timestamp
	sort.Slice(events, func(i, j int) bool {
		return events[i].Timestamp.Before(events[j].Timestamp)
	})

	activeMinutes := 0.0
	inactiveThreshold := 3.0 // 3 minute threshold for inactive periods

	for i := 1; i < len(events); i++ {
		prevEvent := events[i-1]
		currEvent := events[i]

		intervalMinutes := currEvent.Timestamp.Sub(prevEvent.Timestamp).Minutes()

		// Only count intervals up to the threshold as active time
		if intervalMinutes <= inactiveThreshold {
			activeMinutes += intervalMinutes
		}
		// If interval is longer than threshold, don't add any time
		// (this represents an inactive period)
	}

	return int(activeMinutes)
}

// Helper function to safely get string values from map
func getStringValue(data map[string]interface{}, key string) string {
	if value, ok := data[key].(string); ok {
		return value
	}
	return ""
}

// groupEventsByProject groups events by project directory or git repository based on threads flag
func groupEventsByProject(events []*models.SessionEvent, threads bool, debug bool) ([]*models.SessionTimeline, error) {
	if threads {
		// threads=true (worktree mode): group by git repository with child project support
		return groupEventsByRepositoryWithChildren(events, debug)
	} else {
		// threads=false (default): consolidate by git repository
		return groupEventsByRepositoryConsolidated(events, debug)
	}
}

// groupEventsByRepositoryConsolidated consolidates events by git repository (default mode)
func groupEventsByRepositoryConsolidated(events []*models.SessionEvent, debug bool) ([]*models.SessionTimeline, error) {
	// First group events by directory, then by repository
	directoryEventMap := make(map[string][]*models.SessionEvent)
	repoDirectoryMap := make(map[string][]string)

	for _, event := range events {
		directory := event.Directory
		if directory == "" {
			directory = "unknown"
		}

		// Get repository name for this directory
		repoName := git.GetRepositoryName(directory)
		if debug {
			fmt.Printf("DEBUG: Directory '%s' -> git.GetRepositoryName() = '%s'\n", directory, repoName)
		}
		if repoName == "" {
			// Try to find parent repository by walking up the directory tree
			repoName = findParentRepository(directory)
			if debug {
				fmt.Printf("DEBUG: Directory '%s' -> findParentRepository() = '%s'\n", directory, repoName)
			}
			if repoName == "" {
				repoName = filepath.Base(directory) // fallback to directory name
				if debug {
					fmt.Printf("DEBUG: Directory '%s' -> fallback to base name = '%s'\n", directory, repoName)
				}
			}
		}
		if debug {
			fmt.Printf("DEBUG: Final mapping: Directory '%s' -> Repository '%s' (events: %d)\n", directory, repoName, 1)
		}

		// Group by directory first
		directoryEventMap[directory] = append(directoryEventMap[directory], event)

		// Track which directories belong to which repository
		found := false
		for _, existingDir := range repoDirectoryMap[repoName] {
			if existingDir == directory {
				found = true
				break
			}
		}
		if !found {
			repoDirectoryMap[repoName] = append(repoDirectoryMap[repoName], directory)
		}
	}

	var timelines []*models.SessionTimeline

	for repoName, directories := range repoDirectoryMap {
		if len(directories) == 0 {
			continue
		}

		// Collect all events from all directories
		var allRepoEvents []*models.SessionEvent

		// Collect events from all directories
		for _, directory := range directories {
			directoryEvents := directoryEventMap[directory]
			if len(directoryEvents) == 0 {
				continue
			}

			// Add to all events
			allRepoEvents = append(allRepoEvents, directoryEvents...)

			if debug {
				fmt.Printf("DEBUG: Directory '%s' has %d events\n", directory, len(directoryEvents))
			}
		}

		if len(allRepoEvents) == 0 {
			continue
		}

		// Sort all events by timestamp for proper start/end time calculation
		sort.Slice(allRepoEvents, func(i, j int) bool {
			return allRepoEvents[i].Timestamp.Before(allRepoEvents[j].Timestamp)
		})

		// Calculate total duration from all consolidated events
		totalDuration := CalculateActiveDuration(allRepoEvents)

		// Create consolidated timeline for this repository
		timeline := &models.SessionTimeline{
			SessionID:             fmt.Sprintf("repo_%s", repoName),
			Directory:             "", // No specific directory for consolidated repo
			ProjectName:           repoName,
			Events:                allRepoEvents,
			StartTime:             allRepoEvents[0].Timestamp,
			EndTime:               allRepoEvents[len(allRepoEvents)-1].Timestamp,
			ActiveDurationMinutes: totalDuration, // Use calculated duration from all events
		}

		if debug {
			fmt.Printf("DEBUG: Repository '%s' total events: %d, total duration: %d minutes (from %d directories)\n", repoName, len(allRepoEvents), totalDuration, len(directories))
		}

		timelines = append(timelines, timeline)
	}

	// Sort by event count (descending)
	sort.Slice(timelines, func(i, j int) bool {
		return len(timelines[i].Events) > len(timelines[j].Events)
	})

	return timelines, nil
}

// findParentRepository walks up the directory tree to find a parent git repository
func findParentRepository(directory string) string {
	// Clean the directory path
	cleanPath := filepath.Clean(directory)

	// Walk up the directory tree
	for {
		parentDir := filepath.Dir(cleanPath)

		// If we've reached the root or can't go further up, stop
		if parentDir == cleanPath || parentDir == "/" || parentDir == "." {
			break
		}

		// Try to get repository name from parent directory
		repoName := git.GetRepositoryName(parentDir)
		if repoName != "" {
			return repoName
		}

		cleanPath = parentDir
	}

	return ""
}

// findMainRepositoryDirectory identifies the main repository directory from a list of directories
func findMainRepositoryDirectory(directories []string) string {
	if len(directories) == 0 {
		return ""
	}

	// Sort by path length to prioritize shorter paths (likely main directories)
	sort.Slice(directories, func(i, j int) bool {
		return len(directories[i]) < len(directories[j])
	})

	for _, dir := range directories {
		// Prefer directories that directly contain .git (not worktree subdirectories)
		gitPath := filepath.Join(dir, ".git")
		if info, err := os.Stat(gitPath); err == nil && info.IsDir() {
			return dir
		}
	}

	// If no direct .git directory found, return the shortest path
	return directories[0]
}

// generateChildProjectName generates a meaningful name for child projects
func generateChildProjectName(childDir, parentDir string) string {
	// Try to extract a meaningful name from the path difference
	relPath, err := filepath.Rel(parentDir, childDir)
	if err != nil {
		return filepath.Base(childDir)
	}

	// Remove common prefixes like .worktree/
	relPath = strings.TrimPrefix(relPath, ".worktree/")
	relPath = strings.TrimPrefix(relPath, ".git/worktrees/")

	// If the relative path has multiple components, use the last meaningful part
	parts := strings.Split(relPath, string(filepath.Separator))
	if len(parts) > 0 && parts[len(parts)-1] != "" {
		return parts[len(parts)-1]
	}

	return filepath.Base(childDir)
}

// groupEventsByRepositoryWithChildren groups events by git repository with child project support (worktree mode)
func groupEventsByRepositoryWithChildren(events []*models.SessionEvent, debug bool) ([]*models.SessionTimeline, error) {
	// First, group by directory to collect events
	directoryMap := make(map[string][]*models.SessionEvent)

	for _, event := range events {
		directory := event.Directory
		if directory == "" {
			directory = "unknown"
		}
		directoryMap[directory] = append(directoryMap[directory], event)
	}

	// Then, group directories by git repository
	repoMap := make(map[string]map[string][]*models.SessionEvent)
	directoryToRepo := make(map[string]string)

	for directory, directoryEvents := range directoryMap {
		repoName := git.GetRepositoryName(directory)
		if debug {
			fmt.Printf("DEBUG: Directory '%s' -> git.GetRepositoryName() = '%s'\n", directory, repoName)
		}

		if repoName == "" {
			// Try to find parent repository by walking up the directory tree
			repoName = findParentRepository(directory)
			if debug {
				fmt.Printf("DEBUG: Directory '%s' -> findParentRepository() = '%s'\n", directory, repoName)
			}

			if repoName == "" {
				repoName = filepath.Base(directory) // fallback to directory name
				if debug {
					fmt.Printf("DEBUG: Directory '%s' -> fallback to base name = '%s'\n", directory, repoName)
				}
			}
		}
		if debug {
			fmt.Printf("DEBUG: Final mapping: Directory '%s' -> Repository '%s' (events: %d)\n", directory, repoName, len(directoryEvents))
		}

		if repoMap[repoName] == nil {
			repoMap[repoName] = make(map[string][]*models.SessionEvent)
		}
		repoMap[repoName][directory] = directoryEvents
		directoryToRepo[directory] = repoName
	}

	var timelines []*models.SessionTimeline

	for repoName, repoDirs := range repoMap {
		// If only one directory in this repo, treat as single project
		if len(repoDirs) == 1 {
			for directory, projectEvents := range repoDirs {
				if len(projectEvents) == 0 {
					continue
				}

				// Sort events by timestamp
				sort.Slice(projectEvents, func(i, j int) bool {
					return projectEvents[i].Timestamp.Before(projectEvents[j].Timestamp)
				})

				timeline := &models.SessionTimeline{
					SessionID:             fmt.Sprintf("repo_%s", repoName),
					Directory:             directory,
					ProjectName:           repoName,
					Events:                projectEvents,
					StartTime:             projectEvents[0].Timestamp,
					EndTime:               projectEvents[len(projectEvents)-1].Timestamp,
					ActiveDurationMinutes: CalculateActiveDuration(projectEvents),
				}

				timelines = append(timelines, timeline)
			}
		} else {
			// Multiple directories in same repo: create parent and child projects
			// First, identify the main repository directory
			var directories []string
			for directory := range repoDirs {
				directories = append(directories, directory)
			}

			mainDir := findMainRepositoryDirectory(directories)
			mainDirEvents, hasMainDir := repoDirs[mainDir]

			// Create parent project with main directory events only
			if hasMainDir && len(mainDirEvents) > 0 {
				// Sort events by timestamp
				sort.Slice(mainDirEvents, func(i, j int) bool {
					return mainDirEvents[i].Timestamp.Before(mainDirEvents[j].Timestamp)
				})

				parentTimeline := &models.SessionTimeline{
					SessionID:             fmt.Sprintf("repo_%s", repoName),
					Directory:             mainDir,
					ProjectName:           repoName,
					Events:                mainDirEvents,
					StartTime:             mainDirEvents[0].Timestamp,
					EndTime:               mainDirEvents[len(mainDirEvents)-1].Timestamp,
					ActiveDurationMinutes: CalculateActiveDuration(mainDirEvents),
				}

				timelines = append(timelines, parentTimeline)
			}

			// Then, create child projects for non-main directories
			for directory, projectEvents := range repoDirs {
				// Skip the main directory (already processed as parent)
				if directory == mainDir {
					continue
				}

				if len(projectEvents) == 0 {
					continue
				}

				// Sort events by timestamp
				sort.Slice(projectEvents, func(i, j int) bool {
					return projectEvents[i].Timestamp.Before(projectEvents[j].Timestamp)
				})

				// Generate meaningful child project name
				childName := generateChildProjectName(directory, mainDir)

				// Skip if child has the same name as parent (avoid duplication)
				if childName == repoName {
					continue
				}

				childTimeline := &models.SessionTimeline{
					SessionID:             fmt.Sprintf("dir_%s", directory),
					Directory:             directory,
					ProjectName:           childName,
					Events:                projectEvents,
					StartTime:             projectEvents[0].Timestamp,
					EndTime:               projectEvents[len(projectEvents)-1].Timestamp,
					ActiveDurationMinutes: CalculateActiveDuration(projectEvents),
					ParentProject:         &repoName, // Set parent project name
				}

				timelines = append(timelines, childTimeline)
			}
		}
	}

	// Sort by parent-child relationships first, then by event count
	return sortTimelinesWithProperHierarchy(timelines, debug), nil
}

// sortTimelinesWithProperHierarchy sorts timelines maintaining proper parent-child relationships
func sortTimelinesWithProperHierarchy(timelines []*models.SessionTimeline, debug bool) []*models.SessionTimeline {
	// Group timelines by parent-child relationships
	parentProjects := make([]*models.SessionTimeline, 0)
	childProjectsMap := make(map[string][]*models.SessionTimeline)

	for _, timeline := range timelines {
		if timeline.ParentProject == nil {
			// This is a parent project
			parentProjects = append(parentProjects, timeline)
			if debug {
				fmt.Printf("DEBUG: Parent project: '%s' (events: %d)\n", timeline.ProjectName, len(timeline.Events))
			}
		} else {
			// This is a child project
			parentName := *timeline.ParentProject
			if childProjectsMap[parentName] == nil {
				childProjectsMap[parentName] = make([]*models.SessionTimeline, 0)
			}
			childProjectsMap[parentName] = append(childProjectsMap[parentName], timeline)
			if debug {
				fmt.Printf("DEBUG: Child project: '%s' -> Parent: '%s' (events: %d)\n", timeline.ProjectName, parentName, len(timeline.Events))
			}
		}
	}

	// Sort parent projects by event count (descending)
	sort.Slice(parentProjects, func(i, j int) bool {
		return len(parentProjects[i].Events) > len(parentProjects[j].Events)
	})

	// Sort child projects within each parent group by event count (descending)
	for _, children := range childProjectsMap {
		sort.Slice(children, func(i, j int) bool {
			return len(children[i].Events) > len(children[j].Events)
		})
	}

	// Build final sorted list: parent followed by its children
	result := make([]*models.SessionTimeline, 0, len(timelines))

	for _, parent := range parentProjects {
		result = append(result, parent)

		// Add children for this parent
		if children, exists := childProjectsMap[parent.ProjectName]; exists {
			for _, child := range children {
				result = append(result, child)
			}
		}
	}

	return result
}
