# GPUSentry

## Introduction

GPUSentry is a command-line tool for monitoring GPU status in real-time. It provides a continuously updating display of GPU utilization, memory usage, temperature, and other relevant metrics by leveraging the `gpustat` utility.

For researchers in the field of AI, `CUDA out of memory` is likely the most unwelcome error they can encounter. Instead of repeatedly typing `nvidia-smi` into the terminal to check GPU memory usage, why not set up a simple and user-friendly monitoring tool to keep an eye on GPU usage?

We want it to be simple, and **fast** enough as a **loyal sentry**!

## Features

- Real-time GPU monitoring with customizable refresh intervals and flushing options.
- Colorized output for better readability (using `gpustat`)
- Terminal clearing option for a clean display
- Lightweight and efficient implementation (Written in Rust)

## Dependencies

This tool requires the following dependencies to be installed on your system:

1. **Rust** - The tool is written in Rust and requires the Rust toolchain for building

    For methods of installing rust, see [Rust Official Docs](https://www.rust-lang.org/tools/install) for more information.

2. **gpustat** - A command-line utility for GPU monitoring that this tool wraps

    `gpustat` can be installed via pip:

    ```bash
    pip install gpustat
    ```


## Installation

```bash
# clone the repo
git clone https://github.com/xiyuanyang-code/GPUSentry.git
cd GPUSentry

# build the project using Cargo
cargo build --release
# The executable will be located at `target/release/GPUSentry`

# install the executable into path for better CLI usage
cargo install --path .
```


## Usage

After installation, you can run the tool with:

```bash
GPUSentry [OPTIONS]
```

- `-i, --interval <SECONDS>`: Set the refresh interval in seconds (default: 2, only support integer.)
- `--flush`: Clear the terminal before each update for a cleaner display
- `-h, --help`: Display help information
- `-V, --version`: Display version information

1. Basic usage with default 2-second refresh interval:
   ```bash
   GPUSentry
   ```

2. Set a custom refresh interval of 5 seconds:
   ```bash
   GPUSentry -i 5
   ```

3. Use the flush option for a clean display:
   ```bash
   GPUSentry --flush
   ```

4. Combine options:
   ```bash
   GPUSentry -i 3 --flush
   ```

## Demo

<video src="./assets/demo.mp4" controls width="800"></video>

## Todo List

> [!TIP]
> This project still in construction process.

- [ ] Add more info for the sentry
- [ ] Support more options for GPU monitoring
- [ ] Integrating with another project: Feishu GPU Monitoring