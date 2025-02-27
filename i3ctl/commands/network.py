"""
Network management commands.
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
class NetworkCommand(BaseCommand):
    """
    Command for managing network connections.
    """

    name = "network"
    help = "Manage network connections"

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
        
        # List available networks
        list_parser = subparsers.add_parser("list", help="List available Wi-Fi networks")
        list_parser.add_argument(
            "--rescan", "-r",
            action="store_true",
            help="Rescan for available networks"
        )
        list_parser.add_argument(
            "--saved", "-s",
            action="store_true",
            help="Show saved connections only"
        )
        
        # Connect to a network
        connect_parser = subparsers.add_parser("connect", help="Connect to a Wi-Fi network")
        connect_parser.add_argument("ssid", help="SSID of the network to connect to")
        connect_parser.add_argument(
            "--password", "-p",
            help="Password for the network"
        )
        
        # Disconnect from network
        disconnect_parser = subparsers.add_parser("disconnect", help="Disconnect from current network")
        
        # Get network status
        status_parser = subparsers.add_parser("status", help="Show current network status")
        
        # Enable or disable WiFi
        wifi_parser = subparsers.add_parser("wifi", help="Turn Wi-Fi on or off")
        wifi_parser.add_argument(
            "state",
            choices=["on", "off"],
            help="Turn Wi-Fi on or off"
        )
        
        # Rescan for networks
        rescan_parser = subparsers.add_parser("rescan", help="Rescan for available networks")

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
        
        # Detect network manager
        network_tool = self._detect_network_tool()
        
        if not network_tool:
            logger.error("No supported network management tool found")
            print("Error: No supported network management tool found.")
            print("Please install NetworkManager (nmcli), iwd, or wpa_supplicant.")
            return 1
        
        logger.info(f"Using network tool: {network_tool}")
        
        # Handle subcommands
        if args.subcommand == "list":
            self._list_networks(network_tool, args.rescan, args.saved)
        elif args.subcommand == "connect":
            self._connect_network(network_tool, args.ssid, args.password)
        elif args.subcommand == "disconnect":
            self._disconnect_network(network_tool)
        elif args.subcommand == "status":
            self._show_network_status(network_tool)
        elif args.subcommand == "wifi":
            self._set_wifi_state(network_tool, args.state == "on")
        elif args.subcommand == "rescan":
            self._rescan_networks(network_tool)
            
        return 0
    
    def _detect_network_tool(self) -> Optional[str]:
        """
        Detect available network management tool.

        Returns:
            Name of detected tool or None if no tool is found
        """
        if check_command_exists("nmcli"):
            logger.info("Detected NetworkManager (nmcli)")
            return "nmcli"
        elif check_command_exists("iwctl"):
            logger.info("Detected iwd (iwctl)")
            return "iwctl"
        elif check_command_exists("wpa_cli"):
            logger.info("Detected wpa_supplicant (wpa_cli)")
            return "wpa_cli"
        
        logger.error("No network management tool found")
        return None
    
    def _list_networks(self, tool: str, rescan: bool = False, saved_only: bool = False) -> None:
        """
        List available Wi-Fi networks.

        Args:
            tool: Network management tool to use
            rescan: Whether to rescan for networks
            saved_only: Whether to show saved networks only
        """
        if rescan:
            self._rescan_networks(tool)
        
        if tool == "nmcli":
            if saved_only:
                cmd = ["nmcli", "connection", "show"]
                label = "Saved connections"
            else:
                cmd = ["nmcli", "--colors", "no", "--fields", "IN-USE,BARS,SIGNAL,SECURITY,SSID", "device", "wifi", "list"]
                label = "Available Wi-Fi networks"
        elif tool == "iwctl":
            if saved_only:
                cmd = ["iwctl", "known-networks", "list"]
                label = "Saved connections"
            else:
                cmd = ["iwctl", "station", "wlan0", "get-networks"]
                label = "Available Wi-Fi networks"
        elif tool == "wpa_cli":
            if saved_only:
                cmd = ["wpa_cli", "list_networks"]
                label = "Saved connections"
            else:
                cmd = ["wpa_cli", "scan_results"]
                label = "Available Wi-Fi networks"
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to list networks: {stderr}")
            print(f"Error: Failed to list networks: {stderr}")
            return
        
        if not stdout.strip():
            print("No networks found.")
            return
        
        print(f"\n{label}:")
        print(stdout)
    
    def _connect_network(self, tool: str, ssid: str, password: Optional[str] = None) -> None:
        """
        Connect to a Wi-Fi network.

        Args:
            tool: Network management tool to use
            ssid: SSID of the network to connect to
            password: Password for the network
        """
        logger.info(f"Connecting to network: {ssid}")
        print(f"Connecting to network: {ssid}")
        
        if tool == "nmcli":
            if password:
                cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
            else:
                cmd = ["nmcli", "device", "wifi", "connect", ssid]
        elif tool == "iwctl":
            # For iwctl, we need to use an interactive approach
            print("Using iwctl - please follow the prompts...")
            if password:
                # Store password in temporary file to avoid showing it in process list
                with open("/tmp/wifi_pass.tmp", "w") as f:
                    f.write(password)
                run_command(["iwctl", "station", "wlan0", "connect", ssid, "--passphrase", password])
                # Remove the temporary file
                os.remove("/tmp/wifi_pass.tmp")
            else:
                run_command(["iwctl", "station", "wlan0", "connect", ssid])
            return
        elif tool == "wpa_cli":
            # For wpa_cli, we need a complex sequence of commands
            if password:
                print("Using wpa_cli - please wait...")
                # Add a new network
                _, network_id, _ = run_command(["wpa_cli", "add_network"])
                network_id = network_id.strip()
                
                # Set the SSID
                run_command(["wpa_cli", "set_network", network_id, "ssid", f'"{ssid}"'])
                
                # Set the password
                run_command(["wpa_cli", "set_network", network_id, "psk", f'"{password}"'])
                
                # Enable the network
                run_command(["wpa_cli", "enable_network", network_id])
                
                # Save the configuration
                run_command(["wpa_cli", "save_config"])
                
                # Wait for connection
                print("Waiting for connection...")
                time.sleep(5)
                return
            else:
                print("Error: wpa_cli requires a password for connecting to a network.")
                return
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to connect to network: {stderr}")
            print(f"Error: Failed to connect to network: {stderr}")
            return
        
        print("Connected successfully!")
        
        # Show connection status
        self._show_network_status(tool)
    
    def _disconnect_network(self, tool: str) -> None:
        """
        Disconnect from current network.

        Args:
            tool: Network management tool to use
        """
        logger.info("Disconnecting from network")
        print("Disconnecting from network...")
        
        if tool == "nmcli":
            cmd = ["nmcli", "device", "disconnect", "wlan0"]
        elif tool == "iwctl":
            cmd = ["iwctl", "station", "wlan0", "disconnect"]
        elif tool == "wpa_cli":
            cmd = ["wpa_cli", "disconnect"]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to disconnect from network: {stderr}")
            print(f"Error: Failed to disconnect from network: {stderr}")
            return
        
        print("Disconnected successfully!")
    
    def _show_network_status(self, tool: str) -> None:
        """
        Show current network status.

        Args:
            tool: Network management tool to use
        """
        logger.info("Showing network status")
        
        if tool == "nmcli":
            cmd = ["nmcli", "device", "status"]
        elif tool == "iwctl":
            cmd = ["iwctl", "station", "wlan0", "show"]
        elif tool == "wpa_cli":
            cmd = ["wpa_cli", "status"]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to get network status: {stderr}")
            print(f"Error: Failed to get network status: {stderr}")
            return
        
        if not stdout.strip():
            print("No network information available.")
            return
        
        print("\nNetwork Status:")
        print(stdout)
    
    def _set_wifi_state(self, tool: str, enable: bool) -> None:
        """
        Enable or disable Wi-Fi.

        Args:
            tool: Network management tool to use
            enable: Whether to enable or disable Wi-Fi
        """
        state_str = "on" if enable else "off"
        logger.info(f"Setting Wi-Fi state to {state_str}")
        print(f"Setting Wi-Fi state to {state_str}...")
        
        if tool == "nmcli":
            cmd = ["nmcli", "radio", "wifi", state_str]
        elif tool == "iwctl":
            # iwctl doesn't have a direct way to enable/disable Wi-Fi
            device = "wlan0"  # Assume default device is wlan0
            if enable:
                cmd = ["rfkill", "unblock", "wifi"]
            else:
                cmd = ["rfkill", "block", "wifi"]
        elif tool == "wpa_cli":
            # wpa_cli also doesn't have a direct way
            if enable:
                cmd = ["rfkill", "unblock", "wifi"]
            else:
                cmd = ["rfkill", "block", "wifi"]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to set Wi-Fi state: {stderr}")
            print(f"Error: Failed to set Wi-Fi state: {stderr}")
            return
        
        print(f"Wi-Fi turned {state_str} successfully!")
    
    def _rescan_networks(self, tool: str) -> None:
        """
        Rescan for available networks.

        Args:
            tool: Network management tool to use
        """
        logger.info("Rescanning for networks")
        print("Rescanning for networks...")
        
        if tool == "nmcli":
            cmd = ["nmcli", "device", "wifi", "rescan"]
        elif tool == "iwctl":
            cmd = ["iwctl", "station", "wlan0", "scan"]
        elif tool == "wpa_cli":
            cmd = ["wpa_cli", "scan"]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to rescan for networks: {stderr}")
            print(f"Error: Failed to rescan for networks: {stderr}")
            return
        
        # Give some time for the scan to complete
        print("Waiting for scan to complete...")
        time.sleep(2)
        print("Scan completed!")