"""Database models and connection management for GPUSentry."""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Generator
from dataclasses import dataclass
from datetime import datetime
from .utils.logger import app_logger


@dataclass
class GPUStat:
    """Data class representing GPU statistics."""

    timestamp: datetime
    gpu_id: int
    name: str
    temperature: float
    utilization: float
    memory_used: int
    memory_total: int
    power_draw: float
    power_limit: float
    processes: str  # JSON string of running processes


class DatabaseManager:
    """Manages database connections and operations for GPU statistics."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.gpusentry/gpu_stats.db
        """
        if db_path is None:
            home_dir = os.path.expanduser("~")
            gpusentry_dir = os.path.join(home_dir, ".gpusentry")
            os.makedirs(gpusentry_dir, exist_ok=True)
            db_path = os.path.join(gpusentry_dir, "gpu_stats.db")

        self.db_path = db_path
        self.logger = app_logger
        self.logger.info(f"Initilizing db_path in {self.db_path}")
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            self.logger.info(f"Initializing database at {self.db_path}")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpu_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    gpu_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    temperature REAL,
                    utilization REAL,
                    memory_used INTEGER,
                    memory_total INTEGER,
                    power_draw REAL,
                    power_limit REAL,
                    processes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better query performance
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_gpu_stats_timestamp 
                ON gpu_stats (timestamp)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_gpu_stats_gpu_id 
                ON gpu_stats (gpu_id)
            """
            )
            self.logger.info("Database tables and indexes created successfully")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_gpu_stat(self, stat: GPUStat) -> None:
        """Insert a GPU statistics record into the database.

        Args:
            stat: GPUStat object containing the statistics to insert
        """
        with self._get_connection() as conn:
            self.logger.debug(
                f"Inserting GPU stat for GPU {stat.gpu_id} at {stat.timestamp}"
            )
            conn.execute(
                """
                INSERT INTO gpu_stats (
                    timestamp, gpu_id, name, temperature, utilization,
                    memory_used, memory_total, power_draw, power_limit, processes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    stat.timestamp,
                    stat.gpu_id,
                    stat.name,
                    stat.temperature,
                    stat.utilization,
                    stat.memory_used,
                    stat.memory_total,
                    stat.power_draw,
                    stat.power_limit,
                    stat.processes,
                ),
            )
            self.logger.debug(f"Successfully inserted GPU stat for GPU {stat.gpu_id}")

    def get_latest_stats(self, limit: int = 10) -> list[GPUStat]:
        """Retrieve the latest GPU statistics records.

        Args:
            limit: Maximum number of records to retrieve

        Returns:
            List of GPUStat objects
        """
        self.logger.debug(f"Retrieving latest {limit} GPU statistics records")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, gpu_id, name, temperature, utilization,
                       memory_used, memory_total, power_draw, power_limit, processes
                FROM gpu_stats
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            stats = []
            for row in rows:
                stat = GPUStat(
                    timestamp=datetime.fromisoformat(row[0]),
                    gpu_id=row[1],
                    name=row[2],
                    temperature=row[3],
                    utilization=row[4],
                    memory_used=row[5],
                    memory_total=row[6],
                    power_draw=row[7],
                    power_limit=row[8],
                    processes=row[9],
                )
                stats.append(stat)

            self.logger.debug(f"Retrieved {len(stats)} GPU statistics records")
            return stats

    def get_stats_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> list[GPUStat]:
        """Retrieve GPU statistics within a specific time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of GPUStat objects
        """
        self.logger.debug(f"Retrieving GPU statistics from {start_time} to {end_time}")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT *
                FROM gpu_stats
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC;
            """,
                (start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S")),
            )

            rows = cursor.fetchall()
            stats = []
            for row in rows:
                stat = GPUStat(
                    timestamp=datetime.fromisoformat(row[1]),
                    gpu_id=row[2],
                    name=row[3],
                    temperature=row[4],
                    utilization=row[5],
                    memory_used=row[6],
                    memory_total=row[7],
                    power_draw=row[8],
                    power_limit=row[9],
                    processes=row[10],
                )
                stats.append(stat)

            self.logger.debug(
                f"Retrieved {len(stats)} GPU statistics records for time range"
            )
            return stats

    def get_statistics(self) -> dict:
        """Generate basic statistics about the stored GPU data.

        Returns:
            Dictionary containing various statistics
        """
        self.logger.debug("Generating database statistics")
        with self._get_connection() as conn:
            # Count total records
            total_records = conn.execute("SELECT COUNT(*) FROM gpu_stats").fetchone()[0]

            # Get time range
            time_range_result = conn.execute(
                """
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM gpu_stats
            """
            ).fetchone()

            min_time, max_time = time_range_result
            time_range = None
            if min_time and max_time:
                min_dt = datetime.fromisoformat(min_time)
                max_dt = datetime.fromisoformat(max_time)
                time_range = max_dt - min_dt

            # Get number of unique GPUs
            unique_gpus = conn.execute(
                "SELECT COUNT(DISTINCT gpu_id) FROM gpu_stats"
            ).fetchone()[0]

            # Get average memory usage
            avg_memory = conn.execute(
                "SELECT AVG(memory_used) FROM gpu_stats"
            ).fetchone()[0]

            # Get average GPU utilization
            avg_utilization = conn.execute(
                "SELECT AVG(utilization) FROM gpu_stats"
            ).fetchone()[0]

            stats = {
                "total_records": total_records,
                "time_range": time_range,
                "unique_gpus": unique_gpus,
                "average_memory_used": round(avg_memory, 2) if avg_memory else 0,
                "average_utilization": (
                    round(avg_utilization, 2) if avg_utilization else 0
                ),
                "first_record_time": min_time,
                "last_record_time": max_time,
            }

            self.logger.debug(f"Generated statistics: {stats}")
            return stats

    def reset_database(self) -> None:
        """Clear all data from the database."""
        self.logger.info("Resetting database - clearing all GPU statistics")
        with self._get_connection() as conn:
            conn.execute("DELETE FROM gpu_stats")
            self.logger.info("Database reset completed")
