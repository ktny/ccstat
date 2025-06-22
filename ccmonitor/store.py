"""Store functionality for persisting process information."""

import csv
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from .process import ProcessInfo


class ProcessStore:
    """Store manager for persisting Claude process information."""

    # CSV column headers
    HEADERS: ClassVar[list[str]] = [
        "pid",
        "name",
        "cpu_time",
        "start_time",
        "cwd",
        "recorded_at",
        "status",
    ]

    def __init__(self, data_path: str | None = None):
        """Initialize the store.

        Args:
            data_path: Path to the CSV data file. If None, uses default location.
        """
        if data_path is None:
            # Use ~/.config/ccmonitor/processes.csv as default
            config_dir = Path.home() / ".config" / "ccmonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.data_path = config_dir / "processes.csv"
        else:
            self.data_path = Path(data_path)

        # Ensure the data file exists with headers
        if not self.data_path.exists():
            self._init_data_file()

    def _init_data_file(self) -> None:
        """Initialize an empty CSV data file with headers."""
        with self.data_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

    def _load_data(self) -> list[dict[str, str]]:
        """Load data from CSV file.

        Returns:
            List of dictionaries representing process data.
        """
        try:
            with self.data_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except (FileNotFoundError, csv.Error):
            # Return empty list if file is corrupted or missing
            return []

    def _save_data(self, data: list[dict[str, str]]) -> None:
        """Save data to CSV file.

        Args:
            data: List of dictionaries to save.
        """
        with self.data_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            writer.writeheader()
            writer.writerows(data)

    def save_processes(self, processes: list[ProcessInfo]) -> None:
        """Save multiple processes to the store.

        Args:
            processes: List of ProcessInfo objects to save
        """
        if not processes:
            return

        # Load existing data
        existing_data = self._load_data()

        # Mark currently running processes as terminated if they're not in the new list
        current_pids = {str(p.pid) for p in processes}
        for record in existing_data:
            if record.get("status") == "running" and record.get("pid") not in current_pids:
                record["status"] = "terminated"

        # Create new records
        current_time = datetime.now().isoformat()
        new_records = []
        for process in processes:
            new_records.append(
                {
                    "pid": str(process.pid),
                    "name": process.name,
                    "cpu_time": str(process.cpu_time),
                    "start_time": process.start_time.isoformat(),
                    "cwd": process.cwd,
                    "recorded_at": current_time,
                    "status": "running",
                }
            )

        # Combine existing and new data
        all_data = existing_data + new_records

        # Save updated data
        self._save_data(all_data)
