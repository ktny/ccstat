package ui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/ktny/ccmonitor/internal/models"
)

// App represents the Bubbletea application
type App struct {
	model Model
}

// NewApp creates a new UI application
func NewApp(timelines []*models.SessionTimeline, startTime, endTime time.Time) *App {
	model := NewModel(timelines, startTime, endTime)
	return &App{
		model: model,
	}
}

// Run starts the Bubbletea application
func (a *App) Run() error {
	p := tea.NewProgram(a.model, tea.WithAltScreen())
	_, err := p.Run()
	return err
}