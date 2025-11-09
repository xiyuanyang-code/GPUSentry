"""Module for displaying GPU monitoring dashboard using nvitop."""

import subprocess
import sys
import time
import os
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")
    os.system("reset")


def show_time_compute(begin_time: float, end_time: float) -> None:
    """
    Print start time, end time and elapsed duration in a colored table.

    Args:
        begin_time: timestamp from time.time() when monitoring started
        end_time:   timestamp from time.time() when monitoring stopped
    """
    start_dt = datetime.fromtimestamp(begin_time)
    end_dt = datetime.fromtimestamp(end_time)
    elapsed = end_time - begin_time

    # Human-readable duration (hh:mm:ss.mmm)
    hours, rem = divmod(int(elapsed), 3600)
    minutes, sec = divmod(rem, 60)
    duration_str = f"{hours:02d}:{minutes:02d}:{sec + elapsed % 1:05.2f}"

    # Header
    print(Fore.CYAN + Style.BRIGHT + "\n=== GPU Monitoring Session Summary ===")
    print(Fore.CYAN + Style.BRIGHT + "═" * 42)

    # Table rows
    print(
        f"{Fore.GREEN}Start time : {Style.RESET_ALL}{start_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(
        f"{Fore.YELLOW}End time   : {Style.RESET_ALL}{end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"{Fore.MAGENTA}Duration   : {Style.RESET_ALL}{duration_str} seconds")
    print(f"{Fore.WHITE}SEE YOU NEXT TIME!😚")

    print(Fore.CYAN + Style.BRIGHT + "═" * 42 + Style.RESET_ALL)


def show_dashboard():
    """Display GPU monitoring dashboard using nvitop.

    Args:
        refresh_interval: Refresh interval in seconds (default: 5)
    """
    try:
        begin_time = time.time()
        # Use nvitop to show the dashboard with interval
        subprocess.run(["nvitop"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running nvitop: {e}", file=sys.stderr)
        clear_terminal()
        sys.exit(1)
    except FileNotFoundError:
        print("Error: nvitop is not installed or not found in PATH", file=sys.stderr)
        clear_terminal()
        sys.exit(1)
    except KeyboardInterrupt as e:
        print("Detecting Key Board Interuptions, exiting...")
        clear_terminal()
        end_time = time.time()
        show_time_compute(begin_time, end_time)
        sys.exit(0)
