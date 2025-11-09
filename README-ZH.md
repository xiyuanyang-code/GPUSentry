# GPUSentry

> [!IMPORTANT]
> GPUSentry (version 1.0.1) is now up-to-date! 

此版本的 GPUSentry 包含更强大的功能：

- 自动脚本执行
- 日常和月度日志分析
- 自动监控和告警


## 简介

GPUSentry是一个用于实时监控GPU状态的命令行工具。它通过利用`gpustat`工具，提供GPU利用率、内存使用情况、温度和其他相关指标的持续更新显示。

对于AI领域的研究人员来说，"CUDA内存不足"可能是他们遇到的最不受欢迎的错误。与其反复在终端中输入`nvidia-smi`来检查GPU内存使用情况，不如设置一个简单易用的监控工具来关注GPU使用情况？

我们希望它简单且**快速**，成为一个**忠实的哨兵**！

### 功能特性

- 使用 nvitop 的实时GPU监控仪表板
- 持续数据收集和本地数据库存储
- 可配置的监控间隔
- 支持文件和控制台输出的日志系统
- 数据检索和分析功能

## 使用方法

### 安装

```bash
git clone https://github.com/xiyuanyang-code/GPUSentry.git
cd GPUSentry

# 我们推荐使用uv
uv sync
source .venv/bin/activate
uv pip install -e .

# 如果没有uv，也可以直接使用pip
pip install -e .
```

### 基本命令

- `gpusentry` 或 `gpusentry board`：启动GPU监控仪表板
- `gpusentry backend`：启动后台监控服务
- `gpusentry backend --interval 10`：以自定义收集间隔启动（以秒为单位）

## LLM使用说明

本项目中的所有代码均由LLM编写，并在 [spec](./spec/README.md) 中给出了明确规范。
