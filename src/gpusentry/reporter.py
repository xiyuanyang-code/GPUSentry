"""Module for generating comprehensive GPU usage reports."""

import os
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, List
from .database import DatabaseManager, GPUStat
from .analyzer import GPUDataAnalyzer
from .llm import LLMAnalyzer
from .utils.configs import Config
from .utils.feishu_msg import send_feishu_message, send_feishu_message_with_images
from .utils.logger import app_logger


class GPUReporter:
    """Comprehensive reporter for GPU usage data."""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        """Initialize the reporter.
        
        Args:
            db_manager: Database manager instance
            config: Configuration object
        """
        self.db_manager = db_manager
        self.analyzer = GPUDataAnalyzer(db_manager)
        self.llm_analyzer = LLMAnalyzer(config)
        self.config = config
        self.logger = app_logger
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate a daily usage report.
        
        Returns:
            Dictionary containing report data
        """
        return self._generate_report('daily')
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate a weekly usage report.
        
        Returns:
            Dictionary containing report data
        """
        return self._generate_report('weekly')
    
    def generate_monthly_report(self) -> Dict[str, Any]:
        """Generate a monthly usage report.
        
        Returns:
            Dictionary containing report data
        """
        return self._generate_report('monthly')
    
    def _generate_report(self, period: str) -> Dict[str, Any]:
        """Generate a report for the specified period.
        
        Args:
            period: Time period for the report ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary containing report data
        """
        # Get data for the specified period
        if period == 'daily':
            stats = self.analyzer.get_daily_data()
        elif period == 'weekly':
            stats = self.analyzer.get_weekly_data()
        elif period == 'monthly':
            stats = self.analyzer.get_monthly_data()
        else:
            raise ValueError(f"Invalid period: {period}")
        
        # Generate usage summary
        usage_summary = self.analyzer.generate_usage_summary(stats)
        
        # Generate charts
        utilization_chart = self.analyzer.generate_utilization_chart(stats)
        memory_chart = self.analyzer.generate_memory_chart(stats)
        
        # Generate rule-based summary
        rule_based_summary = self._generate_rule_based_summary(usage_summary, period)
        
        # Generate LLM-based summary
        llm_summary = self.llm_analyzer.generate_intelligent_summary(usage_summary, period)
        
        report = {
            'period': period,
            'stats': stats,
            'usage_summary': usage_summary,
            'utilization_chart': utilization_chart,
            'memory_chart': memory_chart,
            'rule_based_summary': rule_based_summary,
            'llm_summary': llm_summary,
            'timestamp': datetime.now()
        }
        
        self.logger.info(f"Generated {period} report with {len(stats)} data points")
        return report
    
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
            hours_spanned = usage_summary['time_range'].total_seconds() / 3600
            summary_parts.append(f"  - Data collected over {hours_spanned:.1f} hours")
            
            if hours_spanned > 20:  # If data was collected for most of the day
                if usage_summary['total_records'] / hours_spanned < 100:  # Low sample frequency per hour
                    summary_parts.append("  - Lower data collection frequency detected")
        
        return "\n".join(summary_parts)
    
    def generate_custom_report(self, n_minutes: int) -> Dict[str, Any]:
        """Generate a custom report for the last N minutes.
        
        Args:
            n_minutes: Number of minutes to look back
            
        Returns:
            Dictionary containing report data
        """
        stats = self.analyzer.get_last_n_minutes_data(n_minutes)
        
        # Generate usage summary
        usage_summary = self.analyzer.generate_usage_summary(stats)
        
        # Generate charts
        utilization_chart = self.analyzer.generate_utilization_chart(stats)
        memory_chart = self.analyzer.generate_memory_chart(stats)
        
        # Generate rule-based summary
        rule_based_summary = self.analyzer._generate_rule_based_summary(usage_summary, f"last {n_minutes} minutes")
        
        # Generate LLM-based summary
        llm_summary = self.llm_analyzer.generate_intelligent_summary(usage_summary, f"last {n_minutes} minutes")
        
        report = {
            'period': f"last {n_minutes} minutes",
            'stats': stats,
            'usage_summary': usage_summary,
            'utilization_chart': utilization_chart,
            'memory_chart': memory_chart,
            'rule_based_summary': rule_based_summary,
            'llm_summary': llm_summary,
            'timestamp': datetime.now()
        }
        
        self.logger.info(f"Generated custom report for last {n_minutes} minutes with {len(stats)} data points")
        return report
    
    def send_report_to_feishu(self, report: Dict[str, Any]) -> bool:
        """Send report to Feishu webhook.
        
        Args:
            report: Report data dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Create a summary message
        message = f"""
【GPUSentry】{report['period'].capitalize()} GPU Usage Report
        
{report['rule_based_summary']}
        
LLM Analysis:
{report['llm_summary']}
        """.strip()
        
        # Prepare images for sending
        image_list = []

        # todo: append image to the message list
        # # Add utilization chart if available
        # if report['utilization_chart']:
        #     image_list.append(report['utilization_chart'])
        
        # # Add memory chart if available
        # if report['memory_chart']:
        #     image_list.append(report['memory_chart'])
        
        # Send message with images
        success = send_feishu_message_with_images(message, image_list)
        
        return success