import argparse
import time
import threading
from datetime import datetime
from .gpu_monitor import GPUStats, main as gpu_monitor_main
from .alert_monitor import GPUAlertMonitor, ReportScheduler
from .db_manager import UsageSummary
import logging
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='GPUSentry - GPU监控和智能报告系统')
    parser.add_argument('--mode', choices=['monitor', 'stats', 'report', 'daemon'], 
                        default='monitor', 
                        help='运行模式: monitor(实时监控), stats(查看统计), report(生成报告), daemon(后台守护)')
    parser.add_argument('--report-type', choices=['daily', 'weekly', 'monthly'], 
                        help='报告类型，仅在stats模式下使用')
    parser.add_argument('--date', help='指定日期，格式: YYYY-MM-DD，仅在stats模式下使用')
    parser.add_argument('--cleanup-days', type=int, default=30, 
                        help='清理旧记录的天数，仅在stats模式下使用')
    
    args = parser.parse_args()
    
    if args.mode == 'monitor':
        # 实时监控模式 - 显示当前GPU状态
        gpu_monitor_main()
    elif args.mode == 'daemon':
        # 守护进程模式 - 后台运行监控和报告
        print("GPUSentry - 启动守护进程模式")
        
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
            print("\n正在停止GPUSentry守护进程...")
            alert_monitor.stop_monitoring()
            report_scheduler.stop_scheduler()
            print("GPUSentry守护进程已停止")
    elif args.mode == 'stats':
        # 统计模式 - 生成历史统计报告
        db_manager = UsageSummary()
        
        if args.report_type:
            # 生成特定类型的报告
            if args.date:
                target_date = datetime.strptime(args.date, '%Y-%m-%d')
            else:
                target_date = datetime.now()
            
            if args.report_type == 'daily':
                report = db_manager.generate_summary_report("daily", target_date)
            elif args.report_type == 'weekly':
                report = db_manager.generate_summary_report("weekly", target_date)
            elif args.report_type == 'monthly':
                report = db_manager.generate_summary_report("monthly", target_date)
            
            print(report)
        else:
            # 显示帮助信息
            print("使用 --report-type 参数指定报告类型: daily, weekly, monthly")
            print("可选参数 --date 指定日期，格式: YYYY-MM-DD")
            print("可选参数 --cleanup-days 清理旧记录的天数")
        
        # 如果指定了清理天数，执行清理
        if args.cleanup_days > 0:
            db_manager.cleanup_old_records(args.cleanup_days)
    elif args.mode == 'report':
        # 立即生成并发送报告
        report_scheduler = ReportScheduler()
        # 发送每日报告
        report_scheduler.generate_and_send_report("daily")


if __name__ == "__main__":
    main()
