package ui

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/ktny/ccmonitor/internal/models"
)

// CreateTimelineVisualization creates the main timeline visualization
func CreateTimelineVisualization(timelines []*models.SessionTimeline, startTime, endTime time.Time, width int) string {
	if len(timelines) == 0 {
		noSessionsText := NoSessionsStyle.Render("🔍 No Claude sessions found in the specified time range")
		return TimelineStyle.Render(noSessionsText)
	}

	var lines []string

	// Calculate timeline width (total width - project column - events column - duration column - padding)
	timelineWidth := width - 30 - 6 - 8 - 20 // Leave some margin
	if timelineWidth < 20 {
		timelineWidth = 20
	}

	// Add time axis row at the top
	timeAxis := createTimeAxis(startTime, endTime, timelineWidth)
	headerRow := fmt.Sprintf("%-30s %s %6s %8s", "", timeAxis, "", "")
	lines = append(lines, headerRow)

	// Add timeline rows
	for _, timeline := range timelines {
		// Create visual timeline string
		timelineStr := createTimelineString(timeline, startTime, endTime, timelineWidth)

		// Calculate session duration
		duration := timeline.EndTime.Sub(timeline.StartTime)
		durationStr := fmt.Sprintf("%dm", int(duration.Minutes()))

		// Add indent for child threads
		projectDisplay := timeline.ProjectName
		if timeline.ParentProject != nil {
			projectDisplay = "  └─ " + timeline.ProjectName
		}

		row := fmt.Sprintf("%-30s %s %6s %8s", 
			ProjectStyle.Render(projectDisplay),
			timelineStr,
			EventsStyle.Render(fmt.Sprintf("%d", len(timeline.Events))),
			DurationStyle.Render(durationStr),
		)
		lines = append(lines, row)
	}

	content := strings.Join(lines, "\n")
	return TimelineStyle.Render(content)
}

// createTimelineString creates a visual timeline string for a session with density-based display
func createTimelineString(timeline *models.SessionTimeline, startTime, endTime time.Time, width int) string {
	// Initialize timeline with idle periods (very light gray)
	timelineChars := make([]string, width)
	for i := range timelineChars {
		timelineChars[i] = lipgloss.NewStyle().Foreground(ActivityColors[0]).Render("■")
	}

	activityCounts := make([]int, width)
	totalDuration := endTime.Sub(startTime).Seconds()

	// Count events per time position
	for _, event := range timeline.Events {
		eventOffset := event.Timestamp.Sub(startTime).Seconds()
		position := int((eventOffset / totalDuration) * float64(width-1))

		if position >= 0 && position < width {
			activityCounts[position]++
		}
	}

	// Find max activity for normalization
	maxActivity := 0
	for _, count := range activityCounts {
		if count > maxActivity {
			maxActivity = count
		}
	}

	if maxActivity == 0 {
		maxActivity = 1
	}

	// Create density-based markers
	for i, count := range activityCounts {
		if count > 0 {
			// Calculate density level (0-4 scale)
			densityLevel := int(math.Min(4, math.Floor(float64(count)/float64(maxActivity)*4)+1))
			
			// Use square markers with different green intensities
			colorIndex := densityLevel
			if colorIndex >= len(ActivityColors) {
				colorIndex = len(ActivityColors) - 1
			}
			
			timelineChars[i] = lipgloss.NewStyle().Foreground(ActivityColors[colorIndex]).Render("■")
		}
	}

	return strings.Join(timelineChars, "")
}

// createTimeAxis creates a time axis string for reference
func createTimeAxis(startTime, endTime time.Time, width int) string {
	axisChars := make([]rune, width)
	for i := range axisChars {
		axisChars[i] = ' '
	}

	totalDuration := endTime.Sub(startTime).Seconds()
	hours := int(totalDuration / 3600)

	// Place markers on even hours only for cleaner display
	for hourOffset := 0; hourOffset <= hours; hourOffset++ {
		currentTime := startTime.Add(time.Duration(hourOffset) * time.Hour)

		// Only show even hours (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
		if currentTime.Hour()%2 == 0 {
			position := int((float64(hourOffset) * 3600 / totalDuration) * float64(width-1))
			if position >= 0 && position < width-2 { // Leave space for hour string
				// Format hour (just HH format for cleaner look)
				hourStr := fmt.Sprintf("%02d", currentTime.Hour())

				// Place the hour marker (2 characters)
				for i, char := range hourStr {
					if position+i < width {
						axisChars[position+i] = char
					}
				}
			}
		}
	}

	return string(axisChars)
}