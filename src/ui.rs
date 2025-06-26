use anyhow::Result;
use chrono::{DateTime, Local};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    symbols,
    text::{Line, Span},
    widgets::{
        Axis, Block, Borders, Cell, Chart, Dataset, Gauge, Paragraph, Row, Table, Tabs, Wrap,
    },
    Frame, Terminal,
};
use std::{
    io,
    time::{Duration, Instant},
};

use crate::{
    db::{ProcessMetric, ProcessStats},
    process::{ClaudeTask, ProcessInfo},
    utils::{format_bytes, format_duration},
};

pub struct UI {
    terminal: Terminal<CrosstermBackend<io::Stdout>>,
    selected_tab: usize,
}

impl UI {
    pub fn new() -> Result<Self> {
        // Setup terminal
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
        let backend = CrosstermBackend::new(stdout);
        let terminal = Terminal::new(backend)?;

        Ok(Self {
            terminal,
            selected_tab: 0,
        })
    }

    pub fn draw(
        &mut self,
        processes: &[ProcessInfo],
        stats: &ProcessStats,
        cpu_history: &[(DateTime<Local>, f32)],
        memory_history: &[(DateTime<Local>, f64)],
        tasks: &[ClaudeTask],
    ) -> Result<()> {
        self.terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .margin(1)
                .constraints(
                    [
                        Constraint::Length(3),  // Title
                        Constraint::Length(3),  // Tabs
                        Constraint::Min(0),     // Content
                    ]
                    .as_ref(),
                )
                .split(f.area());

            // Title
            self.render_title(f, chunks[0]);

            // Tabs
            self.render_tabs(f, chunks[1]);

            // Content based on selected tab
            match self.selected_tab {
                0 => self.render_overview(f, chunks[2], processes, stats, cpu_history, memory_history),
                1 => self.render_processes(f, chunks[2], processes),
                2 => self.render_tasks(f, chunks[2], tasks),
                _ => {}
            }
        })?;

        Ok(())
    }

    fn render_title(&self, f: &mut Frame, area: Rect) {
        let title = Paragraph::new("🖥️  Claude Code Monitor")
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::BOTTOM));
        f.render_widget(title, area);
    }

    fn render_tabs(&self, f: &mut Frame, area: Rect) {
        let tabs = vec!["Overview", "Processes", "Tasks"];
        let tabs = Tabs::new(tabs)
            .block(Block::default().borders(Borders::BOTTOM))
            .select(self.selected_tab)
            .style(Style::default().fg(Color::White))
            .highlight_style(
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD),
            );
        f.render_widget(tabs, area);
    }

    fn render_overview(
        &self,
        f: &mut Frame,
        area: Rect,
        processes: &[ProcessInfo],
        stats: &ProcessStats,
        cpu_history: &[(DateTime<Local>, f32)],
        memory_history: &[(DateTime<Local>, f64)],
    ) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints(
                [
                    Constraint::Length(8),   // Stats
                    Constraint::Percentage(50), // Charts
                    Constraint::Min(0),      // Process list
                ]
                .as_ref(),
            )
            .split(area);

        // Stats panel
        self.render_stats(f, chunks[0], stats);

        // Charts
        let chart_chunks = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
            .split(chunks[1]);

        self.render_cpu_chart(f, chart_chunks[0], cpu_history);
        self.render_memory_chart(f, chart_chunks[1], memory_history);

        // Process list
        self.render_process_list(f, chunks[2], processes);
    }

    fn render_stats(&self, f: &mut Frame, area: Rect, stats: &ProcessStats) {
        let stats_text = vec![
            Line::from(vec![
                Span::raw("Processes: "),
                Span::styled(
                    format!("{}", stats.process_count),
                    Style::default().fg(Color::Green),
                ),
            ]),
            Line::from(vec![
                Span::raw("CPU Usage: "),
                Span::styled(
                    format!("{:.1}%", stats.avg_cpu),
                    Style::default().fg(Color::Yellow),
                ),
                Span::raw(" (max: "),
                Span::styled(
                    format!("{:.1}%", stats.max_cpu),
                    Style::default().fg(Color::Red),
                ),
                Span::raw(")"),
            ]),
            Line::from(vec![
                Span::raw("Memory Usage: "),
                Span::styled(
                    format_bytes((stats.avg_memory * 1024.0 * 1024.0) as u64),
                    Style::default().fg(Color::Yellow),
                ),
                Span::raw(" (max: "),
                Span::styled(
                    format_bytes((stats.max_memory * 1024.0 * 1024.0) as u64),
                    Style::default().fg(Color::Red),
                ),
                Span::raw(")"),
            ]),
        ];

        let stats_paragraph = Paragraph::new(stats_text)
            .block(
                Block::default()
                    .title("📊 Statistics")
                    .borders(Borders::ALL),
            )
            .wrap(Wrap { trim: true });

        f.render_widget(stats_paragraph, area);
    }

    fn render_cpu_chart(&self, f: &mut Frame, area: Rect, cpu_history: &[(DateTime<Local>, f32)]) {
        if cpu_history.is_empty() {
            return;
        }

        let data: Vec<(f64, f64)> = cpu_history
            .iter()
            .enumerate()
            .map(|(i, (_, cpu))| (i as f64, *cpu as f64))
            .collect();

        let dataset = Dataset::default()
            .name("CPU %")
            .marker(symbols::Marker::Braille)
            .style(Style::default().fg(Color::Yellow))
            .data(&data);

        let chart = Chart::new(vec![dataset])
            .block(
                Block::default()
                    .title("📈 CPU Usage")
                    .borders(Borders::ALL),
            )
            .x_axis(
                Axis::default()
                    .style(Style::default().fg(Color::Gray))
                    .bounds([0.0, data.len() as f64]),
            )
            .y_axis(
                Axis::default()
                    .style(Style::default().fg(Color::Gray))
                    .bounds([0.0, 100.0])
                    .labels(vec!["0", "50", "100"]),
            );

        f.render_widget(chart, area);
    }

    fn render_memory_chart(
        &self,
        f: &mut Frame,
        area: Rect,
        memory_history: &[(DateTime<Local>, f64)],
    ) {
        if memory_history.is_empty() {
            return;
        }

        let max_memory = memory_history
            .iter()
            .map(|(_, mem)| *mem)
            .fold(0.0, f64::max);

        let data: Vec<(f64, f64)> = memory_history
            .iter()
            .enumerate()
            .map(|(i, (_, mem))| (i as f64, *mem))
            .collect();

        let dataset = Dataset::default()
            .name("Memory MB")
            .marker(symbols::Marker::Braille)
            .style(Style::default().fg(Color::Cyan))
            .data(&data);

        let chart = Chart::new(vec![dataset])
            .block(
                Block::default()
                    .title("📊 Memory Usage")
                    .borders(Borders::ALL),
            )
            .x_axis(
                Axis::default()
                    .style(Style::default().fg(Color::Gray))
                    .bounds([0.0, data.len() as f64]),
            )
            .y_axis(
                Axis::default()
                    .style(Style::default().fg(Color::Gray))
                    .bounds([0.0, max_memory * 1.1])
                    .labels(vec![
                        "0",
                        &format!("{:.0}", max_memory / 2.0),
                        &format!("{:.0}", max_memory),
                    ]),
            );

        f.render_widget(chart, area);
    }

    fn render_process_list(&self, f: &mut Frame, area: Rect, processes: &[ProcessInfo]) {
        let header = Row::new(vec!["PID", "Name", "CPU %", "Memory", "Runtime", "Status"])
            .style(Style::default().fg(Color::Yellow))
            .bottom_margin(1);

        let rows: Vec<Row> = processes
            .iter()
            .map(|p| {
                Row::new(vec![
                    Cell::from(p.pid.to_string()),
                    Cell::from(p.name.clone()),
                    Cell::from(format!("{:.1}", p.cpu_percent)),
                    Cell::from(format_bytes((p.memory_mb * 1024.0 * 1024.0) as u64)),
                    Cell::from(format_duration(p.runtime_seconds)),
                    Cell::from(p.status.clone()),
                ])
            })
            .collect();

        let table = Table::new(
            rows,
            &[
                Constraint::Length(8),
                Constraint::Min(20),
                Constraint::Length(8),
                Constraint::Length(10),
                Constraint::Length(10),
                Constraint::Min(10),
            ],
        )
        .header(header)
        .block(
            Block::default()
                .title("🔍 Active Processes")
                .borders(Borders::ALL),
        );

        f.render_widget(table, area);
    }

    fn render_processes(&self, f: &mut Frame, area: Rect, processes: &[ProcessInfo]) {
        self.render_process_list(f, area, processes);
    }

    fn render_tasks(&self, f: &mut Frame, area: Rect, tasks: &[ClaudeTask]) {
        let header = Row::new(vec!["ID", "Name", "Status", "Created", "Updated"])
            .style(Style::default().fg(Color::Yellow))
            .bottom_margin(1);

        let rows: Vec<Row> = tasks
            .iter()
            .map(|t| {
                Row::new(vec![
                    Cell::from(t.id.clone()),
                    Cell::from(t.name.clone()),
                    Cell::from(t.status.clone()),
                    Cell::from(t.created_at.format("%Y-%m-%d %H:%M").to_string()),
                    Cell::from(t.updated_at.format("%Y-%m-%d %H:%M").to_string()),
                ])
            })
            .collect();

        let table = Table::new(
            rows,
            &[
                Constraint::Length(10),
                Constraint::Min(30),
                Constraint::Length(15),
                Constraint::Length(16),
                Constraint::Length(16),
            ],
        )
        .header(header)
        .block(
            Block::default()
                .title("📋 Claude Tasks")
                .borders(Borders::ALL),
        );

        f.render_widget(table, area);
    }

    pub fn handle_input(&mut self) -> Result<bool> {
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(true),
                    KeyCode::Tab => {
                        self.selected_tab = (self.selected_tab + 1) % 3;
                    }
                    KeyCode::BackTab => {
                        if self.selected_tab == 0 {
                            self.selected_tab = 2;
                        } else {
                            self.selected_tab -= 1;
                        }
                    }
                    _ => {}
                }
            }
        }
        Ok(false)
    }

    pub fn show_summary(
        &mut self,
        stats: &ProcessStats,
        processes: &[ProcessInfo],
    ) -> Result<()> {
        self.terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .margin(2)
                .constraints(
                    [
                        Constraint::Length(3),  // Title
                        Constraint::Length(10), // Stats
                        Constraint::Min(0),     // Process list
                    ]
                    .as_ref(),
                )
                .split(f.area());

            // Title
            self.render_title(f, chunks[0]);

            // Stats
            self.render_stats(f, chunks[1], stats);

            // Process list
            self.render_process_list(f, chunks[2], processes);
        })?;

        Ok(())
    }
}

impl Drop for UI {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(
            self.terminal.backend_mut(),
            LeaveAlternateScreen,
            DisableMouseCapture
        );
    }
}