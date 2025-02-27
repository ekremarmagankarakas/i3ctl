"""
Volume control commands.
"""

import argparse
import re
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_config_value
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class VolumeCommand(BaseCommand):
    """
    Command for controlling audio volume.
    """

    name = "volume"
    help = "Control audio volume"

    def __init__(self) -> None:
        """
        Initialize command.
        """
        super().__init__()
        self._volume_handlers = {
            "pulseaudio": self._use_pulseaudio,
            "alsa": self._use_alsa,
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
        set_parser = subparsers.add_parser("set", help="Set volume to a specific value")
        set_parser.add_argument("value", type=int, help="Volume value (0-100)")
        
        # Up command
        up_parser = subparsers.add_parser("up", help="Increase volume")
        up_parser.add_argument("percent", type=int, nargs="?", default=5, 
                              help="Percentage to increase (default: 5)")
        
        # Down command
        down_parser = subparsers.add_parser("down", help="Decrease volume")
        down_parser.add_argument("percent", type=int, nargs="?", default=5,
                               help="Percentage to decrease (default: 5)")
        
        # Get command
        get_parser = subparsers.add_parser("get", help="Get current volume")
        
        # Mute command
        mute_parser = subparsers.add_parser("mute", help="Mute or unmute volume")
        mute_parser.add_argument(
            "--state", 
            choices=["on", "off", "toggle"],
            default="toggle",
            help="Mute state (default: toggle)"
        )

    def handle(self, args: argparse.Namespace) -> None:
        """
        Handle command execution.

        Args:
            args: Command arguments
        """
        if not args.subcommand:
            self.parser.print_help()
            return
        
        # Get volume tool from config or auto-detect
        tool = get_config_value("volume_tool", "auto")
        
        if tool == "auto":
            tool = self._detect_volume_tool()
            if not tool:
                print("Error: No volume control tool found.")
                print("Please install PulseAudio (pactl) or ALSA (amixer).")
                return
        elif tool not in self._volume_handlers:
            logger.error(f"Unsupported volume tool: {tool}")
            print(f"Error: Unsupported volume tool: {tool}")
            print(f"Supported tools: {', '.join(self._volume_handlers.keys())}")
            return
        
        logger.info(f"Using volume tool: {tool}")
        
        # Call appropriate handler for the tool
        handler = self._volume_handlers[tool]
        
        if args.subcommand == "set":
            value = max(0, min(100, args.value))  # Clamp to 0-100
            handler("set", value)
        elif args.subcommand == "up":
            handler("up", args.percent)
        elif args.subcommand == "down":
            handler("down", args.percent)
        elif args.subcommand == "get":
            handler("get")
        elif args.subcommand == "mute":
            handler("mute", args.state)
    
    def _detect_volume_tool(self) -> Optional[str]:
        """
        Detect available volume control tool.

        Returns:
            Name of detected tool or None if no tool is found
        """
        # Check for common volume tools
        if check_command_exists("pactl"):
            logger.info("Detected PulseAudio tool: pactl")
            return "pulseaudio"
        elif check_command_exists("amixer"):
            logger.info("Detected ALSA tool: amixer")
            return "alsa"
        
        logger.error("No volume tool found")
        return None
    
    def _use_pulseaudio(self, action: str, value: Optional[str] = None) -> None:
        """
        Use PulseAudio to control volume.

        Args:
            action: Action to perform (set, up, down, get, mute)
            value: Value parameter for the action
        """
        # Get default sink
        sink = self._get_default_pulseaudio_sink()
        if not sink:
            print("Error: No PulseAudio sink found")
            return
        
        if action == "set":
            cmd = ["pactl", "set-sink-volume", sink, f"{value}%"]
            msg = f"Setting volume to {value}%"
        elif action == "up":
            cmd = ["pactl", "set-sink-volume", sink, f"+{value}%"]
            msg = f"Increasing volume by {value}%"
        elif action == "down":
            cmd = ["pactl", "set-sink-volume", sink, f"-{value}%"]
            msg = f"Decreasing volume by {value}%"
        elif action == "get":
            volume, muted = self._get_pulseaudio_volume(sink)
            print(f"Current volume: {volume}%")
            print(f"Muted: {muted}")
            return
        elif action == "mute":
            if value == "on":
                cmd = ["pactl", "set-sink-mute", sink, "1"]
                msg = "Muting volume"
            elif value == "off":
                cmd = ["pactl", "set-sink-mute", sink, "0"]
                msg = "Unmuting volume"
            else:  # toggle
                cmd = ["pactl", "set-sink-mute", sink, "toggle"]
                msg = "Toggling mute state"
        else:
            logger.error(f"Unknown action: {action}")
            return
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"pactl command failed: {stderr}")
            print(f"Error: {stderr}")
            return
        
        # Show current volume after changing it
        if action != "get":
            volume, muted = self._get_pulseaudio_volume(sink)
            print(f"Current volume: {volume}%")
            print(f"Muted: {muted}")
    
    def _get_default_pulseaudio_sink(self) -> Optional[str]:
        """
        Get default PulseAudio sink.

        Returns:
            Sink name or None if not found
        """
        # First try "get-default-sink" command (newer PulseAudio versions)
        return_code, stdout, stderr = run_command(["pactl", "get-default-sink"])
        
        if return_code == 0 and stdout.strip():
            return stdout.strip()
        
        # Fallback to "info" command for older versions
        return_code, stdout, stderr = run_command(["pactl", "info"])
        
        if return_code == 0 and stdout:
            for line in stdout.splitlines():
                if "Default Sink:" in line:
                    return line.split(":", 1)[1].strip()
        
        return None
    
    def _get_pulseaudio_volume(self, sink: str) -> Tuple[int, bool]:
        """
        Get current PulseAudio volume and mute state.

        Args:
            sink: Sink name

        Returns:
            Tuple of (volume percentage, is muted)
        """
        return_code, stdout, stderr = run_command(["pactl", "get-sink-volume", sink])
        
        volume = 0
        if return_code == 0 and stdout:
            # Parse volume from output
            volume_match = re.search(r"(\d+)%", stdout)
            if volume_match:
                volume = int(volume_match.group(1))
        
        return_code, stdout, stderr = run_command(["pactl", "get-sink-mute", sink])
        
        muted = False
        if return_code == 0 and stdout:
            muted = "yes" in stdout.lower()
        
        return volume, muted
    
    def _use_alsa(self, action: str, value: Optional[str] = None) -> None:
        """
        Use ALSA to control volume.

        Args:
            action: Action to perform (set, up, down, get, mute)
            value: Value parameter for the action
        """
        if action == "set":
            cmd = ["amixer", "sset", "Master", f"{value}%"]
            msg = f"Setting volume to {value}%"
        elif action == "up":
            cmd = ["amixer", "sset", "Master", f"{value}%+"]
            msg = f"Increasing volume by {value}%"
        elif action == "down":
            cmd = ["amixer", "sset", "Master", f"{value}%-"]
            msg = f"Decreasing volume by {value}%"
        elif action == "get":
            cmd = ["amixer", "sget", "Master"]
            msg = "Current volume"
        elif action == "mute":
            if value == "on":
                cmd = ["amixer", "sset", "Master", "mute"]
                msg = "Muting volume"
            elif value == "off":
                cmd = ["amixer", "sset", "Master", "unmute"]
                msg = "Unmuting volume"
            else:  # toggle
                cmd = ["amixer", "sset", "Master", "toggle"]
                msg = "Toggling mute state"
        else:
            logger.error(f"Unknown action: {action}")
            return
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"amixer command failed: {stderr}")
            print(f"Error: {stderr}")
            return
        
        if action == "get" or stdout:
            # Parse volume and mute state from amixer output
            volume_match = re.search(r"(\d+)%", stdout)
            muted_match = re.search(r"\[(on|off)\]", stdout)
            
            volume = volume_match.group(1) if volume_match else "unknown"
            muted = "yes" if muted_match and muted_match.group(1) == "off" else "no"
            
            print(f"Current volume: {volume}%")
            print(f"Muted: {muted}")
