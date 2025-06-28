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

	"github.com/ktny/ccmonitor/internal/git"
	"github.com/ktny/ccmonitor/pkg/models"
)

// ParseJSONLFile parses a JSONL file and extracts session events
func ParseJSONLFile(filePath string) ([]*models.SessionEvent, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = file.Close() // Ignore error in defer
	}()

	var events []*models.SessionEvent
	scanner := bufio.NewScanner(file)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(line), &data); err != nil {
			// Skip malformed lines
			continue
		}

		// Extract timestamp
		timestampStr, ok := data["timestamp"].(string)
		if !ok {
			continue
		}

		// Parse ISO format timestamp and convert to local time
		timestamp, err := time.Parse(time.RFC3339, timestampStr)
		if err != nil {
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

	return events, nil
}

// GetAllSessionFiles returns all Claude session JSONL files
func GetAllSessionFiles() ([]string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	projectsDir := filepath.Join(homeDir, ".claude", "projects")

	if _, err := os.Stat(projectsDir); os.IsNotExist(err) {
		return []string{}, nil
	}

	var jsonlFiles []string

	err = filepath.Walk(projectsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(path, ".jsonl") {
			jsonlFiles = append(jsonlFiles, path)
		}

		return nil
	})

	return jsonlFiles, err
}

// LoadSessionsInTimeRange loads all Claude sessions within a time range, grouped by project directory
func LoadSessionsInTimeRange(startTime, endTime time.Time, projectFilter string, threads bool) ([]*models.SessionTimeline, error) {
	var allEvents []*models.SessionEvent

	// Get all JSONL files
	jsonlFiles, err := GetAllSessionFiles()
	if err != nil {
		return nil, err
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

		events, err := ParseJSONLFile(filePath)
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

	// Sort events by timestamp
	sort.Slice(filteredEvents, func(i, j int) bool {
		return filteredEvents[i].Timestamp.Before(filteredEvents[j].Timestamp)
	})

	// Group events by project directory
	timelines, err := groupEventsByProject(filteredEvents, threads)
	if err != nil {
		return nil, err
	}

	// Apply project filter if specified
	if projectFilter != "" {
		var filteredTimelines []*models.SessionTimeline
		for _, timeline := range timelines {
			if strings.Contains(strings.ToLower(timeline.ProjectName), strings.ToLower(projectFilter)) {
				filteredTimelines = append(filteredTimelines, timeline)
			}
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
func groupEventsByProject(events []*models.SessionEvent, threads bool) ([]*models.SessionTimeline, error) {
	if threads {
		// threads=true (worktree mode): group by git repository with child project support
		return groupEventsByRepositoryWithChildren(events)
	}
	// threads=false (default): consolidate by git repository
	return groupEventsByRepositoryConsolidated(events)
}

// groupEventsByRepositoryConsolidated consolidates events by git repository (default mode)
func groupEventsByRepositoryConsolidated(events []*models.SessionEvent) ([]*models.SessionTimeline, error) {
	// Group events by git repository, consolidating all directories of the same repo
	repoEventMap := make(map[string][]*models.SessionEvent)

	for _, event := range events {
		directory := event.Directory
		if directory == "" {
			directory = "unknown"
		}

		// Get repository name for this directory
		repoName := git.GetRepositoryName(directory)
		if repoName == "" {
			repoName = filepath.Base(directory) // fallback to directory name
		}

		repoEventMap[repoName] = append(repoEventMap[repoName], event)
	}

	var timelines []*models.SessionTimeline

	for repoName, repoEvents := range repoEventMap {
		if len(repoEvents) == 0 {
			continue
		}

		// Sort all events by timestamp
		sort.Slice(repoEvents, func(i, j int) bool {
			return repoEvents[i].Timestamp.Before(repoEvents[j].Timestamp)
		})

		// Create consolidated timeline for this repository
		timeline := &models.SessionTimeline{
			SessionID:             fmt.Sprintf("repo_%s", repoName),
			Directory:             "", // No specific directory for consolidated repo
			ProjectName:           repoName,
			Events:                repoEvents,
			StartTime:             repoEvents[0].Timestamp,
			EndTime:               repoEvents[len(repoEvents)-1].Timestamp,
			ActiveDurationMinutes: CalculateActiveDuration(repoEvents),
		}

		timelines = append(timelines, timeline)
	}

	// Sort by event count (descending)
	sort.Slice(timelines, func(i, j int) bool {
		return len(timelines[i].Events) > len(timelines[j].Events)
	})

	return timelines, nil
}

// groupEventsByRepositoryWithChildren groups events by git repository with child project support (worktree mode)
func groupEventsByRepositoryWithChildren(events []*models.SessionEvent) ([]*models.SessionTimeline, error) {
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
		if repoName == "" {
			repoName = filepath.Base(directory) // fallback to directory name
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
			// First, create parent project with all events
			var allEvents []*models.SessionEvent
			for _, directoryEvents := range repoDirs {
				allEvents = append(allEvents, directoryEvents...)
			}

			// Sort all events by timestamp
			sort.Slice(allEvents, func(i, j int) bool {
				return allEvents[i].Timestamp.Before(allEvents[j].Timestamp)
			})

			parentTimeline := &models.SessionTimeline{
				SessionID:             fmt.Sprintf("repo_%s", repoName),
				Directory:             "", // Parent doesn't have specific directory
				ProjectName:           repoName,
				Events:                allEvents,
				StartTime:             allEvents[0].Timestamp,
				EndTime:               allEvents[len(allEvents)-1].Timestamp,
				ActiveDurationMinutes: CalculateActiveDuration(allEvents),
			}

			timelines = append(timelines, parentTimeline)

			// Then, create child projects for each directory
			for directory, projectEvents := range repoDirs {
				if len(projectEvents) == 0 {
					continue
				}

				// Sort events by timestamp
				sort.Slice(projectEvents, func(i, j int) bool {
					return projectEvents[i].Timestamp.Before(projectEvents[j].Timestamp)
				})

				dirName := filepath.Base(directory)
				if dirName == "" || dirName == "." {
					dirName = "unknown"
				}

				childTimeline := &models.SessionTimeline{
					SessionID:             fmt.Sprintf("dir_%s", directory),
					Directory:             directory,
					ProjectName:           dirName,
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

	// Sort by event count (descending), but keep parent-child order
	sort.Slice(timelines, func(i, j int) bool {
		// If one is parent and the other is its child, parent comes first
		if timelines[i].ParentProject == nil && timelines[j].ParentProject != nil &&
			*timelines[j].ParentProject == timelines[i].ProjectName {
			return true
		}
		if timelines[j].ParentProject == nil && timelines[i].ParentProject != nil &&
			*timelines[i].ParentProject == timelines[j].ProjectName {
			return false
		}

		// Both are parents or both are children, sort by event count
		return len(timelines[i].Events) > len(timelines[j].Events)
	})

	return timelines, nil
}
