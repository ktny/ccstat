use anyhow::Result;
use chrono::Local;
use std::time::Duration;
use tokio::time;

use crate::{
    db::Database,
    process::{read_claude_tasks, ProcessMonitor},
    ui::UI,
};

pub struct Monitor {
    process_monitor: ProcessMonitor,
    database: Database,
    ui: UI,
}

impl Monitor {
    pub fn new() -> Result<Self> {
        Ok(Self {
            process_monitor: ProcessMonitor::new(),
            database: Database::new()?,
            ui: UI::new()?,
        })
    }

    pub async fn run(&mut self) -> Result<()> {
        let mut interval = time::interval(Duration::from_secs(1));

        loop {
            interval.tick().await;

            // Refresh process information
            self.process_monitor.refresh();

            // Get current processes
            let processes = self.process_monitor.get_claude_processes();

            // Save to database
            for process in &processes {
                if let Err(e) = self.database.insert_process_metrics(process) {
                    tracing::error!("Failed to insert process metrics: {}", e);
                }
            }

            // Get statistics
            let stats = self.database.get_process_stats(None, None)?;

            // Get history for charts (last 5 minutes)
            let cpu_history = self.database.get_cpu_history(5)?;
            let memory_history = self.database.get_memory_history(5)?;

            // Get Claude tasks
            let tasks = read_claude_tasks().unwrap_or_default();

            // Draw UI
            self.ui.draw(
                &processes,
                &stats,
                &cpu_history,
                &memory_history,
                &tasks,
            )?;

            // Handle user input
            if self.ui.handle_input()? {
                break;
            }
        }

        // Clean up old data before exiting
        self.database.cleanup_old_data(7)?;

        Ok(())
    }

    pub async fn show_summary(&mut self) -> Result<()> {
        // Refresh process information
        self.process_monitor.refresh();

        // Get current processes
        let processes = self.process_monitor.get_claude_processes();

        // Get statistics for the last hour
        let stats = self.database.get_process_stats(None, None)?;

        // Show summary UI
        self.ui.show_summary(&stats, &processes)?;

        // Wait for user input to exit
        loop {
            if self.ui.handle_input()? {
                break;
            }
            time::sleep(Duration::from_millis(100)).await;
        }

        Ok(())
    }
}