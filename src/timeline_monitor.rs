use crate::{claude_logs::load_sessions_in_timerange, timeline_ui::TimelineUI};
use anyhow::Result;
use chrono::{DateTime, Duration, Local};
use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    Terminal,
};
use std::io;

pub struct TimelineMonitor {
    pub days: i64,
    pub project: Option<String>,
    pub threads: bool,
}

impl TimelineMonitor {
    pub fn new(days: i64, project: Option<String>, threads: bool) -> Self {
        Self {
            days,
            project,
            threads,
        }
    }

    pub async fn run(&self) -> Result<()> {
        // Calculate time range
        let now = Local::now();
        let end_time = now;
        let start_time = end_time - Duration::days(self.days);

        // Load sessions
        eprintln!("Loading Claude sessions from the last {} days...", self.days);
        if let Some(ref project) = self.project {
            eprintln!("Filtering by project: {}", project);
        }

        let timelines = load_sessions_in_timerange(
            start_time,
            end_time,
            self.project.as_deref(),
            self.threads,
        )?;

        if timelines.is_empty() {
            eprintln!("No Claude sessions found in the specified time range.");
            return Ok(());
        }

        // Check if we're in a proper terminal environment
        if std::env::var("TERM").is_err() {
            return Err(anyhow::anyhow!("No terminal environment detected. Use --simple flag for text output."));
        }

        // Setup terminal with error handling
        let setup_result = || -> Result<()> {
            enable_raw_mode()?;
            Ok(())
        };

        if let Err(e) = setup_result() {
            return Err(anyhow::anyhow!("Failed to setup terminal: {}. Use --simple flag for text output.", e));
        }

        let mut stdout = io::stdout();
        
        // Try to setup crossterm without mouse capture initially
        if let Err(e) = execute!(stdout, EnterAlternateScreen) {
            disable_raw_mode().ok(); // Try to cleanup
            return Err(anyhow::anyhow!("Failed to enter alternate screen: {}. Use --simple flag for text output.", e));
        }

        let backend = CrosstermBackend::new(stdout);
        let mut terminal = match Terminal::new(backend) {
            Ok(term) => term,
            Err(e) => {
                disable_raw_mode().ok();
                execute!(io::stdout(), LeaveAlternateScreen).ok();
                return Err(anyhow::anyhow!("Failed to create terminal: {}. Use --simple flag for text output.", e));
            }
        };

        // Run the TUI
        let result = self.run_tui(&mut terminal, timelines, start_time, end_time).await;

        // Restore terminal
        disable_raw_mode().ok();
        execute!(
            terminal.backend_mut(),
            LeaveAlternateScreen
        ).ok();
        terminal.show_cursor().ok();

        result
    }

    async fn run_tui<B: Backend>(
        &self,
        terminal: &mut Terminal<B>,
        timelines: Vec<crate::claude_logs::SessionTimeline>,
        start_time: DateTime<Local>,
        end_time: DateTime<Local>,
    ) -> Result<()> {
        let ui = TimelineUI::new(timelines, start_time, end_time);

        loop {
            terminal.draw(|f| {
                ui.render(f, f.area());
            })?;

            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => {
                        break;
                    }
                    _ => {}
                }
            }
        }

        Ok(())
    }
}