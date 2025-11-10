"""Main entry point for GPUSentry CLI application."""

import sys
import argparse
import time
import platform
from . import board, backend
from .utils.configs import Config


def is_apple_system():
    return platform.system() == "Darwin"


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
        print(
            "Sorry, but this tool is designed for Linux Servers or Windows (Supporting Cuda)"
        )
        exit(0)
    if not has_cuda_driver():
        print("Please install Cuda driver first!")
        exit(0)


def main():
    """Main entry point for the GPUSentry CLI application."""
    parser = argparse.ArgumentParser(
        prog="gpusentry", description="GPU monitoring and intelligent reporting system"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Board command - for monitoring dashboard (default command)
    board_parser = subparsers.add_parser("board", help="Show GPU monitoring dashboard")
    board_parser.add_argument(
        "--config",
        type=str,
        default="./config.yaml",
        help="Path to the configuration file (default: ./config.yaml)",
    )

    # Backend command - for background monitoring
    backend_parser = subparsers.add_parser(
        "backend", help="Start backend monitoring service"
    )
    backend_parser.add_argument(
        "--config",
        type=str,
        default="./config.yaml",
        help="Path to the configuration file (default: ./config.yaml)",
    )
    backend_parser.add_argument(
        "--interval",
        type=int,
        help="Data collection interval in seconds (overrides config value)",
    )

    # Reset command - clear database
    reset_parser = subparsers.add_parser(
        "reset", help="Reset database and generate statistics"
    )
    reset_parser.add_argument(
        "--config",
        type=str,
        default="./config.yaml",
        help="Path to the configuration file (default: ./config.yaml)",
    )
    reset_parser.add_argument(
        "--force", action="store_true", help="Force reset without confirmation"
    )

    # Send command - send custom report for last N minutes
    send_parser = subparsers.add_parser("send", help="Send report for the last N minutes")
    send_parser.add_argument(
        "minutes", type=int, help="Number of minutes to look back for the report"
    )
    send_parser.add_argument(
        "--config",
        type=str,
        default="./config.yaml",
        help="Path to the configuration file (default: ./config.yaml)",
    )

    # If no command is specified, default to 'board'
    if len(sys.argv) == 1:
        sys.argv.append("board")

    args = parser.parse_args()

    # Load configuration
    config = Config(config_file_path=args.config)

    if args.command == "board":
        board.show_dashboard()
    elif args.command == "backend":
        # Use command-line interval if provided, otherwise use config value
        interval = (
            args.interval if args.interval is not None else config.monitoring_interval
        )
        backend_service = backend.BackendMonitor(interval=interval, config=config)
        try:
            backend_service.start()
            # Keep the main thread alive
            while backend_service.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, stopping backend service...")
            backend_service.stop()
    elif args.command == "reset":
        from .database import DatabaseManager
        from .utils.feishu_msg import send_feishu_message

        # Initialize database manager
        db_manager = DatabaseManager(db_path=config.database_path)

        # Get current statistics before reset
        stats = db_manager.get_statistics()
        print("Current database statistics:")
        print(f"  Total records: {stats['total_records']}")
        print(
            f"  Time range: {stats['first_record_time']} to {stats['last_record_time']}"
        )
        print(f"  Unique GPUs: {stats['unique_gpus']}")
        print(f"  Average memory used: {stats['average_memory_used']} MB")
        print(f"  Average utilization: {stats['average_utilization']}%")

        # Confirm reset unless --force is used
        if not args.force:
            confirm = input(
                "Are you sure you want to reset the database? This will delete all data. (yes/no): "
            )
            if confirm.lower() not in ["yes", "y"]:
                print("Reset cancelled.")
                return

        # Reset the database
        db_manager.reset_database()
        print("Database has been reset successfully.")

        # Send message to Feishu if configured
        if config.feishu_webhook_url:
            message = f"Database reset completed. Previous data had {stats['total_records']} records over time range {stats['first_record_time']} to {stats['last_record_time']}"
            send_feishu_message(message)
    elif args.command == "send":
        from .database import DatabaseManager
        from .reporter import GPUReporter
        from .utils.feishu_msg import send_feishu_message

        # Initialize database manager
        db_manager = DatabaseManager(db_path=config.database_path)
        reporter = GPUReporter(db_manager, config)

        # Generate and send custom report
        n_minutes = args.minutes
        if n_minutes <= 0:
            print(f"Error: Minutes must be a positive integer, got {n_minutes}")
            sys.exit(1)

        print(f"Generating report for the last {n_minutes} minutes...")
        report = reporter.generate_custom_report(n_minutes)

        # Send report to Feishu
        if config.feishu_webhook_url:
            success = reporter.send_report_to_feishu(report)
            if success:
                print(
                    f"Report for the last {n_minutes} minutes sent to Feishu successfully!"
                )
            else:
                print(f"Failed to send report for the last {n_minutes} minutes to Feishu.")
        else:
            print("Feishu webhook URL not configured. Report generated but not sent.")
        
        # Also print the summary to console
        print("\n" + "="*50)
        print("REPORT SUMMARY")
        print("="*50)
        print(report['rule_based_summary'])
        print("\nLLM ANALYSIS:")
        print(report['llm_summary'])
        print("="*50)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
