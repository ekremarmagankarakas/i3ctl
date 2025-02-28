"""
Bluetooth management commands.
"""

import argparse
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class BluetoothCommand(BaseCommand):
    """
    Command for managing bluetooth connections.
    """

    name = "bluetooth"
    help = "Manage bluetooth connections"

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
        
        # List available bluetooth devices
        list_parser = subparsers.add_parser("list", help="List available bluetooth devices")
        list_parser.add_argument(
            "--scan", "-s",
            action="store_true",
            help="Scan for available devices"
        )
        list_parser.add_argument(
            "--paired", "-p",
            action="store_true",
            help="Show paired devices only"
        )
        
        # Connect to a device
        connect_parser = subparsers.add_parser("connect", help="Connect to a bluetooth device")
        connect_parser.add_argument("device", help="MAC address or device name to connect to")
        
        # Disconnect from device
        disconnect_parser = subparsers.add_parser("disconnect", help="Disconnect from a bluetooth device")
        disconnect_parser.add_argument("device", help="MAC address or device name to disconnect from")
        
        # Pair with a device
        pair_parser = subparsers.add_parser("pair", help="Pair with a bluetooth device")
        pair_parser.add_argument("device", help="MAC address or device name to pair with")
        
        # Remove a paired device
        remove_parser = subparsers.add_parser("remove", help="Remove a paired bluetooth device")
        remove_parser.add_argument("device", help="MAC address or device name to remove")
        
        # Get device status
        status_parser = subparsers.add_parser("status", help="Show bluetooth status")
        
        # Enable or disable bluetooth
        power_parser = subparsers.add_parser("power", help="Turn bluetooth on or off")
        power_parser.add_argument(
            "state",
            choices=["on", "off"],
            help="Turn bluetooth on or off"
        )
        
        # Scan for devices
        scan_parser = subparsers.add_parser("scan", help="Scan for bluetooth devices")
        scan_parser.add_argument(
            "--timeout", "-t",
            type=int,
            default=10,
            help="Scan timeout in seconds"
        )
        scan_parser.add_argument(
            "--continuous", "-c",
            action="store_true",
            help="Scan continuously until interrupted"
        )
        
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
        
        # Detect bluetooth tool
        bluetooth_tool = self._detect_bluetooth_tool()
        
        if not bluetooth_tool:
            logger.error("No supported bluetooth management tool found")
            print("Error: No supported bluetooth management tool found.")
            print("Please install bluetoothctl (bluez) or blueman-manager.")
            return 1
        
        logger.info(f"Using bluetooth tool: {bluetooth_tool}")
        
        # Handle subcommands
        try:
            if args.subcommand == "list":
                self._list_devices(bluetooth_tool, args.scan, args.paired)
            elif args.subcommand == "connect":
                self._connect_device(bluetooth_tool, args.device)
            elif args.subcommand == "disconnect":
                self._disconnect_device(bluetooth_tool, args.device)
            elif args.subcommand == "pair":
                self._pair_device(bluetooth_tool, args.device)
            elif args.subcommand == "remove":
                self._remove_device(bluetooth_tool, args.device)
            elif args.subcommand == "status":
                self._show_status(bluetooth_tool)
            elif args.subcommand == "power":
                self._set_power(bluetooth_tool, args.state == "on")
            elif args.subcommand == "scan":
                self._scan_devices(bluetooth_tool, args.timeout, args.continuous)
                
            return 0
        except Exception as e:
            logger.error(f"Error executing bluetooth command: {e}")
            print(f"Error: {str(e)}")
            return 1
    
    def _detect_bluetooth_tool(self) -> Optional[str]:
        """
        Detect available bluetooth management tool.

        Returns:
            Name of detected tool or None if no tool is found
        """
        if check_command_exists("bluetoothctl"):
            logger.info("Detected bluetoothctl (bluez)")
            return "bluetoothctl"
        elif check_command_exists("blueman-manager"):
            logger.info("Detected blueman-manager")
            return "blueman"
            
        logger.error("No bluetooth management tool found")
        return None
    
    def _list_devices(self, tool: str, scan: bool = False, paired_only: bool = False) -> None:
        """
        List available bluetooth devices.

        Args:
            tool: Bluetooth management tool to use
            scan: Whether to scan for devices first
            paired_only: Whether to show paired devices only
        """
        if scan:
            self._scan_devices(tool, timeout=5, continuous=False)
        
        if tool == "bluetoothctl":
            if paired_only:
                cmd = ["bluetoothctl", "paired-devices"]
                label = "Paired bluetooth devices"
            else:
                cmd = ["bluetoothctl", "devices"]
                label = "Available bluetooth devices"
        elif tool == "blueman":
            # For blueman, we don't have a CLI command to list devices directly
            # So we'll use bluetoothctl's CLI if available as a fallback
            if check_command_exists("bluetoothctl"):
                if paired_only:
                    cmd = ["bluetoothctl", "paired-devices"]
                    label = "Paired bluetooth devices"
                else:
                    cmd = ["bluetoothctl", "devices"]
                    label = "Available bluetooth devices"
            else:
                print("Warning: Cannot list devices through blueman CLI. Please use GUI instead.")
                return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to list devices: {stderr}")
            print(f"Error: Failed to list devices: {stderr}")
            return
        
        if not stdout.strip():
            print("No devices found.")
            return
        
        print(f"\n{label}:")
        print(stdout)
    
    def _connect_device(self, tool: str, device: str) -> None:
        """
        Connect to a bluetooth device.

        Args:
            tool: Bluetooth management tool to use
            device: MAC address or name of the device to connect to
        """
        # Try to get MAC address if a name was provided
        device_mac = self._get_device_mac(tool, device)
        if not device_mac:
            device_mac = device  # Assume the provided device is a MAC address
        
        logger.info(f"Connecting to device: {device_mac}")
        print(f"Connecting to device: {device_mac}")
        
        if tool == "bluetoothctl":
            cmd = ["bluetoothctl", "connect", device_mac]
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                cmd = ["bluetoothctl", "connect", device_mac]
            else:
                print("Warning: Cannot connect through blueman CLI. Please use GUI instead.")
                return
        
        return_code, stdout, stderr = run_command(cmd, timeout=15)  # Bluetooth connections can take time
        
        if return_code != 0 or "Failed to connect" in stdout:
            logger.error(f"Failed to connect to device: {stderr or stdout}")
            print(f"Error: Failed to connect to device: {stderr or stdout}")
            return
        
        print("Connected successfully!")
        
        # Show connection status
        self._show_status(tool)
    
    def _disconnect_device(self, tool: str, device: str) -> None:
        """
        Disconnect from a bluetooth device.

        Args:
            tool: Bluetooth management tool to use
            device: MAC address or name of the device to disconnect from
        """
        # Try to get MAC address if a name was provided
        device_mac = self._get_device_mac(tool, device)
        if not device_mac:
            device_mac = device  # Assume the provided device is a MAC address
        
        logger.info(f"Disconnecting from device: {device_mac}")
        print(f"Disconnecting from device: {device_mac}")
        
        if tool == "bluetoothctl":
            cmd = ["bluetoothctl", "disconnect", device_mac]
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                cmd = ["bluetoothctl", "disconnect", device_mac]
            else:
                print("Warning: Cannot disconnect through blueman CLI. Please use GUI instead.")
                return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0 or "Failed to disconnect" in stdout:
            logger.error(f"Failed to disconnect from device: {stderr or stdout}")
            print(f"Error: Failed to disconnect from device: {stderr or stdout}")
            return
        
        print("Disconnected successfully!")
    
    def _pair_device(self, tool: str, device: str) -> None:
        """
        Pair with a bluetooth device.

        Args:
            tool: Bluetooth management tool to use
            device: MAC address or name of the device to pair with
        """
        # Try to get MAC address if a name was provided
        device_mac = self._get_device_mac(tool, device)
        if not device_mac:
            device_mac = device  # Assume the provided device is a MAC address
        
        logger.info(f"Pairing with device: {device_mac}")
        print(f"Pairing with device: {device_mac}")
        print("Note: You may need to confirm the pairing on both devices.")
        
        if tool == "bluetoothctl":
            # For bluetoothctl, we need to run an interactive session
            print("Using bluetoothctl - follow the prompts on screen...")
            # We'll use a more user-friendly approach with direct console interaction
            run_command(["bluetoothctl", "pair", device_mac], capture_output=False)
            return
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                print("Using bluetoothctl - follow the prompts on screen...")
                run_command(["bluetoothctl", "pair", device_mac], capture_output=False)
                return
            else:
                print("Warning: Cannot pair through blueman CLI. Please use GUI instead.")
                return
    
    def _remove_device(self, tool: str, device: str) -> None:
        """
        Remove a paired bluetooth device.

        Args:
            tool: Bluetooth management tool to use
            device: MAC address or name of the device to remove
        """
        # Try to get MAC address if a name was provided
        device_mac = self._get_device_mac(tool, device)
        if not device_mac:
            device_mac = device  # Assume the provided device is a MAC address
        
        logger.info(f"Removing device: {device_mac}")
        print(f"Removing device: {device_mac}")
        
        if tool == "bluetoothctl":
            cmd = ["bluetoothctl", "remove", device_mac]
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                cmd = ["bluetoothctl", "remove", device_mac]
            else:
                print("Warning: Cannot remove device through blueman CLI. Please use GUI instead.")
                return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0 or "Failed to remove" in stdout:
            logger.error(f"Failed to remove device: {stderr or stdout}")
            print(f"Error: Failed to remove device: {stderr or stdout}")
            return
        
        print("Device removed successfully!")
    
    def _show_status(self, tool: str) -> None:
        """
        Show bluetooth status.

        Args:
            tool: Bluetooth management tool to use
        """
        logger.info("Showing bluetooth status")
        
        if tool == "bluetoothctl":
            cmd = ["bluetoothctl", "show"]
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                cmd = ["bluetoothctl", "show"]
            else:
                # Try using rfkill to at least show power status
                if check_command_exists("rfkill"):
                    cmd = ["rfkill", "list", "bluetooth"]
                else:
                    print("Warning: Cannot show status. No suitable tools found.")
                    return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to get bluetooth status: {stderr}")
            print(f"Error: Failed to get bluetooth status: {stderr}")
            return
        
        if not stdout.strip():
            print("No bluetooth information available.")
            return
        
        print("\nBluetooth Status:")
        print(stdout)
        
        # Also show connected devices
        if tool == "bluetoothctl":
            connected_cmd = ["bluetoothctl", "paired-devices"]
            code, out, err = run_command(connected_cmd)
            if code == 0 and out.strip():
                print("\nPaired Devices:")
                print(out)
    
    def _set_power(self, tool: str, enable: bool) -> None:
        """
        Enable or disable bluetooth.

        Args:
            tool: Bluetooth management tool to use
            enable: Whether to enable or disable bluetooth
        """
        state_str = "on" if enable else "off"
        logger.info(f"Setting bluetooth power to {state_str}")
        print(f"Setting bluetooth power to {state_str}...")
        
        if tool == "bluetoothctl":
            cmd = ["bluetoothctl", "power", state_str]
        elif tool == "blueman":
            # For blueman, we use rfkill if available
            if check_command_exists("rfkill"):
                if enable:
                    cmd = ["rfkill", "unblock", "bluetooth"]
                else:
                    cmd = ["rfkill", "block", "bluetooth"]
            # Also try bluetoothctl as fallback
            elif check_command_exists("bluetoothctl"):
                cmd = ["bluetoothctl", "power", state_str]
            else:
                print("Warning: Cannot set power state. No suitable tools found.")
                return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to set bluetooth power: {stderr}")
            print(f"Error: Failed to set bluetooth power: {stderr}")
            return
        
        print(f"Bluetooth turned {state_str} successfully!")
    
    def _scan_devices(self, tool: str, timeout: int = 10, continuous: bool = False) -> None:
        """
        Scan for bluetooth devices.

        Args:
            tool: Bluetooth management tool to use
            timeout: Scan timeout in seconds
            continuous: Whether to scan continuously
        """
        logger.info(f"Scanning for bluetooth devices (timeout: {timeout}s, continuous: {continuous})")
        print(f"Scanning for bluetooth devices...")
        
        if tool == "bluetoothctl":
            if continuous:
                print("Press Ctrl+C to stop scanning...")
                try:
                    run_command(["bluetoothctl", "scan", "on"], capture_output=False)
                except KeyboardInterrupt:
                    print("\nStopping scan...")
                    run_command(["bluetoothctl", "scan", "off"])
            else:
                # For non-continuous scanning, we'll start, wait, then stop
                print(f"Scanning for {timeout} seconds...")
                run_command(["bluetoothctl", "scan", "on"], capture_output=True)
                time.sleep(timeout)
                run_command(["bluetoothctl", "scan", "off"], capture_output=True)
        elif tool == "blueman":
            # For blueman, we use bluetoothctl as fallback if available
            if check_command_exists("bluetoothctl"):
                if continuous:
                    print("Press Ctrl+C to stop scanning...")
                    try:
                        run_command(["bluetoothctl", "scan", "on"], capture_output=False)
                    except KeyboardInterrupt:
                        print("\nStopping scan...")
                        run_command(["bluetoothctl", "scan", "off"])
                else:
                    # For non-continuous scanning, we'll start, wait, then stop
                    print(f"Scanning for {timeout} seconds...")
                    run_command(["bluetoothctl", "scan", "on"], capture_output=True)
                    time.sleep(timeout)
                    run_command(["bluetoothctl", "scan", "off"], capture_output=True)
            else:
                print("Warning: Cannot scan through blueman CLI. Please use GUI instead.")
                return
        
        print("Scan completed!")
    
    def _get_device_mac(self, tool: str, device_name: str) -> Optional[str]:
        """
        Get MAC address from device name.

        Args:
            tool: Bluetooth management tool to use
            device_name: Name of the device

        Returns:
            MAC address or None if not found
        """
        # First check if the provided string is already a MAC address
        if re.match(r"([0-9A-F]{2}[:-]){5}([0-9A-F]{2})", device_name, re.IGNORECASE):
            return device_name
            
        if tool == "bluetoothctl" or (tool == "blueman" and check_command_exists("bluetoothctl")):
            # Get all devices
            code, out, _ = run_command(["bluetoothctl", "devices"])
            if code != 0 or not out:
                return None
                
            # Parse the output to find the MAC address
            lines = out.strip().split("\n")
            for line in lines:
                if device_name.lower() in line.lower():
                    parts = line.split(" ", 2)
                    if len(parts) >= 2:
                        return parts[1]  # MAC address is the second item
        
        return None