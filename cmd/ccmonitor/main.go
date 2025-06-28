package main

import (
	"fmt"
	"os"
	"time"

	"github.com/ktny/ccmonitor/internal/claude"
	"github.com/ktny/ccmonitor/internal/ui"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

var (
	days     int
	hours    int
	project  string
	worktree bool
	debug    bool
)

var rootCmd = &cobra.Command{
	Use:   "ccmonitor",
	Short: "Claude Session Timeline - CLI tool for visualizing Claude session activity patterns",
	Run: func(cmd *cobra.Command, args []string) {
		if err := runMonitor(); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Error: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.Flags().IntVarP(&days, "days", "d", 1, "Number of days to look back (default: 1)")
	rootCmd.Flags().IntVarP(&hours, "hours", "H", 0, "Number of hours to look back (1-24, overrides --days)")
	rootCmd.Flags().StringVarP(&project, "project", "p", "", "Filter by specific project")
	rootCmd.Flags().BoolVarP(&worktree, "worktree", "w", false, "Show projects as worktree (separate similar repos)")
}

func runMonitor() error {
	// Calculate time range
	now := time.Now()
	endTime := now

	var startTime time.Time
	var timeUnit string

	if hours > 0 {
		startTime = endTime.Add(-time.Duration(hours) * time.Hour)
		timeUnit = fmt.Sprintf("%d hours", hours)
	} else {
		startTime = endTime.Add(-time.Duration(days) * 24 * time.Hour)
		timeUnit = fmt.Sprintf("%d days", days)
	}

	// Display loading message
	loadingMsg := fmt.Sprintf("Loading Claude sessions from the last %s", timeUnit)
	if project != "" {
		loadingMsg += fmt.Sprintf(" (filtered by project: %s)", project)
	}
	loadingMsg += "..."
	fmt.Println(loadingMsg)

	// Load sessions
	timelines, err := claude.LoadSessionsInTimeRange(startTime, endTime, project, worktree, debug)
	if err != nil {
		return fmt.Errorf("failed to load sessions: %w", err)
	}

	// Get terminal width
	width, _, err := term.GetSize(int(os.Stdout.Fd()))
	if err != nil {
		width = 80 // Default width if detection fails
	}

	// Create UI and display timeline
	timelineUI := ui.NewTimelineUI(width)
	output := timelineUI.DisplayTimeline(timelines, startTime, endTime, timeUnit)

	// Display result
	fmt.Print(output)

	return nil
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
