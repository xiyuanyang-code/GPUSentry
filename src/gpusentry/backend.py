'''Module for backend monitoring services.'''
import time
import subprocess
import threading
import json
import schedule
from typing import Optional
from datetime import datetime
from .database import DatabaseManager, GPUStat
from .reporter import GPUReporter
from .utils.logger import app_logger
from .utils.configs import Config


class BackendMonitor:
    '''Backend service for continuous GPU monitoring and data collection.'''
    
    def __init__(self, interval: int = 5, config: Optional[Config] = None):
        '''Initialize backend monitor.
        
        Args:
            interval: Data collection interval in seconds (default: 5)
            config: Configuration object (optional, will use defaults if not provided)
        '''
        self.config = config or Config()
        # Use config value if interval is not provided or use the provided interval
        self.interval = interval if interval != 5 or config is None else self.config.monitoring_interval
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.db_manager = DatabaseManager(db_path=self.config.database_path)
        self.reporter = GPUReporter(self.db_manager, self.config)
        self.logger = app_logger

    def start(self):
        '''Start the backend monitoring service.'''
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        
        # Start scheduler thread for periodic reports
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.start()
        
        # Schedule daily, weekly, and monthly reports
        self._schedule_reports()
        
        self.logger.info('Backend monitoring service started...')

    def stop(self):
        '''Stop the backend monitoring service.'''
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.logger.info('Backend monitoring service stopped.')

    def _monitor_loop(self):
        '''Main monitoring loop.'''
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
                
                self.logger.info(f'Collected GPU data for {len(gpu_data['gpus'])} GPUs')
                self.logger.debug(f'{json.dumps(gpu_data,indent=2,ensure_ascii=False)}')
                time.sleep(self.interval)
            except subprocess.CalledProcessError as e:
                self.logger.error(f'Error collecting GPU stats: {e}')
                time.sleep(self.interval)
            except json.JSONDecodeError as e:
                self.logger.error(f'Error parsing GPU stats JSON: {e}')
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f'Unexpected error in monitoring loop: {e}')
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break

    def _scheduler_loop(self):
        '''Scheduler loop for periodic tasks.'''
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'Error in scheduler loop: {e}')
                time.sleep(1)

    def _schedule_reports(self):
        '''Schedule daily, weekly, and monthly reports.'''
        # Schedule daily report
        daily_time = self.config.daily_time
        schedule.every().day.at(daily_time).do(self._generate_and_send_daily_report)
        self.logger.info(f'Scheduled daily report at {daily_time}')

        # Schedule weekly report (Sunday at 23:30 by default)
        weekly_day = self.config.weekly_day  # 0 = Sunday, 1 = Monday, etc.
        weekly_time = "23:30"  # Fixed time for weekly reports
        days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        if 0 <= weekly_day <= 6:
            getattr(schedule.every(), days[weekly_day]).at(weekly_time).do(self._generate_and_send_weekly_report)
            self.logger.info(f'Scheduled weekly report on {days[weekly_day]} at {weekly_time}')

        # Schedule monthly report (last day of month at 23:45 by default)
        monthly_time = "23:45"  # Fixed time for monthly reports
        schedule.every().day.at(monthly_time).do(self._check_and_generate_monthly_report)
        self.logger.info(f'Scheduled monthly report check at {monthly_time} daily')

    def _generate_and_send_daily_report(self):
        '''Generate and send daily report.'''
        try:
            self.logger.info('Generating daily report...')
            report = self.reporter.generate_daily_report()
            self.reporter.send_report_to_feishu(report)
            self.logger.info('Daily report sent successfully')
        except Exception as e:
            self.logger.error(f'Error generating or sending daily report: {e}')

    def _generate_and_send_weekly_report(self):
        '''Generate and send weekly report.'''
        try:
            self.logger.info('Generating weekly report...')
            report = self.reporter.generate_weekly_report()
            self.reporter.send_report_to_feishu(report)
            self.logger.info('Weekly report sent successfully')
        except Exception as e:
            self.logger.error(f'Error generating or sending weekly report: {e}')

    def _check_and_generate_monthly_report(self):
        '''Check if it's time to generate monthly report based on config.'''
        try:
            from datetime import date, datetime
            today = date.today()
            monthly_day = self.config.monthly_day
            
            should_generate = False
            if monthly_day == -1:
                # Last day of month
                if (today.month == 12 and today.day == 31) or \
                   (today.month < 12 and today.replace(day=1, month=today.month+1) - today).days == 1:
                    should_generate = True
            elif 1 <= monthly_day <= 31:
                # Specific day of month
                if today.day == monthly_day:
                    should_generate = True
            
            if should_generate:
                self.logger.info('Generating monthly report...')
                report = self.reporter.generate_monthly_report()
                self.reporter.send_report_to_feishu(report)
                self.logger.info('Monthly report sent successfully')
        except Exception as e:
            self.logger.error(f'Error generating or sending monthly report: {e}')


def run_backend():
    '''Run the backend monitoring service.'''
    config = Config()
    monitor = BackendMonitor(config=config)
    try:
        monitor.start()
        # Keep the main thread alive
        while monitor.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nReceived interrupt signal, stopping backend service...')
        monitor.stop()

