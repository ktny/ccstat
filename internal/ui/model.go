package ui

import (
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/ktny/ccmonitor/internal/models"
)

// Model represents the Bubbletea application model
type Model struct {
	timelines []*models.SessionTimeline
	startTime time.Time
	endTime   time.Time
	width     int
	height    int
}

// NewModel creates a new UI model
func NewModel(timelines []*models.SessionTimeline, startTime, endTime time.Time) Model {
	return Model{
		timelines: timelines,
		startTime: startTime,
		endTime:   endTime,
		width:     80,
		height:    24,
	}
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	return nil
}

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		}
	}
	return m, nil
}

// View renders the model
func (m Model) View() string {
	var sections []string

	// Header
	header := m.createHeader()
	sections = append(sections, header)

	// Main timeline visualization
	timeline := CreateTimelineVisualization(m.timelines, m.startTime, m.endTime, m.width)
	sections = append(sections, timeline)

	// Footer with legend
	footer := m.createFooter()
	sections = append(sections, footer)

	// Summary statistics
	if len(m.timelines) > 0 {
		summary := m.createSummary()
		sections = append(sections, summary)
	}

	return strings.Join(sections, "\n\n")
}

// createHeader creates the header panel
func (m Model) createHeader() string {
	duration := m.endTime.Sub(m.startTime)
	hours := int(duration.Hours())

	headerText := fmt.Sprintf("%s - %d hours - %d projects\nTime Range: %s - %s",
		TitleStyle.Render("📊 Claude Project Timeline"),
		hours,
		len(m.timelines),
		m.startTime.Format("01/02 15:04"),
		m.endTime.Format("01/02 15:04"),
	)

	return HeaderStyle.Render(headerText)
}

// createFooter creates the footer with activity legend
func (m Model) createFooter() string {
	legend := []string{
		lipgloss.NewStyle().Foreground(ActivityColors[0]).Render("■") + " None",
		lipgloss.NewStyle().Foreground(ActivityColors[1]).Render("■") + " Low",
		lipgloss.NewStyle().Foreground(ActivityColors[2]).Render("■") + " Med",
		lipgloss.NewStyle().Foreground(ActivityColors[3]).Render("■") + " High",
		lipgloss.NewStyle().Foreground(ActivityColors[4]).Render("■") + " Max",
	}

	footerText := "Activity Density: " + strings.Join(legend, "  ")
	return FooterStyle.Render(footerText)
}

// createSummary creates summary statistics
func (m Model) createSummary() string {
	if len(m.timelines) == 0 {
		return ""
	}

	// Calculate statistics
	totalEvents := 0
	var mostActive *models.SessionTimeline
	maxEvents := 0

	for _, t := range m.timelines {
		events := len(t.Events)
		totalEvents += events
		if events > maxEvents {
			maxEvents = events
			mostActive = t
		}
	}

	// Calculate average duration
	totalDuration := 0.0
	for _, t := range m.timelines {
		duration := t.EndTime.Sub(t.StartTime).Minutes()
		totalDuration += duration
	}
	avgDuration := totalDuration / float64(len(m.timelines))

	summaryLines := []string{
		SummaryTitleStyle.Render("Summary Statistics:"),
		fmt.Sprintf("  • Total Projects: %s", SummaryValueStyle.Render(fmt.Sprintf("%d", len(m.timelines)))),
		fmt.Sprintf("  • Total Events: %s", SummaryValueStyle.Render(fmt.Sprintf("%d", totalEvents))),
		fmt.Sprintf("  • Average Project Duration: %s", SummaryValueStyle.Render(fmt.Sprintf("%.1f minutes", avgDuration))),
	}

	if mostActive != nil {
		summaryLines = append(summaryLines, 
			fmt.Sprintf("  • Most Active Project: %s (%d events)", 
				SummaryValueStyle.Render(mostActive.ProjectName), 
				len(mostActive.Events)))
	}

	return strings.Join(summaryLines, "\n")
}