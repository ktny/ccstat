package main

import (
	"fmt"
	"os"
	"runtime/debug"
	"time"

	"github.com/ktny/ccstat/internal/claude"
	"github.com/ktny/ccstat/internal/ui"
	"github.com/ktny/ccstat/internal/updater"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

var (
	// Build-time variables (can be set via -ldflags)
	versionString = "dev"
	commitHash    = "unknown"
	buildDate     = "unknown"

	// CLI flags
	days            int
	hours           int
	project         string
	worktree        bool
	debugFlag       bool
	versionFlag     bool
	updateFlag      bool
	checkUpdateFlag bool
)

func getVersionInfo() string {
	v := versionString

	// Try to get version from build info if not set via ldflags
	if v == "dev" {
		if info, ok := debug.ReadBuildInfo(); ok {
			if info.Main.Version != "(devel)" && info.Main.Version != "" {
				v = info.Main.Version
			}
		}
	}

	if commitHash != "unknown" || buildDate != "unknown" {
		return fmt.Sprintf("ccstat %s (commit: %s, built: %s)", v, commitHash, buildDate)
	}
	return fmt.Sprintf("ccstat %s", v)
}

var rootCmd = &cobra.Command{
	Use:   "ccstat",
	Short: "Claude Session Statistics - CLI tool for visualizing Claude session activity patterns",
	Run: func(cmd *cobra.Command, args []string) {
		if versionFlag {
			fmt.Println(getVersionInfo())
			return
		}
		if checkUpdateFlag {
			if err := checkForUpdate(); err != nil {
				fmt.Fprintf(os.Stderr, "❌ Error checking for updates: %v\n", err)
				os.Exit(1)
			}
			return
		}
		if updateFlag {
			if err := performUpdate(); err != nil {
				fmt.Fprintf(os.Stderr, "❌ Error performing update: %v\n", err)
				os.Exit(1)
			}
			return
		}
		if err := runMonitor(); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Error: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	// Disable flag sorting to maintain custom order
	rootCmd.Flags().SortFlags = false

	// Define flags in desired display order: --days, --hours, --project, --worktree, --help, --version, --debug, --update, --check-update
	rootCmd.Flags().IntVarP(&days, "days", "d", 1, "Number of days to look back (default: 1)")
	rootCmd.Flags().IntVarP(&hours, "hours", "H", 0, "Number of hours to look back (1-24, overrides --days)")
	rootCmd.Flags().StringVarP(&project, "project", "p", "", "Filter by specific project")
	rootCmd.Flags().BoolVarP(&worktree, "worktree", "w", false, "Show projects as worktree (separate similar repos)")
	rootCmd.Flags().BoolVarP(&versionFlag, "version", "v", false, "Show version information")
	rootCmd.Flags().BoolVar(&debugFlag, "debug", false, "Enable debug output for troubleshooting")
	rootCmd.Flags().BoolVar(&updateFlag, "update", false, "Update ccstat to the latest version")
	rootCmd.Flags().BoolVar(&checkUpdateFlag, "check-update", false, "Check if an update is available")
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
	timelines, err := claude.LoadSessionsInTimeRange(startTime, endTime, project, worktree, debugFlag)
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

// checkForUpdate checks for available updates
func checkForUpdate() error {
	fmt.Println("Checking for updates...")

	// Use a default version for development builds
	currentVer := versionString
	if currentVer == "dev" {
		currentVer = "0.0.0-dev"
	}

	u, err := updater.NewUpdater("ktny", "ccstat", currentVer)
	if err != nil {
		return fmt.Errorf("failed to create updater: %w", err)
	}

	updateInfo, err := u.CheckForUpdate()
	if err != nil {
		return fmt.Errorf("failed to check for updates: %w", err)
	}

	if updateInfo.Available {
		fmt.Printf("🎉 Update available!\n")
		fmt.Printf("   Current version: %s\n", updateInfo.CurrentVersion.String())
		fmt.Printf("   Latest version:  %s\n", updateInfo.LatestVersion.String())
		fmt.Printf("   Run 'ccstat --update' to update.\n")
	} else {
		fmt.Printf("✅ You are already using the latest version (%s)\n", updateInfo.CurrentVersion.String())
	}

	return nil
}

// performUpdate performs the update process
func performUpdate() error {
	fmt.Println("Starting update process...")

	// Use a default version for development builds
	currentVer := versionString
	if currentVer == "dev" {
		currentVer = "0.0.0-dev"
	}

	u, err := updater.NewUpdater("ktny", "ccstat", currentVer)
	if err != nil {
		return fmt.Errorf("failed to create updater: %w", err)
	}

	return u.PerformUpdate()
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
