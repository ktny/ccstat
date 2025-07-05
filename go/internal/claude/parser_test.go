package claude

import (
	"os"
	"testing"
	"time"

	"github.com/ktny/ccstat/go/pkg/models"
)

func TestSessionEventBasic(t *testing.T) {
	event := &models.SessionEvent{
		Timestamp:   time.Now(),
		Directory:   "/test/project",
		MessageType: "assistant",
	}

	if event.Directory != "/test/project" {
		t.Errorf("Expected directory '/test/project', got '%s'", event.Directory)
	}

	if event.MessageType != "assistant" {
		t.Errorf("Expected message type 'assistant', got '%s'", event.MessageType)
	}
}

func TestSessionTimelineBasic(t *testing.T) {
	timeline := &models.SessionTimeline{
		ProjectName:           "test-project",
		Directory:             "/test/project",
		ActiveDurationMinutes: 30,
	}

	if timeline.ProjectName != "test-project" {
		t.Errorf("Expected project 'test-project', got '%s'", timeline.ProjectName)
	}

	if timeline.Directory != "/test/project" {
		t.Errorf("Expected directory '/test/project', got '%s'", timeline.Directory)
	}

	if timeline.ActiveDurationMinutes != 30 {
		t.Errorf("Expected active duration 30, got %d", timeline.ActiveDurationMinutes)
	}

	if len(timeline.Events) != 0 {
		t.Errorf("Expected 0 events, got %d", len(timeline.Events))
	}
}

func TestSessionEventContentPreview(t *testing.T) {
	event := &models.SessionEvent{
		RawMessage: map[string]interface{}{
			"content": "This is a test message",
		},
	}

	event.CreateContentPreview()

	if event.ContentPreview != "This is a test message" {
		t.Errorf("Expected content preview 'This is a test message', got '%s'", event.ContentPreview)
	}
}

// parseFilesSequentially is the original sequential implementation for benchmarking
func parseFilesSequentially(jsonlFiles []string, startTime time.Time, debug bool) []*models.SessionEvent {
	var allEvents []*models.SessionEvent

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

	return allEvents
}

func BenchmarkParseFilesSequential(b *testing.B) {
	// Get real files for benchmarking
	jsonlFiles, err := GetAllSessionFiles()
	if err != nil || len(jsonlFiles) == 0 {
		b.Skip("No JSONL files found for benchmarking")
	}

	// Limit to a reasonable number of files for benchmarking
	if len(jsonlFiles) > 10 {
		jsonlFiles = jsonlFiles[:10]
	}

	startTime := time.Now().AddDate(0, 0, -30) // 30 days ago

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = parseFilesSequentially(jsonlFiles, startTime, false)
	}
}

func BenchmarkParseFilesParallel(b *testing.B) {
	// Get real files for benchmarking
	jsonlFiles, err := GetAllSessionFiles()
	if err != nil || len(jsonlFiles) == 0 {
		b.Skip("No JSONL files found for benchmarking")
	}

	// Limit to a reasonable number of files for benchmarking
	if len(jsonlFiles) > 10 {
		jsonlFiles = jsonlFiles[:10]
	}

	startTime := time.Now().AddDate(0, 0, -30) // 30 days ago

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = parseFilesInParallel(jsonlFiles, startTime, false)
	}
}

func BenchmarkGroupEventsByRepositoryConsolidated(b *testing.B) {
	// Create test events for benchmarking
	var events []*models.SessionEvent

	// Simulate many events from the same directory (realistic scenario)
	for i := 0; i < 1000; i++ {
		event := &models.SessionEvent{
			Timestamp:   time.Now().Add(time.Duration(i) * time.Minute),
			Directory:   "/home/test/project1", // Same directory for all events
			MessageType: "assistant",
		}
		events = append(events, event)
	}

	// Add some events from different directories
	for i := 0; i < 100; i++ {
		event := &models.SessionEvent{
			Timestamp:   time.Now().Add(time.Duration(i) * time.Minute),
			Directory:   "/home/test/project2",
			MessageType: "user",
		}
		events = append(events, event)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Clear cache between runs for consistent benchmarking
		repositoryCache = make(map[string]string)
		_, _ = groupEventsByRepositoryConsolidated(events, false)
	}
}
