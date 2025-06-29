package ui

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/lipgloss/table"
	"github.com/ktny/ccmonitor/pkg/models"
	"github.com/muesli/reflow/truncate"
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

// calculateProjectWidth calculates the optimal project column width based on project names
func (ui *TimelineUI) calculateProjectWidth(timelines []*models.SessionTimeline) int {
	const minWidth = 20
	const maxWidth = 30

	if len(timelines) == 0 {
		return minWidth
	}

	maxNameLength := 0
	for _, timeline := range timelines {
		displayName := timeline.ProjectName
		// Consider indentation for child projects
		if timeline.ParentProject != nil {
			displayName = " └─" + timeline.ProjectName
		}

		if len(displayName) > maxNameLength {
			maxNameLength = len(displayName)
		}
	}

	// Add padding for truncation symbol and some margin
	calculatedWidth := maxNameLength + 2

	// Clamp to min/max range
	if calculatedWidth < minWidth {
		return minWidth
	}
	if calculatedWidth > maxWidth {
		return maxWidth
	}

	return calculatedWidth
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
		startTime.Format("2006-01-02 15:04"),
		endTime.Format("2006-01-02 15:04"),
		timeUnit,
		sessionCount)

	return PanelStyle.Render(headerText)
}

// createTimelineTable creates the main timeline visualization table using lipgloss/table
func (ui *TimelineUI) createTimelineTable(timelines []*models.SessionTimeline, startTime, endTime time.Time) string {
	// Calculate project width based on maximum project name length
	projectWidth := ui.calculateProjectWidth(timelines)
	eventsWidth := 8
	durationWidth := 10
	// Account for table borders and external padding (1,2) = 4 horizontal + 4 borders
	timelineWidth := ui.width - projectWidth - eventsWidth - durationWidth - 12
	if timelineWidth < 25 {
		timelineWidth = 25
	}

	// Define style function for dynamic styling based on row and column
	styleFunc := func(row, col int) lipgloss.Style {
		// Header row styling
		if row == table.HeaderRow {
			switch col {
			case 0: // Project column
				return ProjectStyle.Width(projectWidth).Bold(true).Padding(0, 1)
			case 1: // Timeline column
				return lipgloss.NewStyle().Width(timelineWidth).Bold(true).Padding(0, 1)
			case 2: // Events column
				return EventsStyle.Width(eventsWidth).Bold(true).Align(lipgloss.Right).Padding(0, 1)
			case 3: // Duration column
				return DurationStyle.Width(durationWidth).Bold(true).Align(lipgloss.Right).Padding(0, 1)
			}
		}

		// Data row styling (no individual cell padding)
		switch col {
		case 0: // Project column
			return lipgloss.NewStyle().Width(projectWidth).Padding(0, 1)
		case 1: // Timeline column
			return lipgloss.NewStyle().Width(timelineWidth).Padding(0, 1)
		case 2: // Events column
			return lipgloss.NewStyle().Width(eventsWidth).Align(lipgloss.Right).Padding(0, 1)
		case 3: // Duration column
			return lipgloss.NewStyle().Width(durationWidth).Align(lipgloss.Right).Padding(0, 1)
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
	timeAxis := ui.createTimeAxis(startTime, endTime, timelineWidth-2)
	t.Row("", timeAxis, "", "")

	// Add data rows
	for _, timeline := range timelines {
		// Create timeline visualization with actual event density
		timelineStr := ui.createTimelineString(timeline, startTime, endTime, timelineWidth-2)

		// Format duration
		durationStr := fmt.Sprintf("%dm", timeline.ActiveDurationMinutes)

		// Handle project display with indentation for child projects
		projectDisplay := timeline.ProjectName
		if timeline.ParentProject != nil {
			projectDisplay = " └─" + timeline.ProjectName
		}

		projectDisplay = truncate.StringWithTail(projectDisplay, uint(projectWidth-2), "…")

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

// TimeAxisFormat represents different time axis display formats
type TimeAxisFormat struct {
	formatStr   string        // Go time format string
	interval    time.Duration // Interval between ticks
	displayName string        // Human readable name
}

// determineTimeAxisFormat determines the appropriate time axis format based on duration
func determineTimeAxisFormat(duration time.Duration) TimeAxisFormat {
	hours := duration.Hours()
	days := hours / 24

	switch {
	case days <= 2:
		// 1-2 days: hourly display (4-hour intervals for better spacing)
		return TimeAxisFormat{
			formatStr:   "15", // HH format
			interval:    4 * time.Hour,
			displayName: "hours",
		}
	case days <= 30:
		// 3-30 days: daily display with MM/DD format
		return TimeAxisFormat{
			formatStr:   "01/02", // MM/DD format
			interval:    24 * time.Hour,
			displayName: "days",
		}
	case days <= 90:
		// 31-90 days: weekly display
		return TimeAxisFormat{
			formatStr:   "01/02", // MM/DD format for week start
			interval:    7 * 24 * time.Hour,
			displayName: "weeks",
		}
	case days <= 365:
		// 91-365 days: monthly display
		return TimeAxisFormat{
			formatStr:   "Jan",               // Month abbreviation
			interval:    30 * 24 * time.Hour, // Approximate month
			displayName: "months",
		}
	default:
		// 365+ days: yearly display
		return TimeAxisFormat{
			formatStr:   "2006", // Year format
			interval:    365 * 24 * time.Hour,
			displayName: "years",
		}
	}
}

// calculateOptimalTicks calculates optimal tick positions for the time axis
func calculateOptimalTicks(startTime, endTime time.Time, width int, format TimeAxisFormat) []time.Time {
	const minTicks = 3
	const maxTicks = 6

	duration := endTime.Sub(startTime)
	days := duration.Hours() / 24

	// Period-specific tick count optimization
	var targetTicks int
	switch {
	case days <= 1:
		targetTicks = 6 // 1 day: 6 ticks
	case days <= 2:
		targetTicks = 6 // 2 days: 6 ticks
	case days <= 3:
		targetTicks = 3 // 3 days: 3 ticks
	case days <= 4:
		targetTicks = 4 // 4 days: 4 ticks
	case days <= 5:
		targetTicks = 5 // 5 days: 5 ticks
	case days <= 7:
		targetTicks = 6 // 6-7 days: 6 ticks
	default:
		// For longer periods, use dynamic calculation within min/max bounds
		defaultTickCount := int(duration / format.interval)
		if defaultTickCount < minTicks {
			targetTicks = minTicks
		} else if defaultTickCount > maxTicks {
			targetTicks = maxTicks
		} else {
			targetTicks = defaultTickCount
		}
	}

	// Clamp target ticks to bounds
	if targetTicks < minTicks {
		targetTicks = minTicks
	}
	if targetTicks > maxTicks {
		targetTicks = maxTicks
	}

	// Generate evenly spaced ticks
	var ticks []time.Time
	if targetTicks == 1 {
		// Single tick at middle
		ticks = append(ticks, startTime.Add(duration/2))
	} else {
		// Multiple ticks evenly spaced
		tickInterval := duration / time.Duration(targetTicks-1)
		for i := 0; i < targetTicks; i++ {
			tick := startTime.Add(time.Duration(i) * tickInterval)
			if i == targetTicks-1 {
				tick = endTime // Ensure last tick is exactly at end
			}
			ticks = append(ticks, tick)
		}
	}

	return ticks
}

// roundToInterval rounds a time to the nearest interval
func roundToInterval(t time.Time, interval time.Duration) time.Time {
	if interval >= 24*time.Hour {
		// For day or longer intervals, round to start of day
		return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, t.Location())
	} else if interval >= time.Hour {
		// For hour intervals, round to start of hour
		return time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), 0, 0, 0, t.Location())
	}
	// For smaller intervals, return as-is
	return t
}

// createTimeAxis creates a time axis string with appropriate time markers
func (ui *TimelineUI) createTimeAxis(startTime, endTime time.Time, width int) string {
	duration := endTime.Sub(startTime)

	// Determine the appropriate time axis format
	format := determineTimeAxisFormat(duration)

	// Calculate optimal tick positions
	ticks := calculateOptimalTicks(startTime, endTime, width, format)

	// Initialize axis with spaces
	axisChars := make([]string, width)
	for i := range axisChars {
		axisChars[i] = " "
	}

	// Place tick markers
	for _, tick := range ticks {
		// Calculate position for this tick
		tickOffset := tick.Sub(startTime)
		position := int((float64(tickOffset) / float64(duration)) * float64(width))

		// Clamp position to valid range
		if position >= width {
			position = width - 1
		}
		if position < 0 {
			position = 0
		}

		// Format the tick label
		tickLabel := tick.Format(format.formatStr)

		// Place the label, centered on the position if possible
		startPos := position - len(tickLabel)/2
		if startPos < 0 {
			startPos = 0
		}
		if startPos+len(tickLabel) > width {
			startPos = width - len(tickLabel)
		}

		// Only place if it doesn't overflow
		if startPos >= 0 && startPos+len(tickLabel) <= width {
			for i, c := range tickLabel {
				if startPos+i < width {
					axisChars[startPos+i] = string(c)
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
