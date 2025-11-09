'''Main entry point for GPUSentry CLI application.'''
import sys
import argparse
import time
from . import board, backend

def main():
    '''Main entry point for the GPUSentry CLI application.'''
    parser = argparse.ArgumentParser(
        prog='gpusentry',
        description='GPU monitoring and intelligent reporting system'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Board command - for monitoring dashboard (default command)
    board_parser = subparsers.add_parser('board', help='Show GPU monitoring dashboard')
    # Backend command - for background monitoring
    backend_parser = subparsers.add_parser('backend', help='Start backend monitoring service')
    backend_parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Data collection interval in seconds (default: 5)'
    )

    # If no command is specified, default to 'board'
    if len(sys.argv) == 1:
        sys.argv.append('board')

    args = parser.parse_args()

    if args.command == 'board':
        board.show_dashboard()
    elif args.command == 'backend':
        backend_service = backend.BackendMonitor(args.interval)
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