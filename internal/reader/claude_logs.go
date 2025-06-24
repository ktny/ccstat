package reader

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
	"github.com/ktny/ccmonitor/internal/models"
)

// ParseJSONLFile parses a JSONL file and extracts session events
func ParseJSONLFile(filePath string) ([]*models.SessionEvent, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var events []*models.SessionEvent
	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		var data map[string]interface{}
		if err := json.Unmarshal([]byte(line), &data); err != nil {
			continue // Skip malformed lines
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
		timestamp = timestamp.Local()

		// Extract message content
		var messageType, content string
		if message, ok := data["message"].(map[string]interface{}); ok {
			if role, ok := message["role"].(string); ok {
				messageType = role
			}
			if msgContent, ok := message["content"]; ok {
				content = extractContent(msgContent)
			}
		}

		if messageType == "" {
			if typ, ok := data["type"].(string); ok {
				messageType = typ
			} else {
				messageType = "unknown"
			}
		}

		// Create content preview (first 100 chars)
		contentPreview := content
		if len(content) > 100 {
			contentPreview = content[:100] + "..."
		}
		contentPreview = strings.ReplaceAll(contentPreview, "\n", " ")

		event := &models.SessionEvent{
			Timestamp:      timestamp,
			SessionID:      getStringValue(data, "sessionId"),
			Directory:      getStringValue(data, "cwd"),
			MessageType:    messageType,
			ContentPreview: contentPreview,
			UUID:           getStringValue(data, "uuid"),
		}

		events = append(events, event)
	}

	return events, scanner.Err()
}

func extractContent(content interface{}) string {
	switch v := content.(type) {
	case string:
		return v
	case []interface{}:
		var textParts []string
		for _, item := range v {
			if itemMap, ok := item.(map[string]interface{}); ok {
				if itemType, exists := itemMap["type"]; exists && itemType == "text" {
					if text, ok := itemMap["text"].(string); ok {
						textParts = append(textParts, text)
					}
				}
			}
		}
		return strings.Join(textParts, " ")
	default:
		return fmt.Sprintf("%v", content)
	}
}

func getStringValue(data map[string]interface{}, key string) string {
	if value, ok := data[key].(string); ok {
		return value
	}
	return ""
}

// GetAllSessionFiles returns all Claude session JSONL files
func GetAllSessionFiles() ([]string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	projectsDir := filepath.Join(homeDir, ".claude", "projects")
	if _, err := os.Stat(projectsDir); os.IsNotExist(err) {
		return nil, nil
	}

	var jsonlFiles []string

	entries, err := os.ReadDir(projectsDir)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if entry.IsDir() {
			projectPath := filepath.Join(projectsDir, entry.Name())
			files, err := filepath.Glob(filepath.Join(projectPath, "*.jsonl"))
			if err != nil {
				continue
			}
			jsonlFiles = append(jsonlFiles, files...)
		}
	}

	return jsonlFiles, nil
}

// LoadSessionsInTimerange loads all Claude sessions within a time range, grouped by project directory
func LoadSessionsInTimerange(startTime, endTime time.Time, projectFilter string, threads bool) ([]*models.SessionTimeline, error) {
	jsonlFiles, err := GetAllSessionFiles()
	if err != nil {
		return nil, err
	}

	var allEvents []*models.SessionEvent

	// Parse each file and collect events
	for _, filePath := range jsonlFiles {
		events, err := ParseJSONLFile(filePath)
		if err != nil {
			continue // Skip files that can't be parsed
		}
		allEvents = append(allEvents, events...)
	}

	// Filter events by time range
	var filteredEvents []*models.SessionEvent
	for _, event := range allEvents {
		if event.Timestamp.After(startTime) && event.Timestamp.Before(endTime) {
			filteredEvents = append(filteredEvents, event)
		}
	}

	// Sort events by timestamp
	sort.Slice(filteredEvents, func(i, j int) bool {
		return filteredEvents[i].Timestamp.Before(filteredEvents[j].Timestamp)
	})

	// Group events by project directory or repository name
	timelines := groupEventsByProject(filteredEvents, threads)

	// Apply project filter if specified
	if projectFilter != "" {
		var filtered []*models.SessionTimeline
		for _, timeline := range timelines {
			if strings.Contains(strings.ToLower(timeline.ProjectName), strings.ToLower(projectFilter)) {
				filtered = append(filtered, timeline)
			}
		}
		timelines = filtered
	}

	return timelines, nil
}

func groupEventsByProject(events []*models.SessionEvent, threads bool) []*models.SessionTimeline {
	if threads {
		return groupEventsByDirectory(events)
	}
	return groupEventsByRepository(events)
}

func groupEventsByDirectory(events []*models.SessionEvent) []*models.SessionTimeline {
	projectsDict := make(map[string][]*models.SessionEvent)

	// Group events by directory
	for _, event := range events {
		directory := event.Directory
		projectsDict[directory] = append(projectsDict[directory], event)
	}

	// Create timelines with parent-child relationship
	repoToDir := make(map[string][]directoryEvents)
	
	// Get all directories and their repository names
	for directory, events := range projectsDict {
		if len(events) == 0 {
			continue
		}
		
		repoName := git.GetRepositoryName(directory)
		if repoName == "" {
			repoName = filepath.Base(directory)
		}
		
		repoToDir[repoName] = append(repoToDir[repoName], directoryEvents{
			directory: directory,
			events:    events,
		})
	}

	var timelines []*models.SessionTimeline

	// Create timelines with parent information
	for repoName, dirList := range repoToDir {
		// Sort directories: main repo first, then by first event time
		sort.Slice(dirList, func(i, j int) bool {
			// Main repository comes first
			isMainI := git.GetRepositoryName(dirList[i].directory) == repoName
			isMainJ := git.GetRepositoryName(dirList[j].directory) == repoName
			
			if isMainI != isMainJ {
				return isMainI
			}
			
			return dirList[i].events[0].Timestamp.Before(dirList[j].events[0].Timestamp)
		})

		for idx, dirEvent := range dirList {
			// Sort events by timestamp
			sort.Slice(dirEvent.events, func(i, j int) bool {
				return dirEvent.events[i].Timestamp.Before(dirEvent.events[j].Timestamp)
			})

			var parentProject *string
			var displayName string

			if idx == 0 {
				// Main repository
				displayName = repoName
			} else {
				// Child directory
				parentProject = &repoName
				displayName = strings.ReplaceAll(strings.TrimPrefix(dirEvent.directory, dirList[0].directory), "/", "-")
				if displayName == "" {
					displayName = filepath.Base(dirEvent.directory)
				}
			}

			timeline := &models.SessionTimeline{
				SessionID:     fmt.Sprintf("dir_%s", dirEvent.directory),
				Directory:     dirEvent.directory,
				ProjectName:   displayName,
				Events:        dirEvent.events,
				StartTime:     dirEvent.events[0].Timestamp,
				EndTime:       dirEvent.events[len(dirEvent.events)-1].Timestamp,
				ParentProject: parentProject,
			}
			timelines = append(timelines, timeline)
		}
	}

	return sortTimelines(timelines, true)
}

func groupEventsByRepository(events []*models.SessionEvent) []*models.SessionTimeline {
	projectsDict := make(map[string][]*models.SessionEvent)
	repoNames := make(map[string]string)

	// Get all directories and resolve repository names
	allDirectories := make(map[string]bool)
	for _, event := range events {
		allDirectories[event.Directory] = true
	}

	gitRepoDirs := make(map[string]string)
	for directory := range allDirectories {
		if repoName := git.GetRepositoryName(directory); repoName != "" {
			gitRepoDirs[directory] = repoName
		}
	}

	// Resolve repository names for all directories
	for directory := range allDirectories {
		if repoName, exists := gitRepoDirs[directory]; exists {
			repoNames[directory] = repoName
		} else {
			// Check if directory is under any git repository
			var matchedRepo string
			for gitDir, gitRepoName := range gitRepoDirs {
				if strings.HasPrefix(directory, gitDir+"/") {
					matchedRepo = gitRepoName
					break
				}
			}
			
			if matchedRepo != "" {
				repoNames[directory] = matchedRepo
			} else {
				// Use directory name as fallback
				repoNames[directory] = filepath.Base(strings.TrimSuffix(directory, "/"))
				if repoNames[directory] == "" {
					repoNames[directory] = "/"
				}
			}
		}
	}

	// Group events by resolved repository name
	for _, event := range events {
		groupKey := repoNames[event.Directory]
		projectsDict[groupKey] = append(projectsDict[groupKey], event)
	}

	var timelines []*models.SessionTimeline

	// Create timeline for each repository group
	for groupKey, events := range projectsDict {
		if len(events) == 0 {
			continue
		}

		// Sort events by timestamp
		sort.Slice(events, func(i, j int) bool {
			return events[i].Timestamp.Before(events[j].Timestamp)
		})

		timeline := &models.SessionTimeline{
			SessionID:   fmt.Sprintf("repo_%s", groupKey),
			Directory:   events[0].Directory,
			ProjectName: groupKey,
			Events:      events,
			StartTime:   events[0].Timestamp,
			EndTime:     events[len(events)-1].Timestamp,
		}
		timelines = append(timelines, timeline)
	}

	return sortTimelines(timelines, false)
}

type directoryEvents struct {
	directory string
	events    []*models.SessionEvent
}

func sortTimelines(timelines []*models.SessionTimeline, threads bool) []*models.SessionTimeline {
	if threads {
		// For threads mode, group timelines by parent project and sort groups by total events
		groupTimelines := make(map[string][]*models.SessionTimeline)
		standaloneTimelines := []*models.SessionTimeline{}

		for _, timeline := range timelines {
			if timeline.ParentProject != nil {
				groupTimelines[*timeline.ParentProject] = append(groupTimelines[*timeline.ParentProject], timeline)
			} else {
				standaloneTimelines = append(standaloneTimelines, timeline)
			}
		}

		// Calculate total events for each group
		groupTotals := make(map[string]int)
		for _, parentTimeline := range standaloneTimelines {
			total := len(parentTimeline.Events)
			if childTimelines, exists := groupTimelines[parentTimeline.ProjectName]; exists {
				for _, child := range childTimelines {
					total += len(child.Events)
				}
			}
			groupTotals[parentTimeline.ProjectName] = total
		}

		// Sort standalone timelines by their group total events
		sort.Slice(standaloneTimelines, func(i, j int) bool {
			totalI := groupTotals[standaloneTimelines[i].ProjectName]
			totalJ := groupTotals[standaloneTimelines[j].ProjectName]
			return totalI > totalJ
		})

		// Rebuild timelines list with groups together
		var sortedTimelines []*models.SessionTimeline
		for _, parentTimeline := range standaloneTimelines {
			sortedTimelines = append(sortedTimelines, parentTimeline)
			// Add child timelines for this group, sorted by event count
			if childTimelines, exists := groupTimelines[parentTimeline.ProjectName]; exists {
				sort.Slice(childTimelines, func(i, j int) bool {
					return len(childTimelines[i].Events) > len(childTimelines[j].Events)
				})
				sortedTimelines = append(sortedTimelines, childTimelines...)
			}
		}

		return sortedTimelines
	} else {
		// For non-threads mode, sort by event count
		sort.Slice(timelines, func(i, j int) bool {
			return len(timelines[i].Events) > len(timelines[j].Events)
		})
		return timelines
	}
}