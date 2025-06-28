package models

import (
	"time"
)

// SessionEvent represents a single event in a Claude session
type SessionEvent struct {
	Timestamp      time.Time `json:"timestamp"`
	SessionID      string    `json:"sessionId"`
	Directory      string    `json:"cwd"`          // Keep as directory since it's the actual cwd from logs
	MessageType    string    `json:"role"`         // "user", "assistant", etc.
	ContentPreview string    `json:"-"`            // Not from JSON, computed
	UUID           string    `json:"uuid"`
	RawMessage     map[string]interface{} `json:"message"` // Raw message for content extraction
}

// SessionTimeline represents a timeline of events for a single Claude session
type SessionTimeline struct {
	SessionID             string          `json:"session_id"`
	Directory             string          `json:"directory"`       // Full path from logs
	ProjectName           string          `json:"project_name"`    // short name for display
	Events                []*SessionEvent `json:"events"`
	StartTime             time.Time       `json:"start_time"`
	EndTime               time.Time       `json:"end_time"`
	ActiveDurationMinutes int             `json:"active_duration_minutes"` // Active work time in minutes
	ParentProject         *string         `json:"parent_project,omitempty"` // Parent project name for thread display
}

// CreateContentPreview creates a content preview from the raw message content
func (e *SessionEvent) CreateContentPreview() {
	if e.RawMessage == nil {
		e.ContentPreview = ""
		return
	}

	content, ok := e.RawMessage["content"]
	if !ok {
		e.ContentPreview = ""
		return
	}

	var contentStr string
	
	// Handle different content types
	switch c := content.(type) {
	case string:
		contentStr = c
	case []interface{}:
		// Content is a list, extract text from first text item
		for _, item := range c {
			if itemMap, ok := item.(map[string]interface{}); ok {
				if itemType, ok := itemMap["type"].(string); ok && itemType == "text" {
					if text, ok := itemMap["text"].(string); ok {
						contentStr += text + " "
					}
				}
			}
		}
	default:
		contentStr = ""
	}

	// Create content preview (first 100 chars)
	if len(contentStr) > 100 {
		e.ContentPreview = contentStr[:100] + "..."
	} else {
		e.ContentPreview = contentStr
	}

	// Replace newlines with spaces
	for i, r := range e.ContentPreview {
		if r == '\n' {
			e.ContentPreview = e.ContentPreview[:i] + " " + e.ContentPreview[i+1:]
		}
	}
}