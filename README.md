# GPUSentry

GPUSentry is a GPU monitoring and intelligent reporting system designed for individual developers, combining nvitop's dashboard functionality with gpustat's beautiful display, while providing logging, alerting, and regular reporting features.

## Features

- 📊 Real-time GPU monitoring: Dashboard display similar to nvitop and gpustat
- 🎨 Beautiful color output: Automatically colored based on usage
- 📝 Logging: Save GPU usage data to local database
- 📈 Intelligent statistics: Generate daily/weekly/monthly usage reports
- 🚨 Alert system: Send alerts via Feishu webhook when GPU usage is abnormal
- 📋 Automatic reports: Generate and send usage reports to Feishu regularly

## Installation

```bash
# Clone the project
git clone <repository-url>
cd GPUSentry

# Install dependencies
pip install -e .
```

## Configuration

Edit the `config.yaml` file to configure the Feishu webhook and other settings:

```yaml
# Feishu Webhook Configuration
feishu:
  keyword: "GPUSentry"
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url"

# Monitoring Settings
monitoring:
  interval: 5  # Monitoring interval (seconds)
  enable_logging: true  # Whether to enable logging

# Alert Settings
alerting:
  enable_alerts: true  # Whether to enable alerts
  gpu_memory_threshold: 0.9  # GPU memory usage threshold (90%)
  gpu_utilization_threshold: 0.95  # GPU utilization threshold (95%)
  temperature_threshold: 80  # GPU temperature threshold (Celsius)
```

## Usage

### Real-time Monitoring Mode

```bash
python main.py --mode monitor
```

Or using the command-line tool:
```bash
gpusentry --mode monitor
```

### Background Daemon Mode

```bash
python main.py --mode daemon
```

Or using the command-line tool:
```bash
gpusentry --mode daemon
```

### View Statistics Reports

```bash
# Generate daily report
python main.py --mode stats --report-type daily

# Generate report for specific date
python main.py --mode stats --report-type daily --date 2025-01-01

# Generate weekly report
python main.py --mode stats --report-type weekly

# Generate monthly report
python main.py --mode stats --report-type monthly

# Clean up old records (keep 30 days)
python main.py --mode stats --cleanup-days 30

# Using command-line tool
gpusentry --mode stats --report-type daily
```

### Send Report Immediately

```bash
python main.py --mode report
```

Or using the command-line tool:
```bash
gpusentry --mode report
```

## Dependencies

- Python 3.13+
- NVIDIA drivers and nvidia-ml-py
- gpustat
- psutil
- colorama
- tabulate
- sqlalchemy
- pyyaml
- requests
- paramiko

## License

MIT