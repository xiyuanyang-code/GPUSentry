import os
import yaml
from typing import Dict, Any, Optional


class Config:
    """Configuration management class for GPUSentry."""
    
    def __init__(self, config_file_path: str = "./config.yaml"):
        """Initialize the Config class.
        
        Args:
            config_file_path: Path to the configuration file
        """
        self.config_file_path = config_file_path
        self.config_data: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        # First check if the config file exists, if not, try the example config
        config_path = self.config_file_path
        if not os.path.exists(config_path):
            example_path = "./config.example.yaml"
            if os.path.exists(example_path):
                config_path = example_path
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config_data = yaml.safe_load(file) or {}
        except FileNotFoundError:
            # If no config file exists, create a default config
            print("Error! No config files found")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration file: {e}")
    
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'monitoring.interval').
        
        Args:
            key: Configuration key using dot notation
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    # * property settings
    @property
    def feishu_keyword(self) -> str:
        """Get Feishu keyword."""
        return self.get("feishu.keyword", "GPUSentry")
    
    @property
    def feishu_webhook_url(self) -> str:
        """Get Feishu webhook URL."""
        return self.get("feishu.webhook_url", "")
    
    @property
    def monitoring_interval(self) -> int:
        """Get monitoring interval."""
        return self.get("monitoring.interval", 5)
    
    @property
    def enable_logging(self) -> bool:
        """Get enable logging flag."""
        return self.get("monitoring.enable_logging", True)
    
    @property
    def database_path(self) -> str:
        """Get database path."""
        return self.get("logging.database_path", "gpusentry.db")
    
    @property
    def retention_days(self) -> int:
        """Get log retention days."""
        return self.get("logging.retention_days", 30)
    
    @property
    def daily_time(self) -> str:
        """Get daily report time."""
        return self.get("reporting.daily_time", "23:59")
    
    @property
    def weekly_day(self) -> int:
        """Get weekly report day."""
        return self.get("reporting.weekly_day", 0)
    
    @property
    def monthly_day(self) -> int:
        """Get monthly report day."""
        return self.get("reporting.monthly_day", 1)