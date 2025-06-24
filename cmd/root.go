package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/ktny/ccmonitor/internal/app"
)

var (
	days    int
	project string
	threads bool
)

var rootCmd = &cobra.Command{
	Use:   "ccmonitor",
	Short: "Claude Session Timeline - Claudeセッションの時系列可視化ツール",
	Long: `ccmonitorは、Claude Codeのセッション情報を可視化するCLIツールです。
~/.claude/projects/*.jsonlファイルから情報を読み取り、プロジェクト別のアクティビティを時系列で表示します。`,
	Run: func(cmd *cobra.Command, args []string) {
		monitor := app.NewTimelineMonitor(days, project, threads)
		if err := monitor.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
	},
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.PersistentFlags().IntVar(&days, "days", 1, "Number of days to look back (default: 1)")
	rootCmd.PersistentFlags().StringVar(&project, "project", "", "Filter by specific project")
	rootCmd.PersistentFlags().BoolVar(&threads, "threads", false, "Show projects as threads (separate similar repos)")
}