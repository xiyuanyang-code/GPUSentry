import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


Base = declarative_base()


class GPUStatsRecord(Base):
    """GPU统计记录表"""
    __tablename__ = 'gpu_stats'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    gpu_index = Column(Integer, index=True)
    gpu_name = Column(String(255))
    temperature = Column(Integer)  # 温度（摄氏度）
    utilization = Column(Float)    # 利用率（百分比）
    memory_used = Column(Integer)  # 已用显存（MB）
    memory_total = Column(Integer) # 总显存（MB）
    memory_utilization = Column(Float)  # 显存利用率（百分比）
    system_cpu_percent = Column(Float)
    system_memory_percent = Column(Float)
    processes = Column(Text)  # 进程信息的JSON字符串

class UsageSummary:
    """使用情况统计摘要"""
    
    def __init__(self, db_path: str = "gpusentry.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def save_gpu_stats(self, gpu_stats: List[Dict], system_stats: Dict):
        """保存GPU统计信息到数据库"""
        try:
            with self.get_session() as session:
                for gpu in gpu_stats:
                    record = GPUStatsRecord(
                        timestamp=datetime.fromisoformat(system_stats['timestamp']),
                        gpu_index=gpu['index'],
                        gpu_name=gpu['name'],
                        temperature=gpu['temperature'],
                        utilization=gpu['utilization'],
                        memory_used=gpu['memory_used'],
                        memory_total=gpu['memory_total'],
                        memory_utilization=gpu['memory_utilization'],
                        system_cpu_percent=system_stats['cpu_percent'],
                        system_memory_percent=system_stats['memory_percent'],
                        processes=json.dumps(gpu['processes'])
                    )
                    session.add(record)
        except Exception as e:
            logging.error(f"保存GPU统计信息时出错: {e}")
    
    def get_daily_summary(self, date: datetime) -> Dict:
        """获取指定日期的GPU使用摘要"""
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        with self.get_session() as session:
            records = session.query(GPUStatsRecord).filter(
                GPUStatsRecord.timestamp >= start_time,
                GPUStatsRecord.timestamp < end_time
            ).all()
            
            if not records:
                return {"message": f"没有找到 {date.strftime('%Y-%m-%d')} 的数据"}
            
            # 按GPU索引分组统计
            gpu_stats = {}
            for record in records:
                if record.gpu_index not in gpu_stats:
                    gpu_stats[record.gpu_index] = {
                        'name': record.gpu_name,
                        'temperatures': [],
                        'utilizations': [],
                        'memory_usages': [],
                        'max_temperature': 0,
                        'max_utilization': 0,
                        'max_memory_usage': 0
                    }
                
                gpu_stat = gpu_stats[record.gpu_index]
                gpu_stat['temperatures'].append(record.temperature)
                gpu_stat['utilizations'].append(record.utilization)
                memory_usage = (record.memory_used / record.memory_total) * 100 if record.memory_total > 0 else 0
                gpu_stat['memory_usages'].append(memory_usage)
                
                gpu_stat['max_temperature'] = max(gpu_stat['max_temperature'], record.temperature)
                gpu_stat['max_utilization'] = max(gpu_stat['max_utilization'], record.utilization)
                gpu_stat['max_memory_usage'] = max(gpu_stat['max_memory_usage'], memory_usage)
        
        # 计算平均值
        for gpu_idx in gpu_stats:
            stat = gpu_stats[gpu_idx]
            stat['avg_temperature'] = sum(stat['temperatures']) / len(stat['temperatures'])
            stat['avg_utilization'] = sum(stat['utilizations']) / len(stat['utilizations'])
            stat['avg_memory_usage'] = sum(stat['memory_usages']) / len(stat['memory_usages'])
        
        return {
            "date": date.strftime('%Y-%m-%d'),
            "gpu_stats": gpu_stats,
            "total_records": len(records)
        }
    
    def get_weekly_summary(self, start_date: datetime) -> Dict:
        """获取一周的GPU使用摘要"""
        end_date = start_date + timedelta(days=7)
        
        with self.get_session() as session:
            records = session.query(GPUStatsRecord).filter(
                GPUStatsRecord.timestamp >= start_date,
                GPUStatsRecord.timestamp < end_date
            ).all()
            
            if not records:
                return {"message": f"没有找到从 {start_date.strftime('%Y-%m-%d')} 开始的一周数据"}
            
            # 按GPU索引分组统计
            gpu_stats = {}
            for record in records:
                if record.gpu_index not in gpu_stats:
                    gpu_stats[record.gpu_index] = {
                        'name': record.gpu_name,
                        'temperatures': [],
                        'utilizations': [],
                        'memory_usages': [],
                        'max_temperature': 0,
                        'max_utilization': 0,
                        'max_memory_usage': 0
                    }
                
                gpu_stat = gpu_stats[record.gpu_index]
                gpu_stat['temperatures'].append(record.temperature)
                gpu_stat['utilizations'].append(record.utilization)
                memory_usage = (record.memory_used / record.memory_total) * 100 if record.memory_total > 0 else 0
                gpu_stat['memory_usages'].append(memory_usage)
                
                gpu_stat['max_temperature'] = max(gpu_stat['max_temperature'], record.temperature)
                gpu_stat['max_utilization'] = max(gpu_stat['max_utilization'], record.utilization)
                gpu_stat['max_memory_usage'] = max(gpu_stat['max_memory_usage'], memory_usage)
        
        # 计算平均值
        for gpu_idx in gpu_stats:
            stat = gpu_stats[gpu_idx]
            stat['avg_temperature'] = sum(stat['temperatures']) / len(stat['temperatures'])
            stat['avg_utilization'] = sum(stat['utilizations']) / len(stat['utilizations'])
            stat['avg_memory_usage'] = sum(stat['memory_usages']) / len(stat['memory_usages'])
        
        return {
            "week_start": start_date.strftime('%Y-%m-%d'),
            "week_end": end_date.strftime('%Y-%m-%d'),
            "gpu_stats": gpu_stats,
            "total_records": len(records)
        }
    
    def get_monthly_summary(self, start_date: datetime) -> Dict:
        """获取一个月的GPU使用摘要"""
        # 计算一个月后的日期
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1)
        
        with self.get_session() as session:
            records = session.query(GPUStatsRecord).filter(
                GPUStatsRecord.timestamp >= start_date,
                GPUStatsRecord.timestamp < end_date
            ).all()
            
            if not records:
                return {"message": f"没有找到从 {start_date.strftime('%Y-%m-%d')} 开始的一个月数据"}
            
            # 按GPU索引分组统计
            gpu_stats = {}
            for record in records:
                if record.gpu_index not in gpu_stats:
                    gpu_stats[record.gpu_index] = {
                        'name': record.gpu_name,
                        'temperatures': [],
                        'utilizations': [],
                        'memory_usages': [],
                        'max_temperature': 0,
                        'max_utilization': 0,
                        'max_memory_usage': 0
                    }
                
                gpu_stat = gpu_stats[record.gpu_index]
                gpu_stat['temperatures'].append(record.temperature)
                gpu_stat['utilizations'].append(record.utilization)
                memory_usage = (record.memory_used / record.memory_total) * 100 if record.memory_total > 0 else 0
                gpu_stat['memory_usages'].append(memory_usage)
                
                gpu_stat['max_temperature'] = max(gpu_stat['max_temperature'], record.temperature)
                gpu_stat['max_utilization'] = max(gpu_stat['max_utilization'], record.utilization)
                gpu_stat['max_memory_usage'] = max(gpu_stat['max_memory_usage'], memory_usage)
        
        # 计算平均值
        for gpu_idx in gpu_stats:
            stat = gpu_stats[gpu_idx]
            stat['avg_temperature'] = sum(stat['temperatures']) / len(stat['temperatures'])
            stat['avg_utilization'] = sum(stat['utilizations']) / len(stat['utilizations'])
            stat['avg_memory_usage'] = sum(stat['memory_usages']) / len(stat['memory_usages'])
        
        return {
            "month_start": start_date.strftime('%Y-%m-%d'),
            "month_end": end_date.strftime('%Y-%m-%d'),
            "gpu_stats": gpu_stats,
            "total_records": len(records)
        }
    
    def generate_summary_report(self, summary_type: str, date: datetime) -> str:
        """生成摘要报告字符串"""
        if summary_type == "daily":
            summary = self.get_daily_summary(date)
            report = f"📊 GPU日度使用报告 ({summary['date']})\n\n"
            
            if 'message' in summary:
                return summary['message']
            
            for gpu_idx, stats in summary['gpu_stats'].items():
                report += f"GPU {gpu_idx} ({stats['name']}):\n"
                report += f"  平均温度: {stats['avg_temperature']:.1f}°C\n"
                report += f"  最高温度: {stats['max_temperature']}°C\n"
                report += f"  平均利用率: {stats['avg_utilization']:.1f}%\n"
                report += f"  最高利用率: {stats['max_utilization']:.1f}%\n"
                report += f"  平均显存使用率: {stats['avg_memory_usage']:.1f}%\n"
                report += f"  最高显存使用率: {stats['max_memory_usage']:.1f}%\n\n"
                
            report += f"总记录数: {summary['total_records']}\n"
            
        elif summary_type == "weekly":
            summary = self.get_weekly_summary(date)
            report = f"📊 GPU周度使用报告 ({summary['week_start']} 至 {summary['week_end']})\n\n"
            
            if 'message' in summary:
                return summary['message']
            
            for gpu_idx, stats in summary['gpu_stats'].items():
                report += f"GPU {gpu_idx} ({stats['name']}):\n"
                report += f"  平均温度: {stats['avg_temperature']:.1f}°C\n"
                report += f"  最高温度: {stats['max_temperature']}°C\n"
                report += f"  平均利用率: {stats['avg_utilization']:.1f}%\n"
                report += f"  最高利用率: {stats['max_utilization']:.1f}%\n"
                report += f"  平均显存使用率: {stats['avg_memory_usage']:.1f}%\n"
                report += f"  最高显存使用率: {stats['max_memory_usage']:.1f}%\n\n"
                
            report += f"总记录数: {summary['total_records']}\n"
            
        elif summary_type == "monthly":
            summary = self.get_monthly_summary(date)
            report = f"📊 GPU月度使用报告 ({summary['month_start']} 至 {summary['month_end']})\n\n"
            
            if 'message' in summary:
                return summary['message']
            
            for gpu_idx, stats in summary['gpu_stats'].items():
                report += f"GPU {gpu_idx} ({stats['name']}):\n"
                report += f"  平均温度: {stats['avg_temperature']:.1f}°C\n"
                report += f"  最高温度: {stats['max_temperature']}°C\n"
                report += f"  平均利用率: {stats['avg_utilization']:.1f}%\n"
                report += f"  最高利用率: {stats['max_utilization']:.1f}%\n"
                report += f"  平均显存使用率: {stats['avg_memory_usage']:.1f}%\n"
                report += f"  最高显存使用率: {stats['max_memory_usage']:.1f}%\n\n"
                
            report += f"总记录数: {summary['total_records']}\n"
        else:
            report = "未知的摘要类型"
        
        return report
    
    def cleanup_old_records(self, days_to_keep: int = 30):
        """清理旧记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.get_session() as session:
            deleted_count = session.query(GPUStatsRecord).filter(
                GPUStatsRecord.timestamp < cutoff_date
            ).delete()
            
        logging.info(f"已清理 {deleted_count} 条旧记录，保留 {days_to_keep} 天的数据")