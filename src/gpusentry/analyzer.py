"""Module for analyzing GPU usage data and generating reports."""

import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .database import DatabaseManager, GPUStat
from .utils.logger import app_logger


class GPUDataAnalyzer:
    """Analyzer for GPU usage data."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the analyzer.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = app_logger
    
    def get_daily_data(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU data for a specific day.
        
        Args:
            date: Date to get data for (defaults to today)
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        return self.db_manager.get_stats_by_time_range(start_time, end_time)
    
    def get_weekly_data(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU data for a specific week.
        
        Args:
            date: Date to get data for (defaults to today)
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        # Get start of week (Monday)
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=date.weekday())
        end_time = start_time + timedelta(weeks=1)
        
        return self.db_manager.get_stats_by_time_range(start_time, end_time)
    
    def get_monthly_data(self, date: datetime = None) -> List[GPUStat]:
        """Get GPU data for a specific month.
        
        Args:
            date: Date to get data for (defaults to today)
            
        Returns:
            List of GPUStat objects
        """
        if date is None:
            date = datetime.now()
        
        # Get start of month
        start_time = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if date.month == 12:
            end_time = start_time.replace(year=start_time.year + 1, month=1)
        else:
            end_time = start_time.replace(month=start_time.month + 1)
        
        return self.db_manager.get_stats_by_time_range(start_time, end_time)

    def get_last_n_minutes_data(self, n_minutes: int) -> List[GPUStat]:
        """Get GPU data for the last N minutes.
        
        Args:
            n_minutes: Number of minutes to look back
            
        Returns:
            List of GPUStat objects
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=n_minutes)
        self.logger.info(f"Start time: {start_time}")
        self.logger.info(f"End time: {end_time}")
        
        return self.db_manager.get_stats_by_time_range(start_time, end_time)

    def generate_custom_report(self, stats: List[GPUStat], period_desc: str = "custom") -> Dict[str, Any]:
        """Generate a custom report for a specific period of data.
        
        Args:
            stats: List of GPUStat objects
            period_desc: Description of the period (for display purposes)
            
        Returns:
            Dictionary containing report data
        """
        # Generate usage summary
        usage_summary = self.generate_usage_summary(stats)
        
        # Generate charts
        utilization_chart = self.generate_utilization_chart(stats)
        memory_chart = self.generate_memory_chart(stats)
        
        # Generate rule-based summary
        rule_based_summary = self._generate_rule_based_summary(usage_summary, period_desc)
        
        return {
            'period': period_desc,
            'stats': stats,
            'usage_summary': usage_summary,
            'utilization_chart': utilization_chart,
            'memory_chart': memory_chart,
            'rule_based_summary': rule_based_summary,
            'timestamp': datetime.now()
        }

    def _generate_rule_based_summary(self, usage_summary: Dict[str, Any], period: str) -> str:
        """Generate a rule-based summary of GPU usage.
        
        Args:
            usage_summary: Dictionary containing usage statistics
            period: Time period for the summary
            
        Returns:
            Rule-based summary text
        """
        summary_parts = []
        
        # Add basic stats
        summary_parts.append(f"GPU Usage Summary for {period.capitalize()} Period:")
        summary_parts.append(f"  - Total records: {usage_summary['total_records']}")
        summary_parts.append(f"  - Unique GPUs: {usage_summary['unique_gpus']}")
        summary_parts.append(f"  - Average memory used: {usage_summary['average_memory_used']} MB")
        summary_parts.append(f"  - Average utilization: {usage_summary['average_utilization']}%")
        summary_parts.append(f"  - Peak memory used: {usage_summary['peak_memory_used']} MB")
        summary_parts.append(f"  - Peak utilization: {usage_summary['peak_utilization']}%")
        
        # Add insights based on thresholds
        if usage_summary['average_utilization'] > 80:
            summary_parts.append("  - High GPU utilization detected - systems are heavily loaded")
        elif usage_summary['average_utilization'] < 20:
            summary_parts.append("  - Low GPU utilization detected - possible underutilization")
            
        if usage_summary['average_memory_used'] > 0.8 * 8192:  # Assuming 8GB as reference
            summary_parts.append("  - High memory usage detected - consider memory optimization")
            
        # Add time-based insights
        if usage_summary['time_range']:
            if 'minutes' in period:
                # For minute-based reports
                minutes_spanned = usage_summary['time_range'].total_seconds() / 60
                summary_parts.append(f"  - Data collected over {minutes_spanned:.1f} minutes")
            else:
                # For other periods (hours, days, etc.)
                hours_spanned = usage_summary['time_range'].total_seconds() / 3600
                summary_parts.append(f"  - Data collected over {hours_spanned:.1f} hours")
        
        return "\n".join(summary_parts)
    
    def generate_usage_summary(self, stats: List[GPUStat]) -> Dict[str, Any]:
        """Generate a summary of GPU usage from stats.
        
        Args:
            stats: List of GPUStat objects
            
        Returns:
            Dictionary containing usage summary
        """
        if not stats:
            return {
                'total_records': 0,
                'time_range': None,
                'unique_gpus': 0,
                'average_memory_used': 0,
                'average_utilization': 0,
                'peak_memory_used': 0,
                'peak_utilization': 0
            }
        
        # Get time range
        timestamps = [stat.timestamp for stat in stats]
        min_time, max_time = min(timestamps), max(timestamps)
        time_range = max_time - min_time
        
        # Get unique GPUs
        gpu_ids = set(stat.gpu_id for stat in stats)
        
        # Calculate averages
        avg_memory = sum(stat.memory_used for stat in stats) / len(stats)
        avg_utilization = sum(stat.utilization for stat in stats) / len(stats)
        
        # Calculate peaks
        peak_memory = max(stat.memory_used for stat in stats)
        peak_utilization = max(stat.utilization for stat in stats)
        
        return {
            'total_records': len(stats),
            'time_range': time_range,
            'unique_gpus': len(gpu_ids),
            'average_memory_used': round(avg_memory, 2),
            'average_utilization': round(avg_utilization, 2),
            'peak_memory_used': peak_memory,
            'peak_utilization': peak_utilization
        }
    
    def generate_utilization_chart(self, stats: List[GPUStat]) -> str:
        """Generate a utilization chart as base64 encoded image.
        
        Args:
            stats: List of GPUStat objects
            
        Returns:
            Base64 encoded image string
        """
        if not stats:
            return ""
        
        # Group stats by GPU ID
        gpu_stats = {}
        for stat in stats:
            if stat.gpu_id not in gpu_stats:
                gpu_stats[stat.gpu_id] = []
            gpu_stats[stat.gpu_id].append(stat)
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        for gpu_id, gpu_data in gpu_stats.items():
            timestamps = [stat.timestamp for stat in gpu_data]
            utilization = [stat.utilization for stat in gpu_data]
            plt.plot(timestamps, utilization, label=f'GPU {gpu_id}', marker='o', markersize=2)
        
        plt.xlabel('Time')
        plt.ylabel('Utilization (%)')
        plt.title('GPU Utilization Over Time')
        plt.legend()
        plt.grid(True)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()
        
        return image_base64
    
    def generate_memory_chart(self, stats: List[GPUStat]) -> str:
        """Generate a memory usage chart as base64 encoded image.
        
        Args:
            stats: List of GPUStat objects
            
        Returns:
            Base64 encoded image string
        """
        if not stats:
            return ""
        
        # Group stats by GPU ID
        gpu_stats = {}
        for stat in stats:
            if stat.gpu_id not in gpu_stats:
                gpu_stats[stat.gpu_id] = []
            gpu_stats[stat.gpu_id].append(stat)
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        for gpu_id, gpu_data in gpu_stats.items():
            timestamps = [stat.timestamp for stat in gpu_data]
            memory_used = [stat.memory_used for stat in gpu_data]
            plt.plot(timestamps, memory_used, label=f'GPU {gpu_id}', marker='o', markersize=2)
        
        plt.xlabel('Time')
        plt.ylabel('Memory Used (MB)')
        plt.title('GPU Memory Usage Over Time')
        plt.legend()
        plt.grid(True)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()
        
        return image_base64