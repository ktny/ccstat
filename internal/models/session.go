package models

import "time"

// SessionEvent represents a single event in a Claude session
type SessionEvent struct {
	Timestamp      time.Time `json:"timestamp"`
	SessionID      string    `json:"sessionId"`
	Directory      string    `json:"cwd"`
	MessageType    string    `json:"role"`
	ContentPreview string    `json:"content_preview"`
	UUID           string    `json:"uuid"`
}

// SessionTimeline represents a timeline of events for a single Claude session
type SessionTimeline struct {
	SessionID     string          `json:"session_id"`
	Directory     string          `json:"directory"`
	ProjectName   string          `json:"project_name"`
	Events        []*SessionEvent `json:"events"`
	StartTime     time.Time       `json:"start_time"`
	EndTime       time.Time       `json:"end_time"`
	ParentProject *string         `json:"parent_project,omitempty"`
}