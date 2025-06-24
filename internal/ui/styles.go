package ui

import "github.com/charmbracelet/lipgloss"

var (
	// Base styles
	HeaderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("63")).
			Padding(0, 1)

	FooterStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("35")).
			Padding(0, 1)

	TimelineStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("45")).
			Padding(0, 1)

	// Text styles
	TitleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("45")).
			Bold(true)

	ProjectStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("33"))

	EventsStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("45")).
			Align(lipgloss.Right)

	DurationStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("227")).
			Align(lipgloss.Center)

	NoSessionsStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("227")).
			Align(lipgloss.Center)

	SummaryTitleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("45")).
			Bold(true)

	SummaryValueStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("227"))

	// Activity density colors (matching Python version)
	ActivityColors = []lipgloss.Color{
		lipgloss.Color("240"), // None (bright_black)
		lipgloss.Color("22"),  // Low (color(22))
		lipgloss.Color("28"),  // Medium-light (color(28))
		lipgloss.Color("34"),  // Medium-heavy (color(34))
		lipgloss.Color("40"),  // High (color(40))
	}
)