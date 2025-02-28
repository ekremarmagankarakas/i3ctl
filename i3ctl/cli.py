#!/usr/bin/env python3
"""
Command line interface for i3ctl.
"""

import argparse
import logging
import sys
import os
from typing import List, Optional

from i3ctl import __version__
from i3ctl.utils.logger import setup_logger, logger
from i3ctl.utils.config import load_config, get_config_value
from i3ctl.utils.system import detect_tools
from i3ctl.commands import get_command_classes, _commands


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up command line argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Control i3 window manager settings."
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"i3ctl {__version__}"
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="count", 
        default=0,
        help="Increase verbosity (can be used multiple times)"
    )
    
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Suppress output"
    )
    
    parser.add_argument(
        "--log-file", 
        help="Log file path"
    )
    
    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Register all commands
    commands = get_command_classes()
    for name, command_class in commands.items():
        command_instance = command_class()
        command_instance.setup_parser(subparsers)
    
    return parser


def configure_logging(args: argparse.Namespace) -> None:
    """
    Configure logging based on command line arguments.

    Args:
        args: Command line arguments
    """
    log_levels = {
        0: logging.WARNING,  # Default
        1: logging.INFO,     # -v
        2: logging.DEBUG,    # -vv
    }
    
    # Get log level from verbosity count, default to max level for excessive counts
    verbosity = min(args.verbose, max(log_levels.keys()))
    log_level = log_levels[verbosity]
    
    # If quiet is set, only show errors
    if args.quiet:
        log_level = logging.ERROR
    
    # Get log file from args or config
    log_file = args.log_file or get_config_value("log_file")
    
    # Configure logger
    setup_logger(
        level=log_level,
        log_file=log_file,
        stream=None if args.quiet else sys.stdout
    )


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the application.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    try:
        # Load configuration
        config = load_config()
        
        # Parse arguments
        parser = setup_parser()
        args = parser.parse_args(argv or sys.argv[1:])
        
        # Configure logging
        configure_logging(args)
        
        # Detect available tools
        tools = detect_tools()
        logger.debug(f"Detected tools: {tools}")
        
        # If no command is specified, show help
        if not args.command:
            parser.print_help()
            return 1
        
        # Execute command if function is provided
        if hasattr(args, "func"):
            try:
                # Capture return value from command handler
                return_code = args.func(args)
                # Return the command's exit code or 0 if None
                return return_code if return_code is not None else 0
            except Exception as e:
                logger.error(f"Command failed: {e}")
                if args.verbose > 0:
                    import traceback
                    traceback.print_exc()
                return 1
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logger.exception("Unexpected error in main")
        return 1


if __name__ == "__main__":
    sys.exit(main())


def execute_command(args: List[str]) -> int:
    """
    Execute a command programmatically.
    
    This function is used by the GUI to execute commands.
    
    Args:
        args: Command arguments (e.g., ["volume", "up", "5"])
        
    Returns:
        Exit code from the command
    """
    try:
        # Get the command name
        if not args or not args[0]:
            logger.error("No command specified")
            return 1
            
        command_name = args[0]
        command_args = args[1:]
        
        # Get the command class
        commands = get_command_classes()
        if command_name not in commands:
            logger.error(f"Unknown command: {command_name}")
            return 1
            
        # Create parser for this command
        parser = argparse.ArgumentParser(description=f"Execute {command_name} command")
        command_instance = commands[command_name]()
        command_instance.setup_parser(parser.add_subparsers())
        
        # Parse arguments
        parsed_args = parser.parse_args([command_name] + command_args)
        
        # Execute command
        if hasattr(parsed_args, "func"):
            return parsed_args.func(parsed_args) or 0
        else:
            logger.error(f"Command {command_name} has no handler")
            return 1
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")
        return 1