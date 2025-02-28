"""
Bar and i3status management commands.
"""

import argparse
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.commands.i3_wrapper import I3Wrapper
from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists
from i3ctl.utils.config import load_config, save_config, CONFIG_DIR


@register_command
class BarCommand(BaseCommand):
    """
    Command for managing i3 bar and i3status.
    """

    name = "bar"
    help = "Manage i3 bar and i3status settings"

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
        
        # Show/hide bar
        show_parser = subparsers.add_parser("show", help="Show the i3 bar")
        
        hide_parser = subparsers.add_parser("hide", help="Hide the i3 bar")
        
        toggle_parser = subparsers.add_parser("toggle", help="Toggle the visibility of the i3 bar")
        
        # Bar mode
        mode_parser = subparsers.add_parser("mode", help="Set the bar mode")
        mode_parser.add_argument(
            "mode",
            choices=["dock", "hide", "invisible"],
            help="Bar mode (dock: always visible, hide: hidden until mod key is pressed, invisible: never shown)"
        )
        
        # i3status commands
        i3status_parser = subparsers.add_parser("i3status", help="Manage i3status")
        i3status_subparsers = i3status_parser.add_subparsers(dest="i3status_command")
        
        # i3status reload
        i3status_reload_parser = i3status_subparsers.add_parser("reload", help="Reload i3status configuration")
        
        # i3status edit
        i3status_edit_parser = i3status_subparsers.add_parser("edit", help="Edit i3status configuration")
        i3status_edit_parser.add_argument(
            "--editor",
            help="Editor to use (defaults to $EDITOR environment variable)"
        )
        
        # Bar config
        config_parser = subparsers.add_parser("config", help="Manage bar configuration")
        config_subparsers = config_parser.add_subparsers(dest="config_command")
        
        # Bar config edit
        config_edit_parser = config_subparsers.add_parser("edit", help="Edit bar configuration in i3 config")
        config_edit_parser.add_argument(
            "--editor",
            help="Editor to use (defaults to $EDITOR environment variable)"
        )
        
        # Bar config list
        config_list_parser = config_subparsers.add_parser("list", help="List bar configurations")
        
        # Status
        status_parser = subparsers.add_parser("status", help="Show bar status")
        
        return parser

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
        
        # Check if i3 is available
        try:
            I3Wrapper.ensure_i3()
        except Exception as e:
            logger.error(f"i3 not found: {e}")
            print(f"Error: i3 not found. {e}")
            return 1
        
        try:
            # Handle bar commands
            if args.subcommand == "show":
                return self._show_bar()
            elif args.subcommand == "hide":
                return self._hide_bar()
            elif args.subcommand == "toggle":
                return self._toggle_bar()
            elif args.subcommand == "mode":
                return self._set_bar_mode(args.mode)
            elif args.subcommand == "status":
                return self._show_bar_status()
            elif args.subcommand == "i3status":
                if not args.i3status_command:
                    print("Please specify an i3status command. Use --help for more information.")
                    return 1
                    
                if args.i3status_command == "reload":
                    return self._reload_i3status()
                elif args.i3status_command == "edit":
                    return self._edit_i3status_config(args.editor)
            elif args.subcommand == "config":
                if not args.config_command:
                    print("Please specify a config command. Use --help for more information.")
                    return 1
                    
                if args.config_command == "edit":
                    return self._edit_bar_config(args.editor)
                elif args.config_command == "list":
                    return self._list_bar_configs()
                
            return 0
            
        except Exception as e:
            logger.error(f"Error executing bar command: {e}")
            print(f"Error: {str(e)}")
            return 1
    
    def _show_bar(self) -> int:
        """
        Show the i3 bar.
        
        Returns:
            Exit code
        """
        logger.info("Showing i3 bar")
        print("Showing i3 bar...")
        
        success, result = I3Wrapper.i3_command(["bar", "mode", "dock"])
        
        if not success:
            logger.error("Failed to show i3 bar")
            print("Error: Failed to show i3 bar")
            return 1
        
        print("i3 bar is now visible.")
        return 0
    
    def _hide_bar(self) -> int:
        """
        Hide the i3 bar.
        
        Returns:
            Exit code
        """
        logger.info("Hiding i3 bar")
        print("Hiding i3 bar...")
        
        success, result = I3Wrapper.i3_command(["bar", "mode", "hide"])
        
        if not success:
            logger.error("Failed to hide i3 bar")
            print("Error: Failed to hide i3 bar")
            return 1
        
        print("i3 bar is now hidden (press Mod key to show temporarily).")
        return 0
    
    def _toggle_bar(self) -> int:
        """
        Toggle the visibility of the i3 bar.
        
        Returns:
            Exit code
        """
        logger.info("Toggling i3 bar visibility")
        print("Toggling i3 bar visibility...")
        
        # Try to get current bar mode
        try:
            success, result = I3Wrapper.i3_command(["bar", "mode"])
            current_mode = None
            
            if success and result:
                for item in result:
                    if isinstance(item, dict) and "mode" in item:
                        current_mode = item["mode"]
                        break
            
            # If we couldn't get the current mode, assume it's dock
            if not current_mode:
                current_mode = "dock"
                
            # Toggle the mode
            new_mode = "hide" if current_mode == "dock" else "dock"
            
            success, result = I3Wrapper.i3_command(["bar", "mode", new_mode])
            
            if not success:
                logger.error(f"Failed to set bar mode to {new_mode}")
                print(f"Error: Failed to set bar mode to {new_mode}")
                return 1
            
            print(f"i3 bar mode changed from '{current_mode}' to '{new_mode}'")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to toggle bar: {e}")
            print(f"Error: Failed to toggle bar: {e}")
            
            # Fallback - just try to set it to hide
            try:
                print("Trying fallback: setting bar to hide mode...")
                success, _ = I3Wrapper.i3_command(["bar", "mode", "hide"])
                if success:
                    print("Bar set to hide mode.")
                    return 0
                else:
                    print("Fallback failed.")
                    return 1
            except Exception as e2:
                logger.error(f"Fallback failed: {e2}")
                print(f"Fallback error: {e2}")
                return 1
    
    def _set_bar_mode(self, mode: str) -> int:
        """
        Set the bar mode.
        
        Args:
            mode: Bar mode (dock, hide, invisible)
            
        Returns:
            Exit code
        """
        logger.info(f"Setting i3 bar mode to {mode}")
        print(f"Setting i3 bar mode to {mode}...")
        
        success, result = I3Wrapper.i3_command(["bar", "mode", mode])
        
        if not success:
            logger.error(f"Failed to set bar mode to {mode}")
            print(f"Error: Failed to set bar mode to {mode}")
            return 1
        
        mode_descriptions = {
            "dock": "always visible",
            "hide": "hidden until Mod key is pressed",
            "invisible": "never shown"
        }
        
        print(f"i3 bar mode set to '{mode}' ({mode_descriptions.get(mode, '')}).")
        return 0
    
    def _reload_i3status(self) -> int:
        """
        Reload i3status configuration.
        
        Returns:
            Exit code
        """
        logger.info("Reloading i3status")
        print("Reloading i3status...")
        
        # First check if i3status is installed
        if not check_command_exists("killall") or not check_command_exists("i3status"):
            logger.error("i3status not found")
            print("Error: i3status not found. Please install i3status.")
            return 1
        
        # Send SIGUSR1 signal to i3status to reload
        return_code, stdout, stderr = run_command(["killall", "-USR1", "i3status"])
        
        if return_code != 0:
            logger.error(f"Failed to reload i3status: {stderr}")
            print(f"Error: Failed to reload i3status: {stderr}")
            
            # If killall failed, it might be because i3status is not running
            print("i3status might not be running. Restarting i3 may be required.")
            return 1
        
        print("i3status configuration reloaded.")
        return 0
    
    def _edit_i3status_config(self, editor: Optional[str] = None) -> int:
        """
        Edit i3status configuration.
        
        Args:
            editor: Editor to use
            
        Returns:
            Exit code
        """
        logger.info("Editing i3status configuration")
        
        # Find i3status config path
        config_path = self._find_i3status_config()
        
        if not config_path:
            logger.error("i3status config not found")
            print("Error: i3status config not found.")
            print("Creating a new i3status config file...")
            
            # Create a default config
            config_path = os.path.expanduser("~/.config/i3status/config")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write default config
            try:
                with open(config_path, "w") as f:
                    f.write(DEFAULT_I3STATUS_CONFIG)
                print(f"Created default i3status config at {config_path}")
            except Exception as e:
                logger.error(f"Failed to create i3status config: {e}")
                print(f"Error: Failed to create i3status config: {e}")
                return 1
        
        # Get editor
        if not editor:
            editor = os.environ.get("EDITOR", "nano")
        
        # Check if editor exists
        if not check_command_exists(editor):
            logger.error(f"Editor {editor} not found")
            print(f"Error: Editor {editor} not found. Please install it or specify a different editor.")
            return 1
        
        print(f"Editing i3status config at {config_path} with {editor}...")
        
        # Open editor
        try:
            subprocess.run([editor, config_path])
            print("i3status config edited. Use 'i3ctl bar i3status reload' to apply changes.")
            return 0
        except Exception as e:
            logger.error(f"Failed to open editor: {e}")
            print(f"Error: Failed to open editor: {e}")
            return 1
    
    def _edit_bar_config(self, editor: Optional[str] = None) -> int:
        """
        Edit bar configuration in i3 config.
        
        Args:
            editor: Editor to use
            
        Returns:
            Exit code
        """
        logger.info("Editing i3 bar configuration")
        
        # Find i3 config path
        config_path = self._find_i3_config()
        
        if not config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        # Get editor
        if not editor:
            editor = os.environ.get("EDITOR", "nano")
        
        # Check if editor exists
        if not check_command_exists(editor):
            logger.error(f"Editor {editor} not found")
            print(f"Error: Editor {editor} not found. Please install it or specify a different editor.")
            return 1
        
        print(f"Editing i3 config at {config_path} with {editor}...")
        print("Look for the 'bar {{' section to edit bar configuration.")
        
        # Open editor
        try:
            subprocess.run([editor, config_path])
            print("i3 config edited. Reload i3 to apply changes.")
            return 0
        except Exception as e:
            logger.error(f"Failed to open editor: {e}")
            print(f"Error: Failed to open editor: {e}")
            return 1
    
    def _list_bar_configs(self) -> int:
        """
        List bar configurations.
        
        Returns:
            Exit code
        """
        logger.info("Listing i3 bar configurations")
        
        bar_configs = self._get_bar_configs()
        
        if not bar_configs:
            logger.error("Failed to get bar configurations")
            print("No bar configurations found in your i3 config.")
            return 1
        
        print(f"Found {len(bar_configs)} bar configuration(s):")
        for i, bar in enumerate(bar_configs, 1):
            print(f"\nBar #{i}:")
            for key, value in bar.items():
                print(f"  {key}: {value}")
        
        return 0
    
    def _show_bar_status(self) -> int:
        """
        Show bar status.
        
        Returns:
            Exit code
        """
        logger.info("Showing i3 bar status")
        
        # Get i3 config file path
        i3_config_path = self._find_i3_config()
        
        print("i3 Bar Status:")
        
        # Even if we can't get bar configs directly from i3-msg,
        # we can still try to read the i3 config file
        if i3_config_path:
            print(f"\nConfig file: {i3_config_path}")
            try:
                # Read i3 config file to find bar configurations
                with open(i3_config_path, "r") as f:
                    config_content = f.read()
                
                # Look for bar sections
                bar_sections = []
                in_bar_section = False
                current_section = []
                brace_count = 0
                
                for line in config_content.splitlines():
                    line = line.strip()
                    if line.startswith("bar {"):
                        in_bar_section = True
                        brace_count = 1
                        current_section = ["bar {"]
                    elif in_bar_section:
                        current_section.append(line)
                        if "{" in line:
                            brace_count += line.count("{")
                        if "}" in line:
                            brace_count -= line.count("}")
                            if brace_count == 0:
                                in_bar_section = False
                                bar_sections.append("\n".join(current_section))
                
                if bar_sections:
                    print(f"\nFound {len(bar_sections)} bar configuration(s) in i3 config:")
                    for i, section in enumerate(bar_sections, 1):
                        print(f"\nBar #{i}:")
                        
                        # Extract key properties
                        properties = {}
                        for line in section.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#") and line != "bar {" and "}" not in line:
                                # Try to extract key-value pairs
                                try:
                                    key, value = line.split(" ", 1)
                                    properties[key] = value.strip()
                                except ValueError:
                                    continue
                        
                        # Display properties
                        for key, value in properties.items():
                            print(f"  {key}: {value}")
                else:
                    print("\nNo bar sections found in i3 config.")
            except Exception as e:
                logger.error(f"Failed to parse i3 config: {e}")
                print(f"Error reading i3 config: {e}")
        
        # Try to get bar mode using i3-msg command
        try:
            success, result = I3Wrapper.i3_command(["bar", "mode"])
            if success and result:
                print("\nCurrent bar mode:", result[0].get("mode", "unknown"))
        except Exception as e:
            logger.error(f"Failed to get bar mode: {e}")
            
        # Check i3status
        
        # Also check i3status
        if check_command_exists("i3status"):
            print("\ni3status:")
            # Check if i3status is running
            return_code, stdout, stderr = run_command(["pgrep", "i3status"])
            if return_code == 0:
                print("  Status: Running")
            else:
                print("  Status: Not running")
            
            # Find i3status config
            config_path = self._find_i3status_config()
            if config_path:
                print(f"  Config: {config_path}")
            else:
                print("  Config: Not found")
        else:
            print("\ni3status: Not installed")
        
        return 0
    
    def _get_bar_configs(self) -> List[Dict[str, str]]:
        """
        Get bar configurations from i3 tree.
        
        Returns:
            List of bar configurations
        """
        try:
            success, result = I3Wrapper.i3_command(["bar", "mode"])
            
            if not success or not result:
                return []
            
            # If the bar mode command succeeded, we can create a mock config
            # with the information we have
            bar_configs = []
            for item in result:
                if isinstance(item, dict):
                    bar_configs.append(item)
            
            return bar_configs
        except Exception as e:
            logger.error(f"Failed to get bar configs: {e}")
            return []
    
    def _find_i3_config(self) -> Optional[str]:
        """
        Find i3 config file.
        
        Returns:
            Path to i3 config file or None if not found
        """
        # Common i3 config locations
        locations = [
            os.path.expanduser("~/.config/i3/config"),
            os.path.expanduser("~/.i3/config"),
            "/etc/i3/config"
        ]
        
        for location in locations:
            if os.path.isfile(location):
                return location
        
        return None
    
    def _find_i3status_config(self) -> Optional[str]:
        """
        Find i3status config file.
        
        Returns:
            Path to i3status config file or None if not found
        """
        # Common i3status config locations
        locations = [
            os.path.expanduser("~/.config/i3status/config"),
            os.path.expanduser("~/.i3status.conf"),
            "/etc/i3status.conf"
        ]
        
        # Also check if it's specified in the i3 config
        i3_config_path = self._find_i3_config()
        if i3_config_path:
            try:
                with open(i3_config_path, "r") as f:
                    i3_config = f.read()
                    
                    # Look for status_command
                    for line in i3_config.splitlines():
                        if "status_command" in line and "-c" in line:
                            # Extract config path
                            parts = line.split("-c")
                            if len(parts) >= 2:
                                path = parts[1].strip().split()[0].strip()
                                # Remove quotes if any
                                path = path.strip('"\'')
                                # Expand user
                                path = os.path.expanduser(path)
                                if os.path.isfile(path):
                                    return path
            except Exception as e:
                logger.error(f"Failed to read i3 config: {e}")
        
        for location in locations:
            if os.path.isfile(location):
                return location
        
        return None


# Default i3status config template
DEFAULT_I3STATUS_CONFIG = """# i3status configuration file
# see "man i3status" for documentation

general {
        colors = true
        interval = 5
}

order += "cpu_usage"
order += "memory"
order += "disk /"
order += "wireless _first_"
order += "ethernet _first_"
order += "battery all"
order += "tztime local"

wireless _first_ {
        format_up = "W: (%quality at %essid) %ip"
        format_down = "W: down"
}

ethernet _first_ {
        format_up = "E: %ip"
        format_down = "E: down"
}

battery all {
        format = "%status %percentage %remaining"
}

disk "/" {
        format = "%avail"
}

memory {
        format = "%used | %available"
        threshold_degraded = "1G"
        format_degraded = "MEMORY < %available"
}

cpu_usage {
        format = "CPU: %usage"
}

tztime local {
        format = "%Y-%m-%d %H:%M:%S"
}
"""