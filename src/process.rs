use anyhow::Result;
use chrono::{DateTime, Local};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use sysinfo::{Pid, Process, ProcessRefreshKind, System};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub cpu_percent: f32,
    pub memory_mb: f64,
    pub runtime_seconds: u64,
    pub timestamp: DateTime<Local>,
    pub status: String,
    pub cmd: Vec<String>,
}

pub struct ProcessMonitor {
    system: System,
}

impl ProcessMonitor {
    pub fn new() -> Self {
        Self {
            system: System::new_all(),
        }
    }

    /// Refresh process information
    pub fn refresh(&mut self) {
        self.system.refresh_processes_specifics(
            ProcessRefreshKind::new()
                .with_cpu()
                .with_memory()
                .with_cmd(sysinfo::UpdateKind::OnlyIfNotSet),
        );
    }

    /// Get all Claude Code processes
    pub fn get_claude_processes(&self) -> Vec<ProcessInfo> {
        let mut processes = Vec::new();
        let now = Local::now();

        for (pid, process) in self.system.processes() {
            if self.is_claude_process(process) {
                let info = ProcessInfo {
                    pid: pid.as_u32(),
                    name: process.name().to_string_lossy().to_string(),
                    cpu_percent: process.cpu_usage(),
                    memory_mb: process.memory() as f64 / 1024.0 / 1024.0,
                    runtime_seconds: process.run_time(),
                    timestamp: now,
                    status: format!("{:?}", process.status()),
                    cmd: process.cmd().to_vec(),
                };
                processes.push(info);
            }
        }

        processes
    }

    /// Check if a process is a Claude Code process
    fn is_claude_process(&self, process: &Process) -> bool {
        let name = process.name().to_string_lossy().to_lowercase();
        let cmd = process.cmd().join(" ").to_lowercase();

        // Check for Claude Code process patterns
        name.contains("claude") 
            || cmd.contains("claude")
            || cmd.contains("anthropic")
            || (name.contains("node") && cmd.contains("claude-cli"))
    }

    /// Get total CPU usage percentage
    pub fn get_total_cpu_usage(&self) -> f32 {
        self.get_claude_processes()
            .iter()
            .map(|p| p.cpu_percent)
            .sum()
    }

    /// Get total memory usage in MB
    pub fn get_total_memory_mb(&self) -> f64 {
        self.get_claude_processes()
            .iter()
            .map(|p| p.memory_mb)
            .sum()
    }

    /// Get process count
    pub fn get_process_count(&self) -> usize {
        self.get_claude_processes().len()
    }

    /// Get process by PID
    pub fn get_process_by_pid(&self, pid: u32) -> Option<ProcessInfo> {
        self.get_claude_processes()
            .into_iter()
            .find(|p| p.pid == pid)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudeTask {
    pub id: String,
    pub name: String,
    pub status: String,
    pub created_at: DateTime<Local>,
    pub updated_at: DateTime<Local>,
}

/// Read Claude tasks from ~/.claude.json
pub fn read_claude_tasks() -> Result<Vec<ClaudeTask>> {
    use crate::utils::get_claude_json_path;
    use std::fs;

    let path = get_claude_json_path()?;
    
    if !path.exists() {
        return Ok(Vec::new());
    }

    let content = fs::read_to_string(&path)?;
    
    // Parse the JSON - actual structure may vary
    // This is a placeholder implementation
    let json: serde_json::Value = serde_json::from_str(&content)?;
    
    let mut tasks = Vec::new();
    
    if let Some(task_array) = json.get("tasks").and_then(|v| v.as_array()) {
        for task in task_array {
            if let Some(task_obj) = task.as_object() {
                let task = ClaudeTask {
                    id: task_obj.get("id")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                    name: task_obj.get("name")
                        .and_then(|v| v.as_str())
                        .unwrap_or("Unnamed Task")
                        .to_string(),
                    status: task_obj.get("status")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                    created_at: Local::now(), // Placeholder
                    updated_at: Local::now(), // Placeholder
                };
                tasks.push(task);
            }
        }
    }

    Ok(tasks)
}