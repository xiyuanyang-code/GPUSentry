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

### Basic Commands

- `gpusentry` or `gpusentry board`: Launch GPU monitoring dashboard
- `gpusentry backend`: Start background monitoring service
- `gpusentry backend --interval 10`: Start with custom collection interval (in seconds)

## LLM Usage

All the code in this project is written by LLM, with specifications given clearly in [spec](./spec/README.md).