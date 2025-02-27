"""
i3 configuration management commands.
"""

import argparse
import os
import subprocess
from typing import List, Optional

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_i3_config_path, get_config_value
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class ConfigCommand(BaseCommand):
    """
    Command for managing i3 configuration.
    """

    name = "config"
    help = "Manage i3 configuration"

    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Set up command arguments.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        self.parser = parser  # Save the parser for later use
        subparsers = parser.add_subparsers(dest="subcommand")
        
        # Edit command
        edit_parser = subparsers.add_parser("edit", help="Edit i3 config file")
        edit_parser.add_argument(
            "--editor", 
            help="Editor to use (default: $EDITOR or nano)"
        )
        
        # Reload command
        reload_parser = subparsers.add_parser("reload", help="Reload i3 config")
        
        # Show config path command
        path_parser = subparsers.add_parser("path", help="Show i3 config file path")
        
        # Show config command
        show_parser = subparsers.add_parser("show", help="Show i3 config file content")
        show_parser.add_argument(
            "--lines", "-n",
            type=int,
            help="Number of lines to show"
        )
    
    def handle(self, args: argparse.Namespace) -> int:
        """
        Handle command execution.

        Args:
            args: Command arguments
            
        Returns:
            Exit code
        """
        if not args.subcommand:
            self.parser.print_help()
            return 0
        
        config_path = get_i3_config_path()
        
        if not os.path.exists(config_path):
            logger.error(f"i3 config file not found: {config_path}")
            print(f"Error: i3 config file not found: {config_path}")
            return 1
        
        if args.subcommand == "edit":
            return self._edit_config(config_path, args.editor)
        elif args.subcommand == "reload":
            return self._reload_config()
        elif args.subcommand == "path":
            return self._show_config_path(config_path)
        elif args.subcommand == "show":
            return self._show_config(config_path, args.lines)
        
        return 0
    
    def _edit_config(self, config_path: str, editor: Optional[str] = None) -> int:
        """
        Edit i3 config file.

        Args:
            config_path: Path to i3 config file
            editor: Editor to use (uses $EDITOR environment variable if not specified)
            
        Returns:
            Exit code
        """
        # Get editor from args, environment, or fall back to nano
        if not editor:
            editor = os.environ.get("EDITOR", "nano")
        
        logger.info(f"Opening i3 config with {editor}")
        print(f"Opening i3 config with {editor}")
        
        try:
            # Run editor with config file
            subprocess.call([editor, config_path])
            
            # Ask if user wants to reload the config
            print("\nDo you want to reload the i3 config? (y/n) ", end="")
            response = input().strip().lower()
            
            if response in ["y", "yes"]:
                return self._reload_config()
            
            return 0
        except FileNotFoundError:
            logger.error(f"Editor not found: {editor}")
            print(f"Error: Editor not found: {editor}")
            print("Please specify a valid editor with --editor option or set the EDITOR environment variable.")
            return 1
        except Exception as e:
            logger.error(f"Failed to open editor: {e}")
            print(f"Error: Failed to open editor: {e}")
            return 1
    
    def _reload_config(self) -> int:
        """
        Reload i3 config.
        
        Returns:
            Exit code
        """
        logger.info("Reloading i3 config")
        print("Reloading i3 config...")
        
        # Send reload command to i3
        return_code, stdout, stderr = run_command(["i3-msg", "reload"])
        
        if return_code != 0:
            logger.error(f"Failed to reload i3 config: {stderr}")
            print(f"Error: Failed to reload i3 config: {stderr}")
            return 1
        
        logger.info("i3 config reloaded successfully")
        print("i3 config reloaded successfully")
        return 0
    
    def _show_config_path(self, config_path: str) -> int:
        """
        Show i3 config file path.

        Args:
            config_path: Path to i3 config file
            
        Returns:
            Exit code
        """
        print(f"i3 config file path: {config_path}")
        return 0
    
    def _show_config(self, config_path: str, num_lines: Optional[int] = None) -> int:
        """
        Show i3 config file content.

        Args:
            config_path: Path to i3 config file
            num_lines: Number of lines to show (shows all if None)
            
        Returns:
            Exit code
        """
        try:
            with open(config_path, "r") as f:
                lines = f.readlines()
            
            if num_lines:
                lines = lines[:num_lines]
                print(f"Showing first {num_lines} lines of i3 config:")
            else:
                print("i3 config file content:")
            
            for i, line in enumerate(lines):
                print(f"{i+1:4d} | {line}", end="")
            
            if num_lines and len(lines) < num_lines:
                print(f"\n(Shown all {len(lines)} lines)")
            
            return 0
        except Exception as e:
            logger.error(f"Failed to read i3 config: {e}")
            print(f"Error: Failed to read i3 config: {e}")
            return 1