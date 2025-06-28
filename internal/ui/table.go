package ui

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/lipgloss/table"
	"github.com/ktny/ccmonitor/pkg/models"
)

// Colors matching Rich color scheme
var (
	// Header colors
	HeaderStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("12")) // Cyan

	// Column colors
	ProjectStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("12")) // Blue
	EventsStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("14")) // Cyan
	DurationStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("11")) // Yellow

	// Panel styles
	PanelStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("12")).
			Padding(0, 1)

	// Activity density colors (matching Rich color scheme)
	ActivityColors = []lipgloss.Color{
		lipgloss.Color("8"),  // bright_black - no activity
		lipgloss.Color("22"), // color(22) - low activity
		lipgloss.Color("28"), // color(28) - medium-low activity
		lipgloss.Color("34"), // color(34) - medium-high activity
		lipgloss.Color("40"), // color(40) - high activity
	}
)

// TimelineUI handles the UI display logic
type TimelineUI struct {
	width int
}

// NewTimelineUI creates a new timeline UI with the given terminal width
func NewTimelineUI(width int) *TimelineUI {
	return &TimelineUI{
		width: width,
	}
}

// DisplayTimeline displays the complete timeline with header, table, and summary
func (ui *TimelineUI) DisplayTimeline(timelines []*models.SessionTimeline, startTime, endTime time.Time, timeUnit string) string {
	var output strings.Builder

	// Create header
	header := ui.createHeader(startTime, endTime, len(timelines), timeUnit)
	output.WriteString(header)
	output.WriteString("\n")

	if len(timelines) == 0 {
		noSessionsText := "🔍 No Claude sessions found in the specified time range"
		noSessionsPanel := PanelStyle.
			BorderForeground(lipgloss.Color("11")).
			Render(noSessionsText)
		output.WriteString(noSessionsPanel)
		return output.String()
	}

	// Create main timeline table
	table := ui.createTimelineTable(timelines, startTime, endTime)
	output.WriteString(table)

	// Create summary
	summary := ui.createSummary(timelines)
	output.WriteString(summary)

	return output.String()
}

// createHeader creates the header panel with title and time range info
func (ui *TimelineUI) createHeader(startTime, endTime time.Time, sessionCount int, timeUnit string) string {
	headerText := fmt.Sprintf("📊 Claude Project Timeline | %s - %s (%s) | %d projects",
		startTime.Format("01/02/2006 15:04"),
		endTime.Format("01/02/2006 15:04"),
		timeUnit,
		sessionCount)

	return PanelStyle.Render(headerText)
}

// createTimelineTable creates the main timeline visualization table using lipgloss/table
func (ui *TimelineUI) createTimelineTable(timelines []*models.SessionTimeline, startTime, endTime time.Time) string {
	// Calculate column widths considering padding (padding is included in width)
	projectWidth := 20
	eventsWidth := 8
	durationWidth := 10
	timelineWidth := ui.width - projectWidth - eventsWidth - durationWidth - 10
	if timelineWidth < 20 {
		timelineWidth = 20
	}

	// Define style function for dynamic styling based on row and column
	styleFunc := func(row, col int) lipgloss.Style {
		// Header row styling with padding
		if row == table.HeaderRow {
			switch col {
			case 0: // Project column
				return ProjectStyle.Width(projectWidth).Bold(true)
			case 1: // Timeline column
				return lipgloss.NewStyle().Width(timelineWidth).Bold(true)
			case 2: // Events column
				return EventsStyle.Width(eventsWidth).Bold(true).Align(lipgloss.Right)
			case 3: // Duration column
				return DurationStyle.Width(durationWidth).Bold(true).Align(lipgloss.Right)
			}
		}

		// Data row styling with padding
		switch col {
		case 0: // Project column
			return lipgloss.NewStyle().Width(projectWidth)
		case 1: // Timeline column
			return lipgloss.NewStyle().Width(timelineWidth)
		case 2: // Events column
			return lipgloss.NewStyle().Width(eventsWidth).Align(lipgloss.Right)
		case 3: // Duration column
			return lipgloss.NewStyle().Width(durationWidth).Align(lipgloss.Right)
		}
		return lipgloss.NewStyle()
	}

	// Create the table with styling (no inner borders)
	t := table.New().
		Border(lipgloss.RoundedBorder()).
		BorderStyle(lipgloss.NewStyle().Foreground(lipgloss.Color("14"))).
		BorderColumn(false). // Disable column borders
		BorderRow(false).    // Disable row borders (except header)
		BorderHeader(false). // Keep header separator
		StyleFunc(styleFunc).
		Headers("Project", ui.createTimelineHeader(timelineWidth), "Events", "Duration")

	// Add time axis row
	timeAxis := ui.createTimeAxis(startTime, endTime, timelineWidth)
	t.Row("", timeAxis, "", "")

	// Add data rows
	for _, timeline := range timelines {
		// Create timeline visualization with actual event density
		timelineStr := ui.createTimelineString(timeline, startTime, endTime, timelineWidth)

		// Format duration
		durationStr := fmt.Sprintf("%dm", timeline.ActiveDurationMinutes)

		// Handle project display with indentation for child projects
		projectDisplay := timeline.ProjectName
		if timeline.ParentProject != nil {
			projectDisplay = " └─" + timeline.ProjectName
		}

		// Truncate project name if it's too long
		projectDisplay = truncateString(projectDisplay, projectWidth)

		t.Row(projectDisplay, timelineStr, fmt.Sprintf("%d", len(timeline.Events)), durationStr)
	}

	return t.String()
}

// createTimelineHeader creates the timeline column header with activity legend
func (ui *TimelineUI) createTimelineHeader(timelineWidth int) string {
	// Create timeline header with activity density legend (without styles first)
	baseTimelineHeader := "Timeline "
	activityLegend := ""
	for i := range ActivityColors {
		if i == 0 {
			continue // Skip the first (no activity) color for the legend
		}
		activityLegend += "■"
	}

	// Calculate total visible length
	totalHeaderLength := len(baseTimelineHeader + activityLegend)

	// Create styled timeline header
	timelineHeader := baseTimelineHeader
	for i, color := range ActivityColors {
		if i == 0 {
			continue
		}
		timelineHeader += lipgloss.NewStyle().Foreground(color).Render("■")
	}

	// Add padding to match timelineWidth if needed
	if totalHeaderLength < timelineWidth {
		paddingLength := timelineWidth - totalHeaderLength
		timelineHeader += strings.Repeat(" ", paddingLength)
	}

	return timelineHeader
}

// createTimelineString creates a visual timeline string with density-based display
func (ui *TimelineUI) createTimelineString(timeline *models.SessionTimeline, startTime, endTime time.Time, width int) string {
	// Initialize timeline with idle markers
	timelineChars := make([]string, width)
	for i := range timelineChars {
		timelineChars[i] = lipgloss.NewStyle().Foreground(ActivityColors[0]).Render("■")
	}

	activityCounts := make([]int, width)
	totalDuration := endTime.Sub(startTime)

	// Count events per time position
	for _, event := range timeline.Events {
		eventOffset := event.Timestamp.Sub(startTime)
		position := int((float64(eventOffset) / float64(totalDuration)) * float64(width))

		// Clamp position to valid range
		if position >= width {
			position = width - 1
		}
		if position < 0 {
			position = 0
		}

		activityCounts[position]++
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

			// Use appropriate color for density level
			colorIndex := densityLevel
			if colorIndex >= len(ActivityColors) {
				colorIndex = len(ActivityColors) - 1
			}

			timelineChars[i] = lipgloss.NewStyle().Foreground(ActivityColors[colorIndex]).Render("■")
		}
	}

	return strings.Join(timelineChars, "")
}

// createTimeAxis creates a time axis string with appropriate time markers
func (ui *TimelineUI) createTimeAxis(startTime, endTime time.Time, width int) string {
	// Simplified time axis - showing just start/middle/end for now
	// This would need the full time unit logic from the Python version
	duration := endTime.Sub(startTime)

	axisChars := make([]string, width)
	for i := range axisChars {
		axisChars[i] = " "
	}

	// Add time markers at key positions
	if width > 10 {
		// Start time marker
		startStr := startTime.Format("15")
		if len(startStr) <= width {
			for i, c := range startStr {
				if i < width {
					axisChars[i] = string(c)
				}
			}
		}

		// End time marker
		endStr := endTime.Format("15")
		if len(endStr) <= width {
			startPos := width - len(endStr)
			for i, c := range endStr {
				if startPos+i < width && startPos+i >= 0 {
					axisChars[startPos+i] = string(c)
				}
			}
		}

		// Middle marker for longer durations
		if duration.Hours() > 2 && width > 20 {
			middleTime := startTime.Add(duration / 2)
			middleStr := middleTime.Format("15")
			middlePos := width/2 - len(middleStr)/2
			for i, c := range middleStr {
				if middlePos+i < width && middlePos+i >= 0 {
					axisChars[middlePos+i] = string(c)
				}
			}
		}
	}

	return strings.Join(axisChars, "")
}

// createSummary creates the summary statistics text
func (ui *TimelineUI) createSummary(timelines []*models.SessionTimeline) string {
	if len(timelines) == 0 {
		return ""
	}

	totalEvents := 0
	totalDuration := 0

	for _, timeline := range timelines {
		totalEvents += len(timeline.Events)
		totalDuration += timeline.ActiveDurationMinutes
	}

	summary := fmt.Sprintf("\nSummary Statistics:\n"+
		"  • Total Projects: %d\n"+
		"  • Total Events: %d\n"+
		"  • Total Duration: %d minutes",
		len(timelines), totalEvents, totalDuration)

	return HeaderStyle.Render(summary)
}

// truncateString truncates a string to maxLen display width, properly handling ANSI codes
func truncateString(s string, maxLen int) string {
	// Use lipgloss.Width to get the display width (ignoring ANSI codes)
	currentWidth := lipgloss.Width(s)

	if currentWidth <= maxLen {
		return s
	}

	if maxLen <= 3 {
		// If maxLen is very small, just truncate by runes
		runes := []rune(s)
		if len(runes) <= maxLen {
			return s
		}
		return string(runes[:maxLen])
	}

	// Truncate and add ellipsis
	ellipsis := "..."
	targetWidth := maxLen - len(ellipsis)

	// Truncate by runes until we reach the target display width
	runes := []rune(s)
	for i := len(runes); i > 0; i-- {
		candidate := string(runes[:i])
		if lipgloss.Width(candidate) <= targetWidth {
			return candidate + ellipsis
		}
	}

	return ellipsis
}
