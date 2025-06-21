"""Tests for database functionality."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from ccmonitor.database import ProcessDatabase
from ccmonitor.process import ProcessInfo


def test_database_initialization():
    """Test database initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        assert db.db_path == str(db_path)
        assert db_path.exists()


def test_save_single_process():
    """Test saving a single process."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        process = ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )

        db.save_process(process)

        # Verify process was saved
        records = db.get_recent_processes(limit=1)
        assert len(records) == 1
        assert records[0]["pid"] == 1234
        assert records[0]["name"] == "claude"


def test_save_multiple_processes():
    """Test saving multiple processes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        processes = [
            ProcessInfo(
                pid=1234,
                name="claude",
                cpu_time=10.5,
                start_time=datetime.now(),
                elapsed_time=timedelta(hours=1),
                cmdline=["claude", "--config", ".claude.json"],
            ),
            ProcessInfo(
                pid=5678,
                name="claude-helper",
                cpu_time=5.2,
                start_time=datetime.now(),
                elapsed_time=timedelta(minutes=30),
                cmdline=["claude-helper", "--daemon"],
            ),
        ]

        db.save_processes(processes)

        # Verify processes were saved
        records = db.get_recent_processes(limit=10)
        assert len(records) == 2

        pids = [r["pid"] for r in records]
        assert 1234 in pids
        assert 5678 in pids


def test_process_history():
    """Test getting process history for specific PID."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        # Save process multiple times
        process = ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )

        db.save_process(process)
        db.save_process(process)

        # Get history for PID
        history = db.get_process_history(1234)
        assert len(history) == 2
        assert all(h["pid"] == 1234 for h in history)


def test_summary_stats():
    """Test getting summary statistics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        processes = [
            ProcessInfo(
                pid=1234,
                name="claude",
                cpu_time=10.5,
                start_time=datetime.now(),
                elapsed_time=timedelta(hours=1),
                cmdline=["claude", "--config", ".claude.json"],
            ),
            ProcessInfo(
                pid=5678,
                name="claude-helper",
                cpu_time=5.2,
                start_time=datetime.now(),
                elapsed_time=timedelta(minutes=30),
                cmdline=["claude-helper", "--daemon"],
            ),
        ]

        db.save_processes(processes)

        stats = db.get_summary_stats()

        assert stats["total_records"] == 2
        assert stats["unique_processes"] == 2
        assert stats["running_processes"] == 2
        assert stats["total_cpu_time"] == 15.7  # 10.5 + 5.2


def test_cleanup_old_records():
    """Test cleaning up old records."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        # Add some test records
        process = ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )

        db.save_process(process)

        # Cleanup with 0 days (should remove all records)
        deleted_count = db.cleanup_old_records(days=0)
        # DuckDB might return -1 for rowcount, so check if > 0 or verify records are gone
        assert deleted_count != 0 or len(db.get_recent_processes(limit=10)) == 0

        # Verify records were deleted
        records = db.get_recent_processes(limit=10)
        assert len(records) == 0


def test_database_size():
    """Test getting database file size."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = ProcessDatabase(str(db_path))

        # Initially should have some size due to schema creation
        initial_size = db.get_database_size()
        assert initial_size > 0

        # Add data and verify size increases
        process = ProcessInfo(
            pid=1234,
            name="claude",
            cpu_time=10.5,
            start_time=datetime.now(),
            elapsed_time=timedelta(hours=1),
            cmdline=["claude", "--config", ".claude.json"],
        )

        db.save_process(process)

        new_size = db.get_database_size()
        assert new_size >= initial_size


def test_default_config_directory():
    """Test default configuration directory creation."""
    db = ProcessDatabase()

    config_path = Path.home() / ".config" / "ccmonitor"
    assert config_path.exists()
    assert config_path.is_dir()

    db_file = config_path / "processes.db"
    assert db.db_path == str(db_file)
