package ui

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/lipgloss/table"
	"github.com/ktny/ccstat/pkg/models"
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
	case hours <= 2:
		// 1-2 hours: 15-minute intervals with HH:MM format
		return TimeAxisFormat{
			formatStr:   "15:04", // HH:MM format
			interval:    15 * time.Minute,
			displayName: "minutes",
		}
	case hours <= 4:
		// 3-4 hours: 30-minute intervals with HH:MM format
		return TimeAxisFormat{
			formatStr:   "15:04", // HH:MM format
			interval:    30 * time.Minute,
			displayName: "minutes",
		}
	case hours <= 8:
		// 5-8 hours: 1-hour intervals with HH:MM format
		return TimeAxisFormat{
			formatStr:   "15:04", // HH:MM format
			interval:    1 * time.Hour,
			displayName: "hours",
		}
	case hours <= 12:
		// 9-12 hours: 2-hour intervals with HH format
		return TimeAxisFormat{
			formatStr:   "15", // HH format
			interval:    2 * time.Hour,
			displayName: "hours",
		}
	case days <= 2:
		// 13 hours - 2 days: 4-hour intervals with HH format
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

// calculateOptimalTicks calculates optimal tick positions for the time axis with fallback support
func calculateOptimalTicks(startTime, endTime time.Time, width int, format TimeAxisFormat) []time.Time {
	const minTicks = 3
	const maxTicks = 8

	// Try primary format first, then fallback if too many ticks
	formats := getFormatFallbackChain(format)

	for _, currentFormat := range formats {
		ticks := generateTicksForFormat(startTime, endTime, currentFormat)

		// Calculate required width for these ticks
		requiredWidth := calculateRequiredWidth(ticks, currentFormat.formatStr)

		// If ticks fit within available width, use them
		if requiredWidth <= width && len(ticks) >= minTicks && len(ticks) <= maxTicks {
			return ticks
		}
	}

	// If no format fits perfectly, use the least granular format from chain
	lastFormat := formats[len(formats)-1]
	return generateTicksForFormat(startTime, endTime, lastFormat)
}

// getFormatFallbackChain returns a chain of formats with decreasing granularity
func getFormatFallbackChain(primary TimeAxisFormat) []TimeAxisFormat {
	duration := primary.interval

	if duration <= time.Hour {
		// For sub-hourly intervals, create fallback chain
		fallbacks := []TimeAxisFormat{primary}

		if duration == 15*time.Minute {
			fallbacks = append(fallbacks, TimeAxisFormat{"15:04", 30 * time.Minute, "minutes"})
			fallbacks = append(fallbacks, TimeAxisFormat{"15:04", 1 * time.Hour, "hours"})
			fallbacks = append(fallbacks, TimeAxisFormat{"15", 2 * time.Hour, "hours"})
		} else if duration == 30*time.Minute {
			fallbacks = append(fallbacks, TimeAxisFormat{"15:04", 1 * time.Hour, "hours"})
			fallbacks = append(fallbacks, TimeAxisFormat{"15", 2 * time.Hour, "hours"})
		} else if duration == 1*time.Hour {
			fallbacks = append(fallbacks, TimeAxisFormat{"15", 2 * time.Hour, "hours"})
			fallbacks = append(fallbacks, TimeAxisFormat{"15", 4 * time.Hour, "hours"})
		}

		return fallbacks
	}

	// For other intervals, return as-is
	return []TimeAxisFormat{primary}
}

// generateTicksForFormat generates ticks aligned to interval boundaries
func generateTicksForFormat(startTime, endTime time.Time, format TimeAxisFormat) []time.Time {
	var ticks []time.Time

	// Start from a rounded boundary
	current := roundToInterval(startTime, format.interval)

	// If rounded time is before start time, advance to next interval
	if current.Before(startTime) {
		current = current.Add(format.interval)
	}

	// Generate ticks until we exceed end time
	for current.Before(endTime) || current.Equal(endTime) {
		ticks = append(ticks, current)
		current = current.Add(format.interval)
	}

	// Ensure we have at least one tick
	if len(ticks) == 0 {
		ticks = append(ticks, startTime.Add(endTime.Sub(startTime)/2))
	}

	return ticks
}

// calculateRequiredWidth estimates the required width for displaying ticks
func calculateRequiredWidth(ticks []time.Time, formatStr string) int {
	if len(ticks) == 0 {
		return 0
	}

	// Calculate width of one formatted tick
	sampleTick := ticks[0].Format(formatStr)
	tickWidth := len(sampleTick)

	// Add minimum spacing between ticks (2 characters)
	totalWidth := len(ticks)*tickWidth + (len(ticks)-1)*2

	return totalWidth
}

// roundToInterval rounds a time to the nearest interval boundary
func roundToInterval(t time.Time, interval time.Duration) time.Time {
	if interval >= 24*time.Hour {
		// For day or longer intervals, round to start of day
		return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, t.Location())
	} else if interval >= time.Hour {
		// For hour intervals, round to start of hour
		return time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), 0, 0, 0, t.Location())
	} else if interval >= time.Minute {
		// For minute intervals, round to interval boundaries
		minutes := int(interval.Minutes())
		roundedMinute := (t.Minute() / minutes) * minutes
		return time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), roundedMinute, 0, 0, t.Location())
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
		"  - Total Projects: %d\n"+
		"  - Total Events: %d\n"+
		"  - Total Duration: %d minutes\n",
		len(timelines), totalEvents, totalDuration)

	return summary
}
