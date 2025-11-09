"""Module for backend monitoring services."""
import time
import subprocess
import threading
import json
import logging
from typing import Optional
from datetime import datetime
from .database import DatabaseManager, GPUStat
from .logger import app_logger

class BackendMonitor:
    """Backend service for continuous GPU monitoring and data collection."""
    
    def __init__(self, interval: int = 5):
        """Initialize backend monitor.
        
        Args:
            interval: Data collection interval in seconds (default: 5)
        """
        self.interval = interval
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.db_manager = DatabaseManager()
        self.logger = app_logger

    def start(self):
        """Start the backend monitoring service."""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        self.logger.info("Backend monitoring service started...")

    def stop(self):
        """Stop the backend monitoring service."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Backend monitoring service stopped.")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect GPU stats using gpustat
                result = subprocess.run(['gpustat', '--json'], 
                                      capture_output=True, text=True, check=True)
                gpu_data = json.loads(result.stdout)
                time_stamp = datetime.fromisoformat(gpu_data['query_time'])
                
                # Process and store GPU statistics
                for gpu in gpu_data['gpus']:
                    stat = GPUStat(
                        timestamp=time_stamp,
                        gpu_id=gpu['index'],
                        name=gpu['name'],
                        temperature=gpu['temperature.gpu'],
                        utilization=gpu['utilization.gpu'],
                        memory_used=gpu['memory.used'],
                        memory_total=gpu['memory.total'],
                        power_draw=gpu['power.draw'],
                        power_limit=gpu['enforced.power.limit'],
                        processes=json.dumps(gpu['processes']) if gpu['processes'] else '[]'
                    )
                    self.db_manager.insert_gpu_stat(stat)
                
                self.logger.info(f"Collected GPU data for {len(gpu_data['gpus'])} GPUs")
                self.logger.debug(f"{json.dumps(gpu_data,indent=2,ensure_ascii=False)}")
                time.sleep(self.interval)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error collecting GPU stats: {e}")
                time.sleep(self.interval)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing GPU stats JSON: {e}")
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break


def run_backend():
    """Run the backend monitoring service."""
    monitor = BackendMonitor()
    try:
        monitor.start()
        # Keep the main thread alive
        while monitor.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, stopping backend service...")
        monitor.stop()

