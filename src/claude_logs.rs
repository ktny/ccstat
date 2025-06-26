use anyhow::{Context, Result};
use chrono::{DateTime, Local};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use crate::git_utils::get_repository_name;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionEvent {
    pub timestamp: DateTime<Local>,
    pub session_id: String,
    pub directory: String,
    pub message_type: String,
    pub content_preview: String,
    pub uuid: String,
    pub input_tokens: u32,
    pub output_tokens: u32,
}

#[derive(Debug, Clone)]
pub struct SessionTimeline {
    pub session_id: String,
    pub directory: String,
    pub project_name: String,
    pub events: Vec<SessionEvent>,
    pub start_time: DateTime<Local>,
    pub end_time: DateTime<Local>,
    pub active_duration_minutes: u32,
    pub parent_project: Option<String>,
    pub total_input_tokens: u32,
    pub total_output_tokens: u32,
}

#[derive(Debug, Deserialize)]
struct LogEntry {
    timestamp: String,
    #[serde(rename = "sessionId")]
    session_id: Option<String>,
    cwd: Option<String>,
    message: Option<LogMessage>,
    #[serde(rename = "type")]
    entry_type: Option<String>,
    uuid: Option<String>,
}

#[derive(Debug, Deserialize)]
struct LogMessage {
    role: Option<String>,
    content: Option<serde_json::Value>,
    usage: Option<TokenUsage>,
}

#[derive(Debug, Deserialize)]
struct TokenUsage {
    input_tokens: Option<u32>,
    output_tokens: Option<u32>,
}

impl SessionEvent {
    fn from_log_entry(entry: LogEntry) -> Option<Self> {
        let timestamp_str = entry.timestamp;
        
        // Parse ISO format timestamp and convert to local time
        let timestamp = if timestamp_str.ends_with('Z') {
            DateTime::parse_from_rfc3339(&timestamp_str.replace('Z', "+00:00"))
                .ok()?
                .with_timezone(&Local)
        } else {
            DateTime::parse_from_rfc3339(&timestamp_str)
                .ok()?
                .with_timezone(&Local)
        };

        let session_id = entry.session_id.unwrap_or_default();
        let directory = entry.cwd.unwrap_or_default();
        let uuid = entry.uuid.unwrap_or_default();

        let (message_type, content_preview, input_tokens, output_tokens) = 
            if let Some(message) = entry.message {
                let role = message.role.unwrap_or_else(|| 
                    entry.entry_type.unwrap_or_else(|| "unknown".to_string())
                );
                
                let content = Self::extract_content_text(&message.content);
                let content_preview = if content.len() > 100 {
                    format!("{}...", &content[..100])
                } else {
                    content
                }.replace('\n', " ");

                let (input_tokens, output_tokens) = if role == "assistant" {
                    if let Some(usage) = message.usage {
                        (
                            usage.input_tokens.unwrap_or(0),
                            usage.output_tokens.unwrap_or(0)
                        )
                    } else {
                        (0, 0)
                    }
                } else {
                    (0, 0)
                };

                (role, content_preview, input_tokens, output_tokens)
            } else {
                ("unknown".to_string(), String::new(), 0, 0)
            };

        Some(SessionEvent {
            timestamp,
            session_id,
            directory,
            message_type,
            content_preview,
            uuid,
            input_tokens,
            output_tokens,
        })
    }

    fn extract_content_text(content: &Option<serde_json::Value>) -> String {
        match content {
            Some(serde_json::Value::String(s)) => s.clone(),
            Some(serde_json::Value::Array(arr)) => {
                arr.iter()
                    .filter_map(|item| {
                        if let serde_json::Value::Object(obj) = item {
                            if obj.get("type")? == "text" {
                                obj.get("text")?.as_str().map(|s| s.to_string())
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            }
            Some(other) => other.to_string(),
            None => String::new(),
        }
    }
}

pub fn parse_jsonl_file<P: AsRef<Path>>(file_path: P) -> Result<Vec<SessionEvent>> {
    let file = File::open(&file_path)
        .with_context(|| format!("Failed to open file: {}", file_path.as_ref().display()))?;
    
    let reader = BufReader::new(file);
    let mut events = Vec::new();

    for (line_num, line) in reader.lines().enumerate() {
        let line = line
            .with_context(|| format!("Failed to read line {} from file", line_num + 1))?;
        
        if line.trim().is_empty() {
            continue;
        }

        let entry: LogEntry = serde_json::from_str(&line)
            .with_context(|| format!("Failed to parse JSON on line {}", line_num + 1))?;
        
        if let Some(event) = SessionEvent::from_log_entry(entry) {
            events.push(event);
        }
    }

    Ok(events)
}

pub fn calculate_active_duration(events: &[SessionEvent]) -> u32 {
    if events.is_empty() {
        return 0;
    }

    if events.len() == 1 {
        return 5; // Minimum 5 minutes for single event
    }

    let mut total_minutes = 0;
    let threshold_minutes = 1; // 1 minute threshold

    for window in events.windows(2) {
        let diff = window[1].timestamp.signed_duration_since(window[0].timestamp);
        let minutes = diff.num_minutes();
        
        if minutes <= threshold_minutes {
            total_minutes += minutes;
        }
    }

    total_minutes.max(0) as u32
}

pub fn calculate_token_totals(events: &[SessionEvent]) -> (u32, u32) {
    events.iter().fold((0, 0), |(input_total, output_total), event| {
        (
            input_total + event.input_tokens,
            output_total + event.output_tokens,
        )
    })
}

pub fn load_sessions_in_timerange(
    start_time: DateTime<Local>,
    end_time: DateTime<Local>,
    project_filter: Option<&str>,
    _threads: bool,
) -> Result<Vec<SessionTimeline>> {
    let claude_dir = dirs::home_dir()
        .context("Could not find home directory")?
        .join(".claude/projects");

    if !claude_dir.exists() {
        return Ok(Vec::new());
    }

    let mut all_events = Vec::new();

    // Recursively find all .jsonl files
    for entry in walkdir::WalkDir::new(&claude_dir)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        if entry.file_type().is_file() {
            if let Some(extension) = entry.path().extension() {
                if extension == "jsonl" {
                    match parse_jsonl_file(entry.path()) {
                        Ok(mut events) => {
                            // Filter events by time range
                            events.retain(|event| {
                                event.timestamp >= start_time && event.timestamp <= end_time
                            });
                            all_events.extend(events);
                        }
                        Err(_) => {
                            // Skip files that can't be parsed
                            continue;
                        }
                    }
                }
            }
        }
    }

    // Group events by session and directory
    let mut session_groups: HashMap<(String, String), Vec<SessionEvent>> = HashMap::new();
    
    for event in all_events {
        let key = (event.session_id.clone(), event.directory.clone());
        session_groups.entry(key).or_default().push(event);
    }

    let mut timelines = Vec::new();

    for ((session_id, directory), mut events) in session_groups {
        // Sort events by timestamp
        events.sort_by_key(|e| e.timestamp);

        if events.is_empty() {
            continue;
        }

        let start_time = events.first().unwrap().timestamp;
        let end_time = events.last().unwrap().timestamp;
        
        let project_name = get_repository_name(&directory)
            .unwrap_or_else(|| {
                Path::new(&directory)
                    .file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or("unknown")
                    .to_string()
            });

        // Apply project filter
        if let Some(filter) = project_filter {
            if !project_name.contains(filter) {
                continue;
            }
        }

        let active_duration_minutes = calculate_active_duration(&events);
        let (total_input_tokens, total_output_tokens) = calculate_token_totals(&events);

        let timeline = SessionTimeline {
            session_id,
            directory,
            project_name,
            events,
            start_time,
            end_time,
            active_duration_minutes,
            parent_project: None, // TODO: Implement parent project grouping
            total_input_tokens,
            total_output_tokens,
        };

        timelines.push(timeline);
    }

    // Sort timelines by start time
    timelines.sort_by_key(|t| t.start_time);

    Ok(timelines)
}