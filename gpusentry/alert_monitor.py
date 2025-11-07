import time
import threading
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from .gpu_monitor import GPUStats
from .db_manager import UsageSummary
from .feishu_message import send_feishu_message, load_config

class GPUAlertMonitor:
    """GPU预警监控类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.alert_config = self.config.get('alerting', {})
        self.gpu_stats = GPUStats()
        self.db_manager = UsageSummary()
        self.is_monitoring = False
        self.logger = logging.getLogger(__name__)
        
        # 初始化阈值
        self.gpu_memory_threshold = self.alert_config.get('gpu_memory_threshold', 0.9)
        self.gpu_utilization_threshold = self.alert_config.get('gpu_utilization_threshold', 0.95)
        self.temperature_threshold = self.alert_config.get('temperature_threshold', 80)
    
    def check_gpu_alerts(self) -> List[str]:
        """检查GPU是否触发预警"""
        alerts = []
        gpu_stats = self.gpu_stats.get_gpu_stats()
        
        if not gpu_stats:
            return ["无法获取GPU状态信息"]
        
        for gpu in gpu_stats:
            # 检查温度预警
            if gpu['temperature'] > self.temperature_threshold:
                alerts.append(f"⚠️ GPU {gpu['index']} 温度过高: {gpu['temperature']}°C (阈值: {self.temperature_threshold}°C)")
            
            # 检查GPU利用率预警
            if gpu['utilization'] / 100 > self.gpu_utilization_threshold:
                alerts.append(f"⚠️ GPU {gpu['index']} 利用率过高: {gpu['utilization']}% (阈值: {self.gpu_utilization_threshold * 100}%)")
            
            # 检查显存使用率预警
            memory_utilization = (gpu['memory_used'] / gpu['memory_total']) if gpu['memory_total'] > 0 else 0
            if memory_utilization > self.gpu_memory_threshold:
                alerts.append(f"⚠️ GPU {gpu['index']} 显存使用率过高: {memory_utilization * 100:.1f}% (阈值: {self.gpu_memory_threshold * 100}%)")
        
        return alerts
    
    def send_alerts(self, alerts: List[str]) -> bool:
        """发送预警信息到飞书"""
        if not alerts:
            return True
        
        alert_message = "🚨 GPUSentry 预警信息 🚨\n\n"
        alert_message += "\n".join(alerts)
        
        return send_feishu_message(alert_message)
    
    def start_monitoring(self, interval: int = 5):
        """开始监控"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # 检查预警
                alerts = self.check_gpu_alerts()
                if alerts:
                    success = self.send_alerts(alerts)
                    if success:
                        self.logger.info(f"成功发送 {len(alerts)} 条预警信息")
                    else:
                        self.logger.error("发送预警信息失败")
                
                # 获取并保存统计信息
                gpu_stats = self.gpu_stats.get_gpu_stats()
                system_stats = self.gpu_stats.get_system_stats()
                
                if gpu_stats:
                    self.db_manager.save_gpu_stats(gpu_stats, system_stats)
                
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"监控过程中出错: {e}")
                time.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False


class ReportScheduler:
    """报告调度器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.db_manager = UsageSummary()
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
    def generate_and_send_report(self, report_type: str):
        """生成并发送报告"""
        try:
            if report_type == "daily":
                date = datetime.now() - timedelta(days=1)  # 昨天的数据
                report = self.db_manager.generate_summary_report("daily", date)
            elif report_type == "weekly":
                # 获取上周的数据
                date = datetime.now() - timedelta(days=7)
                report = self.db_manager.generate_summary_report("weekly", date)
            elif report_type == "monthly":
                # 获取上个月的数据
                date = datetime.now() - timedelta(days=30)
                report = self.db_manager.generate_summary_report("monthly", date)
            else:
                self.logger.error(f"未知的报告类型: {report_type}")
                return False
            
            # 发送报告到飞书
            success = send_feishu_message(f"📋 {report}")
            if success:
                self.logger.info(f"成功发送{report_type}报告")
                return True
            else:
                self.logger.error(f"发送{report_type}报告失败")
                return False
        except Exception as e:
            self.logger.error(f"生成{report_type}报告时出错: {e}")
            return False
    
    def start_scheduler(self):
        """启动报告调度器"""
        self.is_running = True
        
        while self.is_running:
            now = datetime.now()
            
            # 检查是否需要发送每日报告
            daily_time = self.config.get('reporting', {}).get('daily_time', '23:59')
            daily_hour, daily_minute = map(int, daily_time.split(':'))
            if now.hour == daily_hour and now.minute == daily_minute:
                self.generate_and_send_report("daily")
                time.sleep(60)  # 等待一分钟以避免重复发送
            
            # 检查是否需要发送每周报告
            weekly_day = self.config.get('reporting', {}).get('weekly_day', 0)  # 0=周日
            if now.weekday() == weekly_day and now.hour == 0 and now.minute == 0:
                self.generate_and_send_report("weekly")
                time.sleep(60)  # 等待一分钟以避免重复发送
            
            # 检查是否需要发送每月报告
            monthly_day = self.config.get('reporting', {}).get('monthly_day', 1)
            if now.day == monthly_day and now.hour == 0 and now.minute == 0:
                self.generate_and_send_report("monthly")
                time.sleep(60)  # 等待一分钟以避免重复发送
            
            time.sleep(30)  # 每30秒检查一次
    
    def stop_scheduler(self):
        """停止报告调度器"""
        self.is_running = False


def main():
    """主函数，启动监控和报告调度"""
    print("GPUSentry - 启动监控和报告服务")
    
    # 启动预警监控
    alert_monitor = GPUAlertMonitor()
    alert_thread = threading.Thread(target=alert_monitor.start_monitoring, args=(5,))
    alert_thread.daemon = True
    alert_thread.start()
    
    # 启动报告调度器
    report_scheduler = ReportScheduler()
    report_thread = threading.Thread(target=report_scheduler.start_scheduler)
    report_thread.daemon = True
    report_thread.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止GPUSentry服务...")
        alert_monitor.stop_monitoring()
        report_scheduler.stop_scheduler()
        print("GPUSentry服务已停止")


if __name__ == "__main__":
    main()