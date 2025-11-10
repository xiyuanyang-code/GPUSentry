# GPUSentry

> [!IMPORTANT]
> GPUSentry (version 1.0.1) is now up-to-date! 

This version for GPUSentry contains more powerful features:

- Auto Scripting
- Analyzing Logger for daily & monthly
- Automatic Monitoring and Alerting


## Introduction

GPUSentry is a command-line tool for monitoring GPU status in real-time. It provides a continuously updating display of GPU utilization, memory usage, temperature, and other relevant metrics by leveraging the `gpustat` utility.

For researchers in the field of AI, `CUDA out of memory` is likely the most unwelcome error they can encounter. Instead of repeatedly typing `nvidia-smi` into the terminal to check GPU memory usage, why not set up a simple and user-friendly monitoring tool to keep an eye on GPU usage?

We want it to be simple, and **fast** enough as a **loyal sentry**!

### Features

- Real-time GPU monitoring dashboard using nvitop
- Continuous data collection and local database storage
- Configurable monitoring intervals
- Logging system with file and console output
- Data retrieval and analysis capabilities

## Usage

### Installation

```bash
git clone https://github.com/xiyuanyang-code/GPUSentry.git
cd GPUSentry

# we recommend using uv
uv sync
sourve .venv/bin/activate
uv pip install -e .

# if you do not have uv, you can also use it directly in pip
pip install -e .
```

### Configurations

Copy [`config.example.yaml`](./config.example.yaml) into `config.yaml`.

```yaml
# GPUSentry Configuration File

# Feishu Webhook Configuration
feishu:
  keyword: "GPUSentry"
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your-hook"

# Monitoring Settings
monitoring:
  interval: 5  # Monitoring interval (seconds)
  enable_logging: true  # Whether to enable logging

LLM:
  model_name: deepseek-chat
  OPENAI_API_KEY: sk-your-api-key
  BASE_URL: https://api.deepseek.com

# Reporting Settings
# todo to be done in the future

# alert settings
# todo to be done in the future
```

- For message sending of alert and notifications, you are required to create a Feishu Bot and get the webhook-url.
- Configure your LLM api-key for OpenAI SDK format.

### Basic Commands

- `gpusentry` or `gpusentry board`: Launch GPU monitoring dashboard
- `gpusentry backend`: Start background monitoring service
- `gpusentry backend --interval 10`: Start with custom collection interval (in seconds)
- `gpusentry reset`: reset database
- `gpusentry send $1`: for debugging, sending last `$1` minutes to Feishu Webhook

## LLM Usage

All the code in this project is written by LLM, with specifications given clearly in [spec](./spec/README.md).