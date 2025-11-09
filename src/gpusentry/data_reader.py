"""Module for reading and analyzing GPU statistics data."""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .database import DatabaseManager, GPUStat
from .utils.logger import app_logger

class DataReader:
    """Class for reading and analyzing GPU statistics data."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize data reader.
        
        Args:
            db_manager: Database manager instance. If None, creates a new one.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.logger = app_logger
    
    def get_latest_stats(self, limit: int = 10) -> List[GPUStat]:
        """Get the latest GPU statistics records.
        
        Args:
            limit: Maximum number of records to retrieve
            
        Returns:
            List of GPUStat objects
        """
        self.logger.info(f"Retrieving latest {limit} GPU statistics records")
        return self.db_manager.get_latest_stats(limit)
    
    def get_stats_by_time_range(self, start_time: datetime, end_time: datetime) -> List[GPUStat]:
        """Get GPU statistics within a specific time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of GPUStat objects
        """
        self.logger.info(f"Retrieving GPU statistics from {start_time} to {end_time}")
        return self.db_manager.get_stats_by_time_range(start_time, end_time)
    
    def get_daily_stats(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU statistics for a specific day.
        
        Args:
            date: Date to retrieve stats for. If None, uses today.
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        start_time = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_time = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        self.logger.info(f"Retrieving GPU statistics for {date.date()}")
        return self.get_stats_by_time_range(start_time, end_time)
    
    def get_weekly_stats(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU statistics for a specific week.
        
        Args:
            date: Date to retrieve stats for. If None, uses current week.
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        # Calculate start of week (Monday)
        start_of_week = date - timedelta(days=date.weekday())
        start_time = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0)
        end_time = start_time + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        self.logger.info(f"Retrieving GPU statistics for week starting {start_time.date()}")
        return self.get_stats_by_time_range(start_time, end_time)
    
    def get_monthly_stats(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU statistics for a specific month.
        
        Args:
            date: Date to retrieve stats for. If None, uses current month.
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        # Calculate start and end of month
        start_time = datetime(date.year, date.month, 1, 0, 0, 0)
        
        # Calculate end of month
        if date.month == 12:
            end_time = datetime(date.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            end_time = datetime(date.year, date.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        self.logger.info(f"Retrieving GPU statistics for {start_time.strftime('%Y-%m')}")
        return self.get_stats_by_time_range(start_time, end_time)
    
    def get_gpu_utilization_summary(self, stats: List[GPUStat]) -> Dict[str, Any]:
        """Generate a summary of GPU utilization from stats.
        
        Args:
            stats: List of GPUStat objects
            
        Returns:
            Dictionary with utilization summary
        """
        if not stats:
            return {}
        
        # Group stats by GPU ID
        gpu_stats = {}
        for stat in stats:
            if stat.gpu_id not in gpu_stats:
                gpu_stats[stat.gpu_id] = []
            gpu_stats[stat.gpu_id].append(stat)
        
        summary = {}
        for gpu_id, gpu_data in gpu_stats.items():
            utilizations = [stat.utilization for stat in gpu_data if stat.utilization is not None]
            memory_usages = [stat.memory_used for stat in gpu_data if stat.memory_used is not None]
            
            summary[gpu_id] = {
                'gpu_id': gpu_id,
                'name': gpu_data[0].name if gpu_data else 'Unknown',
                'avg_utilization': sum(utilizations) / len(utilizations) if utilizations else 0,
                'max_utilization': max(utilizations) if utilizations else 0,
                'min_utilization': min(utilizations) if utilizations else 0,
                'avg_memory_usage': sum(memory_usages) / len(memory_usages) if memory_usages else 0,
                'max_memory_usage': max(memory_usages) if memory_usages else 0,
                'min_memory_usage': min(memory_usages) if memory_usages else 0,
                'sample_count': len(gpu_data)
            }
        
        self.logger.info(f"Generated utilization summary for {len(summary)} GPUs")
        self.logger.debug(f"{json.dumps(summary[gpu_id],indent=2,ensure_ascii=False)}")
        return summary