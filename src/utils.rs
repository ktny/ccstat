use anyhow::Result;
use dirs::home_dir;
use std::path::PathBuf;

/// Get the path to the ccmonitor data directory
pub fn get_data_dir() -> Result<PathBuf> {
    let mut path = home_dir()
        .ok_or_else(|| anyhow::anyhow!("Failed to get home directory"))?;
    path.push(".ccmonitor");
    Ok(path)
}

/// Get the path to the ccmonitor database file
pub fn get_db_path() -> Result<PathBuf> {
    let mut path = get_data_dir()?;
    path.push("data.db");
    Ok(path)
}

/// Get the path to Claude's JSON file
pub fn get_claude_json_path() -> Result<PathBuf> {
    let mut path = home_dir()
        .ok_or_else(|| anyhow::anyhow!("Failed to get home directory"))?;
    path.push(".claude.json");
    Ok(path)
}

/// Format bytes into human-readable string
pub fn format_bytes(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB", "TB"];
    let mut size = bytes as f64;
    let mut unit_index = 0;

    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }

    if unit_index == 0 {
        format!("{} {}", size as u64, UNITS[unit_index])
    } else {
        format!("{:.1} {}", size, UNITS[unit_index])
    }
}

/// Format duration into human-readable string
pub fn format_duration(seconds: u64) -> String {
    let hours = seconds / 3600;
    let minutes = (seconds % 3600) / 60;
    let secs = seconds % 60;

    if hours > 0 {
        format!("{:02}:{:02}:{:02}", hours, minutes, secs)
    } else {
        format!("{:02}:{:02}", minutes, secs)
    }
}