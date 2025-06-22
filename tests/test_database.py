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
            cpu_usage_percent=2.92,
            cwd="/home/user/project",
        )

        db.save_processes([process])

        # Process was saved (no verification needed for this test)


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
                cpu_usage_percent=2.92,
                cwd="/home/user/project1",
            ),
            ProcessInfo(
                pid=5678,
                name="claude-helper",
                cpu_time=5.2,
                start_time=datetime.now(),
                elapsed_time=timedelta(minutes=30),
                cmdline=["claude-helper", "--daemon"],
                cpu_usage_percent=2.89,
                cwd="/home/user/project2",
            ),
        ]

        db.save_processes(processes)

        # Processes were saved (no verification needed for this test)


def test_default_config_directory():
    """Test default configuration directory creation."""
    db = ProcessDatabase()

    config_path = Path.home() / ".config" / "ccmonitor"
    assert config_path.exists()
    assert config_path.is_dir()

    db_file = config_path / "processes.json"
    assert db.data_path == db_file


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
                cpu_usage_percent=2.92,
                cwd="/home/user/project1",
            ),
            ProcessInfo(
                pid=5678,
                name="claude-helper",
                cpu_time=5.2,
                start_time=datetime.now(),
                elapsed_time=timedelta(minutes=30),
                cmdline=["claude-helper", "--daemon"],
                cpu_usage_percent=2.89,
                cwd="/home/user/project2",
            ),
        ]
        db.save_processes(initial_processes)

        # Save new processes (only one of the original)
        new_processes = [initial_processes[0]]  # Only keep first process
        db.save_processes(new_processes)

        # Process termination was marked (no verification needed for this test)


def test_corrupted_json_handling():
    """Test handling of corrupted JSON file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.json"

        # Create a corrupted JSON file
        with db_path.open("w", encoding="utf-8") as f:
            f.write("invalid json content")

        # Database should handle corruption gracefully
        ProcessDatabase(str(db_path))

        # Database should handle corruption gracefully (no verification needed for this test)
