package app

import (
	"fmt"
	"time"

	"github.com/ktny/ccmonitor/internal/reader"
	"github.com/ktny/ccmonitor/internal/ui"
)

// TimelineMonitor represents the main application monitor
type TimelineMonitor struct {
	days    int
	project string
	threads bool
}

// NewTimelineMonitor creates a new timeline monitor
func NewTimelineMonitor(days int, project string, threads bool) *TimelineMonitor {
	return &TimelineMonitor{
		days:    days,
		project: project,
		threads: threads,
	}
}

// Run executes the timeline visualization
func (m *TimelineMonitor) Run() error {
	// Calculate time range in local time
	now := time.Now()
	endTime := now
	startTime := endTime.AddDate(0, 0, -m.days)

	// Load sessions in the time range
	loadingMsg := fmt.Sprintf("Loading Claude sessions from the last %d days", m.days)
	if m.project != "" {
		loadingMsg += fmt.Sprintf(" (filtered by project: %s)", m.project)
	}
	loadingMsg += "..."
	
	fmt.Println(loadingMsg)

	timelines, err := reader.LoadSessionsInTimerange(startTime, endTime, m.project, m.threads)
	if err != nil {
		return fmt.Errorf("error loading sessions: %w", err)
	}

	// Create and run UI
	app := ui.NewApp(timelines, startTime, endTime)
	return app.Run()
}