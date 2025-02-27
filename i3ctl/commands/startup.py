"""
Startup application management commands.
"""

import argparse
import os
import re
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_i3_config_path, load_config, save_config
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class StartupCommand(BaseCommand):
    """
    Command for managing startup applications.
    """

    name = "startup"
    help = "Manage startup applications"

    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Set up command arguments.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        self.parser = parser  # Save the parser for later use
        subparsers = self.parser.add_subparsers(dest="subcommand")
        
        # Add startup command
        add_parser = subparsers.add_parser("add", help="Add a startup command")
        add_parser.add_argument("command", help="Command to add")
        add_parser.add_argument(
            "--once", "-o",
            action="store_true",
            help="Run only once (exec instead of exec_always)"
        )
        add_parser.add_argument(
            "--comment", "-c",
            help="Comment to add with the command"
        )
        
        # Remove startup command
        remove_parser = subparsers.add_parser("remove", help="Remove a startup command")
        remove_parser.add_argument("command", help="Command to remove")
        
        # List startup commands
        list_parser = subparsers.add_parser("list", help="List startup commands")
        list_parser.add_argument(
            "--all", "-a",
            action="store_true",
            help="Show all commands including commented ones"
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
        
        # Get i3 config path
        i3_config_path = get_i3_config_path()
        
        if not os.path.exists(i3_config_path):
            logger.error(f"i3 config file not found: {i3_config_path}")
            print(f"Error: i3 config file not found: {i3_config_path}")
            return 0
        
        # Handle subcommands
        if args.subcommand == "add":
            self._add_startup_command(i3_config_path, args.command, not args.once, args.comment)
        elif args.subcommand == "remove":
            self._remove_startup_command(i3_config_path, args.command)
        elif args.subcommand == "list":
            self._list_startup_commands(i3_config_path, args.all)
            
        return 0
    
    def _add_startup_command(self, config_path: str, command: str, always: bool = True, comment: Optional[str] = None) -> None:
        """
        Add a startup command to i3 config.

        Args:
            config_path: Path to i3 config file
            command: Command to add
            always: Whether to use exec_always (True) or exec (False)
            comment: Optional comment to add
        """
        # Read the config file
        with open(config_path, "r") as f:
            config_lines = f.readlines()
        
        # Check if command already exists
        command_pattern = f"^(exec(_always)?) {re.escape(command)}$"
        for line in config_lines:
            if re.search(command_pattern, line.strip()):
                logger.warning(f"Command already exists in config: {command}")
                print(f"Command already exists in config: {command}")
                return
        
        # Prepare new line
        exec_type = "exec_always" if always else "exec"
        new_line = f"{exec_type} {command}\n"
        
        if comment:
            new_line = f"# {comment}\n{new_line}"
        
        # Find the best place to add the command
        # Look for existing exec or exec_always lines
        last_exec_index = -1
        for i, line in enumerate(config_lines):
            if line.strip().startswith("exec") or line.strip().startswith("# exec"):
                last_exec_index = i
        
        if last_exec_index >= 0:
            # Add after the last exec line
            config_lines.insert(last_exec_index + 1, new_line)
        else:
            # Add at the end of the file
            config_lines.append("\n# Startup applications\n")
            config_lines.append(new_line)
        
        # Write the updated config file
        with open(config_path, "w") as f:
            f.writelines(config_lines)
        
        logger.info(f"Added startup command: {command}")
        print(f"Added startup command: {command}")
        
        # Suggest reloading i3 config
        print("To apply changes, reload the i3 config with: i3ctl config reload")
    
    def _remove_startup_command(self, config_path: str, command: str) -> None:
        """
        Remove a startup command from i3 config.

        Args:
            config_path: Path to i3 config file
            command: Command to remove
        """
        # Read the config file
        with open(config_path, "r") as f:
            config_lines = f.readlines()
        
        # Find all lines with the command
        command_pattern = f"^(exec(_always)?) {re.escape(command)}$"
        matching_indices = []
        
        for i, line in enumerate(config_lines):
            if re.search(command_pattern, line.strip()):
                matching_indices.append(i)
        
        if not matching_indices:
            logger.warning(f"Command not found in config: {command}")
            print(f"Command not found in config: {command}")
            return
        
        # Remove the commands and any associated comments
        for index in sorted(matching_indices, reverse=True):
            # Remove the line
            config_lines.pop(index)
            
            # Check if the previous line is a comment
            if index > 0 and config_lines[index - 1].strip().startswith("#"):
                # Also remove the comment if it's not part of another section
                if index - 1 == 0 or not config_lines[index - 2].strip().startswith("#"):
                    config_lines.pop(index - 1)
        
        # Write the updated config file
        with open(config_path, "w") as f:
            f.writelines(config_lines)
        
        logger.info(f"Removed startup command: {command}")
        print(f"Removed startup command: {command}")
        
        # Suggest reloading i3 config
        print("To apply changes, reload the i3 config with: i3ctl config reload")
    
    def _list_startup_commands(self, config_path: str, show_all: bool = False) -> None:
        """
        List startup commands from i3 config.

        Args:
            config_path: Path to i3 config file
            show_all: Whether to show commented (disabled) commands
        """
        # Read the config file
        with open(config_path, "r") as f:
            config_lines = f.readlines()
        
        # Extract exec and exec_always lines
        exec_lines = []
        exec_always_lines = []
        commented_lines = []
        
        # Also extract comments that precede exec lines
        current_comment = None
        
        for line in config_lines:
            stripped = line.strip()
            
            if stripped.startswith("#"):
                # Store potential comment
                if not current_comment:
                    current_comment = stripped[1:].strip()
                continue
            
            if not stripped:
                # Reset comment on empty line
                current_comment = None
                continue
            
            if stripped.startswith("exec "):
                exec_lines.append((stripped, current_comment))
                current_comment = None
            elif stripped.startswith("exec_always "):
                exec_always_lines.append((stripped, current_comment))
                current_comment = None
            elif show_all and stripped.startswith("# exec"):
                # This is a commented-out exec command
                clean_line = stripped[1:].strip()
                commented_lines.append((clean_line, None))
        
        # Print results
        if not exec_lines and not exec_always_lines and (not commented_lines or not show_all):
            print("No startup commands found.")
            return
        
        # Print exec_always commands
        if exec_always_lines:
            print("\nRun on every startup (exec_always):")
            for cmd, comment in exec_always_lines:
                cmd_str = cmd[len("exec_always "):].strip()
                if comment:
                    print(f"- {cmd_str}  # {comment}")
                else:
                    print(f"- {cmd_str}")
        
        # Print exec commands
        if exec_lines:
            print("\nRun once on startup (exec):")
            for cmd, comment in exec_lines:
                cmd_str = cmd[len("exec "):].strip()
                if comment:
                    print(f"- {cmd_str}  # {comment}")
                else:
                    print(f"- {cmd_str}")
        
        # Print commented (disabled) commands
        if show_all and commented_lines:
            print("\nDisabled startup commands (commented out):")
            for cmd, _ in commented_lines:
                if cmd.startswith("exec_always "):
                    cmd_str = cmd[len("exec_always "):].strip()
                    print(f"- {cmd_str} (always)")
                elif cmd.startswith("exec "):
                    cmd_str = cmd[len("exec "):].strip()
                    print(f"- {cmd_str} (once)")
                else:
                    print(f"- {cmd}")