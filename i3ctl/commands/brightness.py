"""
Brightness control commands.
"""

import argparse
import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_config_value
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class BrightnessCommand(BaseCommand):
    """
    Command for controlling display brightness.
    """

    name = "brightness"
    help = "Control display brightness"

    def __init__(self) -> None:
        """
        Initialize command.
        """
        super().__init__()
        self._brightness_handlers = {
            "xbacklight": self._use_xbacklight,
            "brightnessctl": self._use_brightnessctl,
            "light": self._use_light,
        }

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
        
        # Set command
        set_parser = subparsers.add_parser("set", help="Set brightness to a specific value")
        set_parser.add_argument("value", type=int, help="Brightness value (0-100)")
        
        # Up command
        up_parser = subparsers.add_parser("up", help="Increase brightness")
        up_parser.add_argument("percent", type=int, nargs="?", default=5, 
                              help="Percentage to increase (default: 5)")
        
        # Down command
        down_parser = subparsers.add_parser("down", help="Decrease brightness")
        down_parser.add_argument("percent", type=int, nargs="?", default=5,
                               help="Percentage to decrease (default: 5)")
        
        # Get command
        get_parser = subparsers.add_parser("get", help="Get current brightness")

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
        
        # Get brightness tool from config or auto-detect
        tool = get_config_value("brightness_tool", "auto")
        
        if tool == "auto":
            tool = self._detect_brightness_tool()
            if not tool:
                print("Error: No brightness control tool found.")
                print("Please install xbacklight, brightnessctl, or light.")
                return 1
        elif tool not in self._brightness_handlers:
            logger.error(f"Unsupported brightness tool: {tool}")
            print(f"Error: Unsupported brightness tool: {tool}")
            print(f"Supported tools: {', '.join(self._brightness_handlers.keys())}")
            return 1
        
        logger.info(f"Using brightness tool: {tool}")
        
        # Call appropriate handler for the tool
        handler = self._brightness_handlers[tool]
        
        if args.subcommand == "set":
            value = max(0, min(100, args.value))  # Clamp to 0-100
            return handler("set", value)
        elif args.subcommand == "up":
            return handler("up", args.percent)
        elif args.subcommand == "down":
            return handler("down", args.percent)
        elif args.subcommand == "get":
            return handler("get")
            
        return 0
    
    def _detect_brightness_tool(self) -> Optional[str]:
        """
        Detect available brightness control tool.

        Returns:
            Name of detected tool or None if no tool is found
        """
        # Check for common brightness tools
        if check_command_exists("xbacklight"):
            logger.info("Detected brightness tool: xbacklight")
            return "xbacklight"
        elif check_command_exists("brightnessctl"):
            logger.info("Detected brightness tool: brightnessctl")
            return "brightnessctl"
        elif check_command_exists("light"):
            logger.info("Detected brightness tool: light")
            return "light"
        
        logger.error("No brightness tool found")
        return None
    
    def _use_xbacklight(self, action: str, value: Optional[int] = None) -> int:
        """
        Use xbacklight to control brightness.

        Args:
            action: Action to perform (set, up, down, get)
            value: Value parameter for the action
            
        Returns:
            Exit code
        """
        if action == "set":
            cmd = ["xbacklight", "-set", str(value)]
            msg = f"Setting brightness to {value}%"
        elif action == "up":
            cmd = ["xbacklight", "-inc", str(value)]
            msg = f"Increasing brightness by {value}%"
        elif action == "down":
            cmd = ["xbacklight", "-dec", str(value)]
            msg = f"Decreasing brightness by {value}%"
        elif action == "get":
            cmd = ["xbacklight", "-get"]
            msg = "Current brightness"
        else:
            logger.error(f"Unknown action: {action}")
            return 1
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"xbacklight command failed: {stderr}")
            print(f"Error: {stderr}")
            return 1
        
        if action == "get" and stdout:
            try:
                brightness = float(stdout.strip())
                print(f"Current brightness: {brightness:.1f}%")
            except ValueError:
                print(f"Current brightness: {stdout.strip()}")
        
        return 0
    
    def _use_brightnessctl(self, action: str, value: Optional[int] = None) -> int:
        """
        Use brightnessctl to control brightness.

        Args:
            action: Action to perform (set, up, down, get)
            value: Value parameter for the action
            
        Returns:
            Exit code
        """
        if action == "set":
            cmd = ["brightnessctl", "set", f"{value}%"]
            msg = f"Setting brightness to {value}%"
        elif action == "up":
            cmd = ["brightnessctl", "set", f"{value}%+"]
            msg = f"Increasing brightness by {value}%"
        elif action == "down":
            cmd = ["brightnessctl", "set", f"{value}%-"]
            msg = f"Decreasing brightness by {value}%"
        elif action == "get":
            cmd = ["brightnessctl", "get"]
            msg = "Current brightness"
        else:
            logger.error(f"Unknown action: {action}")
            return 1
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"brightnessctl command failed: {stderr}")
            print(f"Error: {stderr}")
            return 1
        
        if action == "get" and stdout:
            try:
                max_cmd = ["brightnessctl", "max"]
                return_code, max_stdout, _ = run_command(max_cmd)
                
                if return_code == 0 and max_stdout.strip():
                    current = int(stdout.strip())
                    maximum = int(max_stdout.strip())
                    brightness = (current / maximum) * 100
                    print(f"Current brightness: {brightness:.1f}%")
                else:
                    print(f"Current brightness: {stdout.strip()}")
            except ValueError:
                print(f"Current brightness: {stdout.strip()}")
        
        return 0
    
    def _use_light(self, action: str, value: Optional[int] = None) -> int:
        """
        Use light to control brightness.

        Args:
            action: Action to perform (set, up, down, get)
            value: Value parameter for the action
            
        Returns:
            Exit code
        """
        if action == "set":
            cmd = ["light", "-S", str(value)]
            msg = f"Setting brightness to {value}%"
        elif action == "up":
            cmd = ["light", "-A", str(value)]
            msg = f"Increasing brightness by {value}%"
        elif action == "down":
            cmd = ["light", "-U", str(value)]
            msg = f"Decreasing brightness by {value}%"
        elif action == "get":
            cmd = ["light", "-G"]
            msg = "Current brightness"
        else:
            logger.error(f"Unknown action: {action}")
            return 1
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"light command failed: {stderr}")
            print(f"Error: {stderr}")
            return 1
        
        if action == "get" and stdout:
            try:
                brightness = float(stdout.strip())
                print(f"Current brightness: {brightness:.1f}%")
            except ValueError:
                print(f"Current brightness: {stdout.strip()}")
        
        return 0