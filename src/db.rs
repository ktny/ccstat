use anyhow::Result;
use chrono::{DateTime, Local, NaiveDateTime};
use duckdb::{params, Connection};
use std::fs;
use std::path::PathBuf;

use crate::process::ProcessInfo;
use crate::utils::get_data_dir;

pub struct Database {
    conn: Connection,
}

impl Database {
    /// Create a new database connection
    pub fn new() -> Result<Self> {
        let data_dir = get_data_dir()?;
        
        // Create directory if it doesn't exist
        fs::create_dir_all(&data_dir)?;
        
        let db_path = data_dir.join("data.db");
        let conn = Connection::open(&db_path)?;
        
        let mut db = Self { conn };
        db.init_schema()?;
        
        Ok(db)
    }

    /// Initialize database schema
    fn init_schema(&mut self) -> Result<()> {
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS process_metrics (
                id INTEGER PRIMARY KEY,
                pid INTEGER NOT NULL,
                name TEXT NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_mb REAL NOT NULL,
                runtime_seconds INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                cmd TEXT NOT NULL
            )",
            [],
        )?;

        // Create index for faster queries
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON process_metrics(timestamp)",
            [],
        )?;

        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pid ON process_metrics(pid)",
            [],
        )?;

        Ok(())
    }

    /// Insert process metrics
    pub fn insert_process_metrics(&mut self, process: &ProcessInfo) -> Result<()> {
        self.conn.execute(
            "INSERT INTO process_metrics 
            (pid, name, cpu_percent, memory_mb, runtime_seconds, timestamp, status, cmd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            params![
                process.pid,
                &process.name,
                process.cpu_percent,
                process.memory_mb,
                process.runtime_seconds,
                process.timestamp.naive_local(),
                &process.status,
                serde_json::to_string(&process.cmd)?
            ],
        )?;

        Ok(())
    }

    /// Get process statistics for a time range
    pub fn get_process_stats(
        &self,
        start_time: Option<DateTime<Local>>,
        end_time: Option<DateTime<Local>>,
    ) -> Result<ProcessStats> {
        let mut query = String::from(
            "SELECT 
                COUNT(DISTINCT pid) as process_count,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_mb) as avg_memory,
                MAX(memory_mb) as max_memory,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM process_metrics"
        );

        let mut conditions = Vec::new();
        
        if let Some(start) = start_time {
            conditions.push(format!("timestamp >= '{}'", start.naive_local()));
        }
        
        if let Some(end) = end_time {
            conditions.push(format!("timestamp <= '{}'", end.naive_local()));
        }

        if !conditions.is_empty() {
            query.push_str(" WHERE ");
            query.push_str(&conditions.join(" AND "));
        }

        let mut stmt = self.conn.prepare(&query)?;
        let stats = stmt.query_row([], |row| {
            Ok(ProcessStats {
                process_count: row.get(0)?,
                avg_cpu: row.get(1)?,
                max_cpu: row.get(2)?,
                avg_memory: row.get(3)?,
                max_memory: row.get(4)?,
                start_time: row.get::<_, Option<NaiveDateTime>>(5)?
                    .map(|dt| DateTime::from_naive_utc_and_offset(dt, *Local::now().offset())),
                end_time: row.get::<_, Option<NaiveDateTime>>(6)?
                    .map(|dt| DateTime::from_naive_utc_and_offset(dt, *Local::now().offset())),
            })
        })?;

        Ok(stats)
    }

    /// Get recent process metrics
    pub fn get_recent_metrics(&self, limit: usize) -> Result<Vec<ProcessMetric>> {
        let mut stmt = self.conn.prepare(
            "SELECT pid, name, cpu_percent, memory_mb, timestamp 
            FROM process_metrics 
            ORDER BY timestamp DESC 
            LIMIT ?"
        )?;

        let metrics = stmt
            .query_map([limit], |row| {
                Ok(ProcessMetric {
                    pid: row.get(0)?,
                    name: row.get(1)?,
                    cpu_percent: row.get(2)?,
                    memory_mb: row.get(3)?,
                    timestamp: DateTime::from_naive_utc_and_offset(
                        row.get::<_, NaiveDateTime>(4)?,
                        *Local::now().offset()
                    ),
                })
            })?
            .collect::<Result<Vec<_>, _>>()?;

        Ok(metrics)
    }

    /// Get CPU usage history for graphs
    pub fn get_cpu_history(&self, minutes: u32) -> Result<Vec<(DateTime<Local>, f32)>> {
        let query = format!(
            "SELECT timestamp, SUM(cpu_percent) as total_cpu
            FROM process_metrics
            WHERE timestamp >= datetime('now', '-{} minutes')
            GROUP BY timestamp
            ORDER BY timestamp",
            minutes
        );

        let mut stmt = self.conn.prepare(&query)?;
        let history = stmt
            .query_map([], |row| {
                let timestamp = DateTime::from_naive_utc_and_offset(
                    row.get::<_, NaiveDateTime>(0)?,
                    *Local::now().offset()
                );
                let cpu: f32 = row.get(1)?;
                Ok((timestamp, cpu))
            })?
            .collect::<Result<Vec<_>, _>>()?;

        Ok(history)
    }

    /// Get memory usage history for graphs
    pub fn get_memory_history(&self, minutes: u32) -> Result<Vec<(DateTime<Local>, f64)>> {
        let query = format!(
            "SELECT timestamp, SUM(memory_mb) as total_memory
            FROM process_metrics
            WHERE timestamp >= datetime('now', '-{} minutes')
            GROUP BY timestamp
            ORDER BY timestamp",
            minutes
        );

        let mut stmt = self.conn.prepare(&query)?;
        let history = stmt
            .query_map([], |row| {
                let timestamp = DateTime::from_naive_utc_and_offset(
                    row.get::<_, NaiveDateTime>(0)?,
                    *Local::now().offset()
                );
                let memory: f64 = row.get(1)?;
                Ok((timestamp, memory))
            })?
            .collect::<Result<Vec<_>, _>>()?;

        Ok(history)
    }

    /// Clean up old data (older than 7 days by default)
    pub fn cleanup_old_data(&mut self, days: u32) -> Result<()> {
        self.conn.execute(
            &format!(
                "DELETE FROM process_metrics 
                WHERE timestamp < datetime('now', '-{} days')",
                days
            ),
            [],
        )?;

        // Vacuum to reclaim space
        self.conn.execute("VACUUM", [])?;

        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct ProcessStats {
    pub process_count: i32,
    pub avg_cpu: f32,
    pub max_cpu: f32,
    pub avg_memory: f64,
    pub max_memory: f64,
    pub start_time: Option<DateTime<Local>>,
    pub end_time: Option<DateTime<Local>>,
}

#[derive(Debug, Clone)]
pub struct ProcessMetric {
    pub pid: u32,
    pub name: String,
    pub cpu_percent: f32,
    pub memory_mb: f64,
    pub timestamp: DateTime<Local>,
}