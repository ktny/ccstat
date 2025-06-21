"""Tests for database functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from ccmonitor.database import ProcessDatabase
from ccmonitor.process import ProcessInfo


def test_database_initialization():
    """Test database initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
        db = ProcessDatabase(str(db_path))

        assert db.data_path == db_path
        assert db_path.exists()

        # Check that it creates an empty JSON array
        with db_path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data == []


def test_save_single_process():
    """Test saving a single process."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
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
        stats = db.get_summary_stats()
        assert stats["total_records"] == 1
        assert stats["unique_processes"] == 1


def test_save_multiple_processes():
    """Test saving multiple processes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
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
        stats = db.get_summary_stats()
        assert stats["total_records"] == 2
        assert stats["unique_processes"] == 2


def test_summary_stats():
    """Test getting summary statistics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
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
        db_path = Path(temp_dir) / "test.json"
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
        assert deleted_count > 0

        # Verify records were deleted
        stats = db.get_summary_stats()
        assert stats["total_records"] == 0


def test_database_size():
    """Test getting database file size."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
        db = ProcessDatabase(str(db_path))

        # Initially should have minimal size for empty JSON array
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
        assert new_size > initial_size


def test_default_config_directory():
    """Test default configuration directory creation."""
    db = ProcessDatabase()

    config_path = Path.home() / ".config" / "ccmonitor"
    assert config_path.exists()
    assert config_path.is_dir()

    db_file = config_path / "processes.json"
    assert db.data_path == db_file


def test_empty_data_handling():
    """Test handling of empty data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
        db = ProcessDatabase(str(db_path))

        # Test with no data

        stats = db.get_summary_stats()
        assert stats["total_records"] == 0
        assert stats["unique_processes"] == 0
        assert stats["running_processes"] == 0
        assert stats["total_cpu_time"] == 0.0
        assert stats["oldest_record"] is None
        assert stats["newest_record"] is None


def test_process_termination_marking():
    """Test that processes not in new list are marked as terminated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"
        db = ProcessDatabase(str(db_path))

        # Save initial processes
        initial_processes = [
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
        db.save_processes(initial_processes)

        # Save new processes (only one of the original)
        new_processes = [initial_processes[0]]  # Only keep first process
        db.save_processes(new_processes)

        # Check that the stats reflect the termination
        stats = db.get_summary_stats()
        # Should have records from both processes
        assert stats["total_records"] >= 2
        # But only one running process
        assert stats["running_processes"] == 1


def test_corrupted_json_handling():
    """Test handling of corrupted JSON file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"

        # Create a corrupted JSON file
        with db_path.open("w", encoding="utf-8") as f:
            f.write("invalid json content")

        # Database should handle corruption gracefully
        db = ProcessDatabase(str(db_path))

        # Should return empty results for corrupted data
        stats = db.get_summary_stats()
        assert stats["total_records"] == 0
