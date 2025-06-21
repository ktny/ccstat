"""Database functionality for persisting process information."""

import os
from pathlib import Path
from typing import Optional

import duckdb

from .process import ProcessInfo


class ProcessDatabase:
    """Database manager for persisting Claude process information."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database.

        Args:
            db_path: Path to the database file. If None, uses default location.
        """
        if db_path is None:
            # Use ~/.config/ccmonitor/processes.db as default
            config_dir = Path.home() / ".config" / "ccmonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(config_dir / "processes.db")
        else:
            self.db_path = db_path

        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database schema."""
        with duckdb.connect(self.db_path) as conn:
            # Create processes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER,
                    pid INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    cpu_time DOUBLE NOT NULL,
                    memory_mb DOUBLE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    elapsed_seconds INTEGER NOT NULL,
                    cmdline VARCHAR NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR DEFAULT 'running'
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processes_pid 
                ON processes(pid)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processes_recorded_at 
                ON processes(recorded_at)
            """)

    def save_process(self, process: ProcessInfo) -> None:
        """Save a process to the database.

        Args:
            process: ProcessInfo object to save
        """
        with duckdb.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO processes (
                    pid, name, cpu_time, memory_mb, start_time, 
                    elapsed_seconds, cmdline
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    process.pid,
                    process.name,
                    process.cpu_time,
                    process.memory_mb,
                    process.start_time,
                    int(process.elapsed_time.total_seconds()),
                    " ".join(process.cmdline),
                ),
            )

    def save_processes(self, processes: list[ProcessInfo]) -> None:
        """Save multiple processes to the database.

        Args:
            processes: List of ProcessInfo objects to save
        """
        if not processes:
            return

        with duckdb.connect(self.db_path) as conn:
            # Mark currently running processes as terminated
            self._mark_terminated_processes(conn, [p.pid for p in processes])

            # Insert new process records
            data = [
                (
                    p.pid,
                    p.name,
                    p.cpu_time,
                    p.memory_mb,
                    p.start_time,
                    int(p.elapsed_time.total_seconds()),
                    " ".join(p.cmdline),
                )
                for p in processes
            ]

            conn.executemany(
                """
                INSERT INTO processes (
                    pid, name, cpu_time, memory_mb, start_time,
                    elapsed_seconds, cmdline
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

    def _mark_terminated_processes(
        self, conn: duckdb.DuckDBPyConnection, current_pids: list[int]
    ) -> None:
        """Mark processes not in current_pids as terminated.

        Args:
            conn: Database connection
            current_pids: List of currently running PIDs
        """
        if current_pids:
            # Convert to comma-separated string for SQL IN clause
            pid_list = ",".join(map(str, current_pids))
            conn.execute(f"""
                UPDATE processes 
                SET status = 'terminated'
                WHERE status = 'running' 
                AND pid NOT IN ({pid_list})
            """)
        else:
            # No running processes, mark all as terminated
            conn.execute("""
                UPDATE processes 
                SET status = 'terminated'
                WHERE status = 'running'
            """)

    def get_recent_processes(self, limit: int = 50) -> list[dict]:
        """Get recent process records from the database.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of process records as dictionaries
        """
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT 
                    pid, name, cpu_time, memory_mb, start_time,
                    elapsed_seconds, cmdline, recorded_at, status
                FROM processes
                ORDER BY recorded_at DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

            columns = [
                "pid",
                "name",
                "cpu_time",
                "memory_mb",
                "start_time",
                "elapsed_seconds",
                "cmdline",
                "recorded_at",
                "status",
            ]

            return [dict(zip(columns, row)) for row in result]

    def get_process_history(self, pid: int) -> list[dict]:
        """Get history for a specific process PID.

        Args:
            pid: Process ID to get history for

        Returns:
            List of process records for the given PID
        """
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT 
                    pid, name, cpu_time, memory_mb, start_time,
                    elapsed_seconds, cmdline, recorded_at, status
                FROM processes
                WHERE pid = ?
                ORDER BY recorded_at DESC
            """,
                (pid,),
            ).fetchall()

            columns = [
                "pid",
                "name",
                "cpu_time",
                "memory_mb",
                "start_time",
                "elapsed_seconds",
                "cmdline",
                "recorded_at",
                "status",
            ]

            return [dict(zip(columns, row)) for row in result]

    def get_summary_stats(self) -> dict:
        """Get summary statistics from the database.

        Returns:
            Dictionary containing summary statistics
        """
        with duckdb.connect(self.db_path) as conn:
            # Get total records count
            total_records = conn.execute("""
                SELECT COUNT(*) FROM processes
            """).fetchone()[0]

            # Get unique processes count
            unique_processes = conn.execute("""
                SELECT COUNT(DISTINCT pid) FROM processes
            """).fetchone()[0]

            # Get currently running processes
            running_processes = conn.execute("""
                SELECT COUNT(*) FROM processes 
                WHERE status = 'running'
            """).fetchone()[0]

            # Get total memory usage of running processes
            total_memory = conn.execute("""
                SELECT COALESCE(SUM(memory_mb), 0) 
                FROM processes 
                WHERE status = 'running'
            """).fetchone()[0]

            # Get total CPU time of all recorded processes
            total_cpu_time = conn.execute("""
                SELECT COALESCE(SUM(cpu_time), 0) 
                FROM processes
            """).fetchone()[0]

            # Get oldest and newest records
            date_range = conn.execute("""
                SELECT MIN(recorded_at), MAX(recorded_at) 
                FROM processes
            """).fetchone()

            return {
                "total_records": total_records,
                "unique_processes": unique_processes,
                "running_processes": running_processes,
                "total_memory_mb": total_memory,
                "total_cpu_time": total_cpu_time,
                "oldest_record": date_range[0],
                "newest_record": date_range[1],
            }

    def cleanup_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days.

        Args:
            days: Number of days to keep records for

        Returns:
            Number of records deleted
        """
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute(f"""
                DELETE FROM processes 
                WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL {days} DAY
            """)

            return result.rowcount if result.rowcount else 0

    def get_database_size(self) -> int:
        """Get the size of the database file in bytes.

        Returns:
            Size of database file in bytes, or 0 if file doesn't exist
        """
        try:
            return os.path.getsize(self.db_path)
        except OSError:
            return 0
