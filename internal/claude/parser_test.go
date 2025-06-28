package claude

import (
	"testing"
	"time"

	"github.com/ktny/ccmonitor/pkg/models"
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