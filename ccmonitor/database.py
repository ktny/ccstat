"""Database functionality for persisting process information."""

import json
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Optional

import polars as pl

from .process import ProcessInfo


class ProcessDatabase:
    """Database manager for persisting Claude process information."""

    # Common schema for all DataFrames
    SCHEMA: ClassVar[dict[str, pl.DataType]] = {
        "pid": pl.Int64,
        "name": pl.Utf8,
        "cpu_time": pl.Float64,
        "start_time": pl.Datetime,
        "elapsed_seconds": pl.Int64,
        "cmdline": pl.Utf8,
        "cwd": pl.Utf8,
        "recorded_at": pl.Datetime,
        "status": pl.Utf8,
    }

    def __init__(self, data_path: Optional[str] = None):
        """Initialize the database.

        Args:
            data_path: Path to the JSON data file. If None, uses default location.
        """
        if data_path is None:
            # Use ~/.config/ccmonitor/processes.json as default
            config_dir = Path.home() / ".config" / "ccmonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.data_path = config_dir / "processes.json"
        else:
            self.data_path = Path(data_path)

        # Ensure the data file exists
        if not self.data_path.exists():
            self._init_data_file()

    def _init_data_file(self) -> None:
        """Initialize an empty JSON data file."""
        with self.data_path.open("w", encoding="utf-8") as f:
            json.dump([], f)

    def _load_data(self) -> pl.DataFrame:
        """Load data from JSON file into a Polars DataFrame.

        Returns:
            DataFrame containing process data.
        """
        try:
            with self.data_path.open(encoding="utf-8") as f:
                data = json.load(f)

            if not data:
                # Return empty DataFrame with proper schema
                return pl.DataFrame(schema=self.SCHEMA)

            # Convert JSON data to DataFrame
            df = pl.DataFrame(data)

            # Convert datetime strings back to datetime objects
            if "start_time" in df.columns:
                df = df.with_columns(pl.col("start_time").str.to_datetime())
            if "recorded_at" in df.columns:
                df = df.with_columns(pl.col("recorded_at").str.to_datetime())

            return df

        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty DataFrame if file is corrupted or missing
            return pl.DataFrame(schema=self.SCHEMA)

    def _save_data(self, df: pl.DataFrame) -> None:
        """Save DataFrame to JSON file.

        Args:
            df: DataFrame to save.
        """
        # Convert DataFrame to list of dictionaries for JSON serialization
        data = df.to_dicts()

        # Convert datetime objects to ISO format strings
        for record in data:
            if "start_time" in record and record["start_time"] is not None:
                record["start_time"] = record["start_time"].isoformat()
            if "recorded_at" in record and record["recorded_at"] is not None:
                record["recorded_at"] = record["recorded_at"].isoformat()

        with self.data_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def save_processes(self, processes: list[ProcessInfo]) -> None:
        """Save multiple processes to the database.

        Args:
            processes: List of ProcessInfo objects to save
        """
        if not processes:
            return

        # Load existing data
        df = self._load_data()

        # Mark currently running processes as terminated if they're not in the new list
        current_pids = [p.pid for p in processes]
        if not df.is_empty():
            df = df.with_columns(
                pl.when(
                    (pl.col("status") == "running")
                    & (~pl.col("pid").is_in(current_pids))
                )
                .then(pl.lit("terminated"))
                .otherwise(pl.col("status"))
                .alias("status")
            )

        # Create new records
        current_time = datetime.now()
        new_records = []
        for process in processes:
            new_records.append(
                {
                    "pid": process.pid,
                    "name": process.name,
                    "cpu_time": process.cpu_time,
                    "start_time": process.start_time,
                    "elapsed_seconds": int(process.elapsed_time.total_seconds()),
                    "cmdline": " ".join(process.cmdline),
                    "cwd": process.cwd,
                    "recorded_at": current_time,
                    "status": "running",
                }
            )

        # Add new records to DataFrame
        if new_records:
            new_df = pl.DataFrame(new_records)
            df = pl.concat([df, new_df], how="vertical")

        # Save updated data
        self._save_data(df)




