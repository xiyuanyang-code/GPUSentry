'''Main entry point for GPUSentry CLI application.'''
import sys
import argparse
import time
import platform
from . import board, backend
from .utils.configs import Config

def is_apple_system():
    return platform.system() == 'Darwin'

def has_cuda_driver():
    try:
        from pynvml import nvmlInit, nvmlDeviceGetCount, nvmlShutdown
        nvmlInit()
        count = nvmlDeviceGetCount()
        nvmlShutdown()
        return count > 0
    except Exception:
        return False

def basic_check():
    if is_apple_system():
        print("Sorry, but this tool is designed for Linux Servers or Windows (Supporting Cuda)")
        exit(0)
    if not has_cuda_driver():
        print("Please install Cuda driver first!")
        exit(0)

def main():
    '''Main entry point for the GPUSentry CLI application.'''
    parser = argparse.ArgumentParser(
        prog='gpusentry',
        description='GPU monitoring and intelligent reporting system'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Board command - for monitoring dashboard (default command)
    board_parser = subparsers.add_parser('board', help='Show GPU monitoring dashboard')
    board_parser.add_argument(
        '--config',
        type=str,
        default='./config.yaml',
        help='Path to the configuration file (default: ./config.yaml)'
    )
    
    # Backend command - for background monitoring
    backend_parser = subparsers.add_parser('backend', help='Start backend monitoring service')
    backend_parser.add_argument(
        '--config',
        type=str,
        default='./config.yaml',
        help='Path to the configuration file (default: ./config.yaml)'
    )
    backend_parser.add_argument(
        '--interval',
        type=int,
        help='Data collection interval in seconds (overrides config value)'
    )

    # If no command is specified, default to 'board'
    if len(sys.argv) == 1:
        sys.argv.append('board')

    args = parser.parse_args()

    # Load configuration
    config = Config(config_file_path=args.config)

    if args.command == 'board':
        board.show_dashboard()
    elif args.command == 'backend':
        # Use command-line interval if provided, otherwise use config value
        interval = args.interval if args.interval is not None else config.monitoring_interval
        backend_service = backend.BackendMonitor(interval=interval, config=config)
        try:
            backend_service.start()
            # Keep the main thread alive
            while backend_service.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, stopping backend service...")
            backend_service.stop()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()