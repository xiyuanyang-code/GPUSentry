import gpustat
import time
import psutil
import logging
from typing import Dict, List, Optional
from datetime import datetime
from colorama import Fore, Style, init
import json


# 初始化colorama
init(autoreset=True)


class GPUStats:
    """GPU统计信息类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_gpu_stats(self) -> Optional[List[Dict]]:
        """
        获取GPU统计信息
        
        Returns:
            List[Dict]: GPU信息列表，如果出错则返回None
        """
        try:
            # 使用gpustat获取GPU信息
            stats = gpustat.new_query()
            gpu_info = []
            
            for gpu in stats.gpus:
                # 计算显存使用率
                memory_utilization = (gpu.memory_used / gpu.memory_total * 100) if gpu.memory_total > 0 else 0
                
                gpu_data = {
                    'index': gpu.index,
                    'name': gpu.name,
                    'temperature': gpu.temperature,
                    'utilization': gpu.utilization,
                    'memory_used': gpu.memory_used,
                    'memory_total': gpu.memory_total,
                    'memory_utilization': memory_utilization,
                    'processes': [
                        {
                            'pid': p['pid'],
                            'username': p['username'],
                            'command': p['command'],
                            'gpu_memory': p['gpu_memory']
                        }
                        for p in gpu.processes
                    ]
                }
                gpu_info.append(gpu_data)
            
            return gpu_info
        except Exception as e:
            self.logger.error(f"获取GPU统计信息时出错: {e}")
            return None
    
    def get_system_stats(self) -> Dict:
        """
        获取系统统计信息
        
        Returns:
            Dict: 系统信息
        """
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def format_gpu_stats(self, gpu_stats: List[Dict], system_stats: Dict) -> str:
        """
        格式化GPU统计信息为美观的字符串
        
        Args:
            gpu_stats (List[Dict]): GPU统计信息
            system_stats (Dict): 系统统计信息
            
        Returns:
            str: 格式化后的字符串
        """
        if not gpu_stats:
            return "无法获取GPU信息"
        
        # 构建输出字符串
        output_lines = []
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_lines.append(f"{Fore.CYAN}=== GPUSentry - {timestamp} ==={Style.RESET_ALL}")
        
        # 添加系统信息
        output_lines.append(f"{Fore.YELLOW}系统信息:{Style.RESET_ALL}")
        output_lines.append(f"  CPU使用率: {system_stats['cpu_percent']:.1f}%")
        output_lines.append(f"  内存使用率: {system_stats['memory_percent']:.1f}%")
        output_lines.append("")
        
        # 添加GPU信息
        output_lines.append(f"{Fore.YELLOW}GPU信息:{Style.RESET_ALL}")
        for gpu in gpu_stats:
            # 根据GPU利用率设置颜色
            if gpu['utilization'] > 80:
                util_color = Fore.RED
            elif gpu['utilization'] > 50:
                util_color = Fore.YELLOW
            else:
                util_color = Fore.GREEN
                
            # 根据GPU内存使用率设置颜色
            memory_util = (gpu['memory_used'] / gpu['memory_total']) * 100 if gpu['memory_total'] > 0 else 0
            if memory_util > 80:
                mem_color = Fore.RED
            elif memory_util > 50:
                mem_color = Fore.YELLOW
            else:
                mem_color = Fore.GREEN
                
            # 根据温度设置颜色
            if gpu['temperature'] > 80:
                temp_color = Fore.RED
            elif gpu['temperature'] > 60:
                temp_color = Fore.YELLOW
            else:
                temp_color = Fore.GREEN
            
            output_lines.append(f"  GPU {gpu['index']}: {gpu['name']}")
            output_lines.append(f"    温度: {temp_color}{gpu['temperature']}°C{Style.RESET_ALL}")
            output_lines.append(f"    利用率: {util_color}{gpu['utilization']}%{Style.RESET_ALL}")
            output_lines.append(f"    显存: {mem_color}{gpu['memory_used']}MB / {gpu['memory_total']}MB ({memory_util:.1f}%){Style.RESET_ALL}")
            
            # 显示进程信息
            if gpu['processes']:
                output_lines.append(f"    进程:")
                for process in gpu['processes']:
                    output_lines.append(f"      PID {process['pid']} ({process['username']}): {process['command']} - {process['gpu_memory']}MB")
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def display_stats(self, show_processes: bool = True) -> bool:
        """
        显示GPU统计信息
        
        Args:
            show_processes (bool): 是否显示进程信息
            
        Returns:
            bool: 是否成功显示
        """
        gpu_stats = self.get_gpu_stats()
        if gpu_stats is None:
            print(f"{Fore.RED}无法获取GPU信息，请检查NVIDIA驱动和nvidia-ml-py是否正确安装{Style.RESET_ALL}")
            return False
            
        system_stats = self.get_system_stats()
        formatted_stats = self.format_gpu_stats(gpu_stats, system_stats)
        print(formatted_stats)
        return True


def main():
    """主函数，用于实时显示GPU状态"""
    gpu_stats = GPUStats()
    
    print(f"{Fore.GREEN}GPUSentry - GPU监控系统启动{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}按 Ctrl+C 退出{Style.RESET_ALL}")
    
    try:
        while True:
            # 清屏
            print("\033[2J\033[H", end="")
            
            # 显示统计信息
            gpu_stats.display_stats()
            
            # 等待
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}GPUSentry 已退出{Style.RESET_ALL}")


if __name__ == "__main__":
    main()