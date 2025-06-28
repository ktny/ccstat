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

	"github.com/ktny/ccmonitor/pkg/models"
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

// groupEventsByProject groups events by project directory
func groupEventsByProject(events []*models.SessionEvent, threads bool) ([]*models.SessionTimeline, error) {
	// This is a simplified version - we'll implement the full grouping logic later
	// For now, just group by directory
	projectMap := make(map[string][]*models.SessionEvent)

	for _, event := range events {
		directory := event.Directory
		if directory == "" {
			directory = "unknown"
		}
		projectMap[directory] = append(projectMap[directory], event)
	}

	var timelines []*models.SessionTimeline

	for directory, projectEvents := range projectMap {
		if len(projectEvents) == 0 {
			continue
		}

		// Sort events by timestamp
		sort.Slice(projectEvents, func(i, j int) bool {
			return projectEvents[i].Timestamp.Before(projectEvents[j].Timestamp)
		})

		// Use directory name as project name (simplified)
		projectName := filepath.Base(directory)
		if projectName == "" || projectName == "." {
			projectName = "unknown"
		}

		timeline := &models.SessionTimeline{
			SessionID:             fmt.Sprintf("dir_%s", directory),
			Directory:             directory,
			ProjectName:           projectName,
			Events:                projectEvents,
			StartTime:             projectEvents[0].Timestamp,
			EndTime:               projectEvents[len(projectEvents)-1].Timestamp,
			ActiveDurationMinutes: CalculateActiveDuration(projectEvents),
		}

		timelines = append(timelines, timeline)
	}

	// Sort by event count (descending)
	sort.Slice(timelines, func(i, j int) bool {
		return len(timelines[i].Events) > len(timelines[j].Events)
	})

	return timelines, nil
}
