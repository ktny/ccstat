use crate::claude_logs::SessionTimeline;
use chrono::{DateTime, Local, Timelike, Datelike};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Row, Table},
    Frame,
};

pub struct TimelineUI {
    pub timelines: Vec<SessionTimeline>,
    pub start_time: DateTime<Local>,
    pub end_time: DateTime<Local>,
}

impl TimelineUI {
    pub fn new(
        timelines: Vec<SessionTimeline>,
        start_time: DateTime<Local>,
        end_time: DateTime<Local>,
    ) -> Self {
        Self {
            timelines,
            start_time,
            end_time,
        }
    }

    pub fn render(&self, frame: &mut Frame, area: Rect) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .margin(1)
            .constraints([
                Constraint::Min(3),  // Header
                Constraint::Min(10), // Timeline table
                Constraint::Min(5),  // Summary
            ])
            .split(area);

        // Render header
        self.render_header(frame, chunks[0]);

        // Render timeline table
        self.render_timeline_table(frame, chunks[1]);

        // Render summary
        self.render_summary(frame, chunks[2]);
    }

    fn render_header(&self, frame: &mut Frame, area: Rect) {
        let duration = self.end_time.signed_duration_since(self.start_time);
        let hours = duration.num_hours();

        let header_text = vec![
            Line::from(vec![
                Span::styled("📊 Claude Project Timeline", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
                Span::raw(" | "),
                Span::raw(self.start_time.format("%m/%d/%Y %H:%M").to_string()),
                Span::raw(" - "),
                Span::raw(self.end_time.format("%m/%d/%Y %H:%M").to_string()),
                Span::styled(format!(" ({} hours)", hours), Style::default().add_modifier(Modifier::BOLD)),
                Span::raw(" | "),
                Span::styled(format!("{} projects", self.timelines.len()), Style::default().fg(Color::Yellow)),
            ]),
        ];

        let header = Paragraph::new(header_text)
            .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::Blue)));

        frame.render_widget(header, area);
    }

    fn render_timeline_table(&self, frame: &mut Frame, area: Rect) {
        if self.timelines.is_empty() {
            let no_data = Paragraph::new("🔍 No Claude sessions found in the specified time range")
                .style(Style::default().fg(Color::Yellow))
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::Yellow)));
            frame.render_widget(no_data, area);
            return;
        }

        // Calculate timeline width
        let timeline_width = (area.width as usize).saturating_sub(80).max(20);

        // Create table headers
        let timeline_header = self.create_timeline_header();
        let headers = Row::new(vec![
            "Project",
            &timeline_header,
            "Events",
            "Input",
            "Output", 
            "Duration",
        ])
        .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD));

        // Create time axis row
        let time_axis = self.create_time_axis(timeline_width);
        let time_axis_row = Row::new(vec![
            "",
            &time_axis,
            "",
            "",
            "",
            "",
        ]);

        // Create data rows
        let mut rows = vec![time_axis_row];
        
        for timeline in &self.timelines {
            let timeline_str = self.create_timeline_string(timeline, timeline_width);
            let input_tokens = if timeline.total_input_tokens > 0 {
                Self::format_number(timeline.total_input_tokens)
            } else {
                "-".to_string()
            };
            let output_tokens = if timeline.total_output_tokens > 0 {
                Self::format_number(timeline.total_output_tokens)
            } else {
                "-".to_string()
            };

            let project_display = if let Some(ref _parent) = timeline.parent_project {
                format!(" └─{}", timeline.project_name)
            } else {
                timeline.project_name.clone()
            };

            let row = Row::new(vec![
                project_display,
                timeline_str,
                timeline.events.len().to_string(),
                input_tokens,
                output_tokens,
                format!("{}m", timeline.active_duration_minutes),
            ]);

            rows.push(row);
        }

        let table = Table::new(rows, [
            Constraint::Length(30),  // Project
            Constraint::Min(20),     // Timeline
            Constraint::Length(6),   // Events
            Constraint::Length(8),   // Input
            Constraint::Length(8),   // Output
            Constraint::Length(8),   // Duration
        ])
        .header(headers)
        .block(Block::default().title("Project Activity").borders(Borders::ALL).border_style(Style::default().fg(Color::Cyan)));

        frame.render_widget(table, area);
    }

    fn render_summary(&self, frame: &mut Frame, area: Rect) {
        if self.timelines.is_empty() {
            return;
        }

        let total_events: usize = self.timelines.iter().map(|t| t.events.len()).sum();
        let total_projects = self.timelines.len();
        
        let most_active = self.timelines
            .iter()
            .max_by_key(|t| t.events.len())
            .unwrap();

        let avg_duration: f64 = self.timelines
            .iter()
            .map(|t| t.active_duration_minutes as f64)
            .sum::<f64>() / total_projects as f64;

        let summary_text = vec![
            Line::from(vec![
                Span::styled("Summary Statistics:", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::raw("  • Total Projects: "),
                Span::styled(total_projects.to_string(), Style::default().fg(Color::Yellow)),
            ]),
            Line::from(vec![
                Span::raw("  • Total Events: "),
                Span::styled(total_events.to_string(), Style::default().fg(Color::Yellow)),
            ]),
            Line::from(vec![
                Span::raw("  • Average Duration: "),
                Span::styled(format!("{:.1} minutes", avg_duration), Style::default().fg(Color::Yellow)),
            ]),
            Line::from(vec![
                Span::raw("  • Most Active Project: "),
                Span::styled(&most_active.project_name, Style::default().fg(Color::Yellow)),
                Span::raw(format!(" ({} events)", most_active.events.len())),
            ]),
        ];

        let summary = Paragraph::new(summary_text);
        frame.render_widget(summary, area);
    }

    fn create_timeline_header(&self) -> String {
        "Timeline ■■■■■".to_string()
    }

    fn create_time_axis(&self, width: usize) -> String {
        let total_duration = self.end_time.signed_duration_since(self.start_time);
        let total_hours = total_duration.num_hours();

        let mut axis_chars = vec![' '; width];

        // Simple time markers for now - show every few hours/days
        if total_hours <= 24 {
            // Hour markers
            let interval = 3; // Every 3 hours
            let mut current = self.start_time;
            current = current
                .with_minute(0)
                .unwrap()
                .with_second(0)
                .unwrap()
                .with_nanosecond(0)
                .unwrap();

            while current <= self.end_time {
                if current >= self.start_time {
                    let offset_seconds = current.signed_duration_since(self.start_time).num_seconds();
                    let position = ((offset_seconds as f64 / total_duration.num_seconds() as f64) * (width - 1) as f64) as usize;

                    if position < width.saturating_sub(2) {
                        let label = format!("{:02}", current.hour());
                        for (i, ch) in label.chars().enumerate() {
                            if position + i < width {
                                axis_chars[position + i] = ch;
                            }
                        }
                    }
                }
                current = current + chrono::Duration::hours(interval);
            }
        } else {
            // Day markers
            let mut current = self.start_time
                .with_hour(0)
                .unwrap()
                .with_minute(0)
                .unwrap()
                .with_second(0)
                .unwrap()
                .with_nanosecond(0)
                .unwrap();

            while current <= self.end_time {
                if current >= self.start_time {
                    let offset_seconds = current.signed_duration_since(self.start_time).num_seconds();
                    let position = ((offset_seconds as f64 / total_duration.num_seconds() as f64) * (width - 1) as f64) as usize;

                    if position < width.saturating_sub(5) {
                        let label = format!("{:02}/{:02}", current.month(), current.day());
                        for (i, ch) in label.chars().enumerate() {
                            if position + i < width {
                                axis_chars[position + i] = ch;
                            }
                        }
                    }
                }
                current = current + chrono::Duration::days(1);
            }
        }

        axis_chars.into_iter().collect()
    }

    fn create_timeline_string(&self, timeline: &SessionTimeline, width: usize) -> String {
        let mut timeline_chars = vec!['■'; width];
        let mut activity_counts = vec![0u32; width];

        let total_duration = self.end_time.signed_duration_since(self.start_time);

        // Count events per position
        for event in &timeline.events {
            let event_offset = event.timestamp.signed_duration_since(self.start_time);
            let position = ((event_offset.num_seconds() as f64 / total_duration.num_seconds() as f64) * width as f64) as usize;
            
            if position < width {
                activity_counts[position] += 1;
            }
        }

        // Find max activity for normalization
        let max_activity = *activity_counts.iter().max().unwrap_or(&1);

        // Create timeline string with basic density indication
        // Note: Ratatui doesn't support rich markup like Rich, so we use simple characters
        for (i, &count) in activity_counts.iter().enumerate() {
            if count == 0 {
                timeline_chars[i] = '·'; // Low activity
            } else {
                let density = ((count as f64 / max_activity as f64) * 4.0) as u32;
                timeline_chars[i] = match density {
                    0 => '·',
                    1 => '▪',
                    2 => '▫',
                    3 => '■',
                    _ => '█',
                };
            }
        }

        timeline_chars.into_iter().collect()
    }

    fn format_number(num: u32) -> String {
        // Simple number formatting with commas
        let num_str = num.to_string();
        let len = num_str.len();
        let mut result = String::new();
        
        for (i, ch) in num_str.chars().enumerate() {
            if i > 0 && (len - i) % 3 == 0 {
                result.push(',');
            }
            result.push(ch);
        }
        
        result
    }
}