"""
Power management commands.
"""

import argparse
import os
import sys
import time
from typing import Dict, List, Optional

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class PowerCommand(BaseCommand):
    """
    Command for power management.
    """

    name = "power"
    help = "Manage system power"

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
        
        # Power off command
        off_parser = subparsers.add_parser("off", help="Power off the system")
        off_parser.add_argument(
            "--now", "-n",
            action="store_true",
            help="Power off immediately without confirmation"
        )
        off_parser.add_argument(
            "--time", "-t",
            type=int,
            default=0,
            help="Schedule power off after specified minutes"
        )
        
        # Reboot command
        reboot_parser = subparsers.add_parser("reboot", help="Reboot the system")
        reboot_parser.add_argument(
            "--now", "-n",
            action="store_true",
            help="Reboot immediately without confirmation"
        )
        
        # Suspend command
        suspend_parser = subparsers.add_parser("suspend", help="Suspend the system")
        suspend_parser.add_argument(
            "--now", "-n",
            action="store_true",
            help="Suspend immediately without confirmation"
        )
        
        # Hibernate command
        hibernate_parser = subparsers.add_parser("hibernate", help="Hibernate the system")
        hibernate_parser.add_argument(
            "--now", "-n",
            action="store_true",
            help="Hibernate immediately without confirmation"
        )
        
        # Hybrid sleep command
        hybrid_sleep_parser = subparsers.add_parser("hybrid-sleep", help="Hybrid sleep the system")
        hybrid_sleep_parser.add_argument(
            "--now", "-n",
            action="store_true",
            help="Hybrid sleep immediately without confirmation"
        )
        
        # Lock screen command
        lock_parser = subparsers.add_parser("lock", help="Lock the screen")
        
        # Show power status command
        status_parser = subparsers.add_parser("status", help="Show power status")
        
        # Cancel scheduled power off command
        cancel_parser = subparsers.add_parser("cancel", help="Cancel scheduled power off")

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
        
        # Handle subcommands
        if args.subcommand == "off":
            self._power_off(args.now, args.time)
        elif args.subcommand == "reboot":
            self._reboot(args.now)
        elif args.subcommand == "suspend":
            self._suspend(args.now)
        elif args.subcommand == "hibernate":
            self._hibernate(args.now)
        elif args.subcommand == "hybrid-sleep":
            self._hybrid_sleep(args.now)
        elif args.subcommand == "lock":
            self._lock_screen()
        elif args.subcommand == "status":
            self._show_power_status()
        elif args.subcommand == "cancel":
            self._cancel_scheduled_power_off()
            
        return 0
    
    def _power_off(self, now: bool = False, wait_time: int = 0) -> None:
        """
        Power off the system.

        Args:
            now: Whether to power off immediately without confirmation
            wait_time: Time in minutes to wait before powering off
        """
        if wait_time > 0:
            # Schedule power off
            return self._schedule_power_off(wait_time)
        
        if not now:
            # Prompt for confirmation
            print("Are you sure you want to power off the system? (y/n) ", end="")
            response = input().strip().lower()
            
            if response not in ["y", "yes"]:
                print("Power off cancelled.")
                return
        
        logger.info("Powering off the system")
        print("Powering off the system...")
        
        # Check if we have systemctl
        if check_command_exists("systemctl"):
            run_command(["systemctl", "poweroff"])
        else:
            # Fallback to traditional commands
            run_command(["sudo", "shutdown", "-h", "now"])
    
    def _reboot(self, now: bool = False) -> None:
        """
        Reboot the system.

        Args:
            now: Whether to reboot immediately without confirmation
        """
        if not now:
            # Prompt for confirmation
            print("Are you sure you want to reboot the system? (y/n) ", end="")
            response = input().strip().lower()
            
            if response not in ["y", "yes"]:
                print("Reboot cancelled.")
                return
        
        logger.info("Rebooting the system")
        print("Rebooting the system...")
        
        # Check if we have systemctl
        if check_command_exists("systemctl"):
            run_command(["systemctl", "reboot"])
        else:
            # Fallback to traditional commands
            run_command(["sudo", "shutdown", "-r", "now"])
    
    def _suspend(self, now: bool = False) -> None:
        """
        Suspend the system.

        Args:
            now: Whether to suspend immediately without confirmation
        """
        if not now:
            # Prompt for confirmation
            print("Are you sure you want to suspend the system? (y/n) ", end="")
            response = input().strip().lower()
            
            if response not in ["y", "yes"]:
                print("Suspend cancelled.")
                return
        
        logger.info("Suspending the system")
        print("Suspending the system...")
        
        # Check if we have systemctl
        if check_command_exists("systemctl"):
            run_command(["systemctl", "suspend"])
        else:
            # Fallback to traditional commands
            run_command(["sudo", "pm-suspend"])
    
    def _hibernate(self, now: bool = False) -> None:
        """
        Hibernate the system.

        Args:
            now: Whether to hibernate immediately without confirmation
        """
        if not now:
            # Prompt for confirmation
            print("Are you sure you want to hibernate the system? (y/n) ", end="")
            response = input().strip().lower()
            
            if response not in ["y", "yes"]:
                print("Hibernate cancelled.")
                return
        
        logger.info("Hibernating the system")
        print("Hibernating the system...")
        
        # Check if we have systemctl
        if check_command_exists("systemctl"):
            run_command(["systemctl", "hibernate"])
        else:
            # Fallback to traditional commands
            run_command(["sudo", "pm-hibernate"])
    
    def _hybrid_sleep(self, now: bool = False) -> None:
        """
        Hybrid sleep the system.

        Args:
            now: Whether to hybrid sleep immediately without confirmation
        """
        if not now:
            # Prompt for confirmation
            print("Are you sure you want to hybrid sleep the system? (y/n) ", end="")
            response = input().strip().lower()
            
            if response not in ["y", "yes"]:
                print("Hybrid sleep cancelled.")
                return
        
        logger.info("Hybrid sleeping the system")
        print("Hybrid sleeping the system...")
        
        # Check if we have systemctl
        if check_command_exists("systemctl"):
            run_command(["systemctl", "hybrid-sleep"])
        else:
            # Fallback to traditional commands
            run_command(["sudo", "pm-suspend-hybrid"])
    
    def _lock_screen(self) -> None:
        """
        Lock the screen.
        """
        logger.info("Locking the screen")
        print("Locking the screen...")
        
        # Try multiple lock methods in order of preference
        lock_methods = [
            ["i3lock"],
            ["xscreensaver-command", "-lock"],
            ["gnome-screensaver-command", "--lock"],
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"]
        ]
        
        for lock_cmd in lock_methods:
            if check_command_exists(lock_cmd[0]):
                run_command(lock_cmd)
                return
        
        logger.error("No screen lock command found")
        print("Error: No screen lock command found.")
        print("Please install i3lock, xscreensaver, or gnome-screensaver.")
    
    def _schedule_power_off(self, minutes: int) -> None:
        """
        Schedule power off after a specified time.

        Args:
            minutes: Minutes to wait before powering off
        """
        if minutes <= 0:
            print("Error: Time must be greater than 0 minutes.")
            return
        
        logger.info(f"Scheduling power off in {minutes} minutes")
        print(f"Scheduling power off in {minutes} minutes...")
        
        # Check if we have systemctl
        if check_command_exists("shutdown"):
            run_command(["sudo", "shutdown", "-h", f"+{minutes}"])
            print(f"System will power off at {self._get_shutdown_time(minutes)}.")
            print("Run 'i3ctl power cancel' to cancel the scheduled power off.")
        elif check_command_exists("at"):
            # Try to use the 'at' command as a fallback
            time_str = f"now + {minutes} minutes"
            process = subprocess.Popen(
                ["at", time_str],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.stdin.write(b"systemctl poweroff\n")
            process.stdin.close()
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print(f"System will power off at {self._get_shutdown_time(minutes)}.")
                print("Run 'i3ctl power cancel' to cancel the scheduled power off.")
            else:
                logger.error(f"Failed to schedule power off: {stderr.decode()}")
                print(f"Error: Failed to schedule power off: {stderr.decode()}")
        else:
            logger.error("No command found to schedule power off")
            print("Error: No command found to schedule power off.")
            print("Please install 'at' or make sure 'shutdown' is available.")
    
    def _cancel_scheduled_power_off(self) -> None:
        """
        Cancel a scheduled power off.
        """
        logger.info("Cancelling scheduled power off")
        print("Cancelling scheduled power off...")
        
        # Check if we have systemctl
        if check_command_exists("shutdown"):
            run_command(["sudo", "shutdown", "-c"])
            print("Scheduled power off has been cancelled.")
        elif check_command_exists("at"):
            # Try to use the 'at' command as a fallback
            # This is tricky since we need to find the job ID
            run_command(["atq"])
            print("Please use 'atrm <job_id>' to remove the scheduled job.")
        else:
            logger.error("No command found to cancel scheduled power off")
            print("Error: No command found to cancel scheduled power off.")
            print("Please install 'at' or make sure 'shutdown' is available.")
    
    def _show_power_status(self) -> None:
        """
        Show power status.
        """
        print("Power Status:")
        
        # Battery status
        self._show_battery_status()
        
        # Scheduled shutdowns
        self._show_scheduled_shutdowns()
        
        # CPU frequency and governor
        self._show_cpu_info()
    
    def _show_battery_status(self) -> None:
        """
        Show battery status.
        """
        # Check if we have the battery
        battery_path = "/sys/class/power_supply/BAT0"
        if not os.path.exists(battery_path):
            battery_path = "/sys/class/power_supply/BAT1"
            if not os.path.exists(battery_path):
                print("  Battery: Not found")
                return
        
        # Read battery status
        try:
            with open(f"{battery_path}/status", "r") as f:
                status = f.read().strip()
            
            with open(f"{battery_path}/capacity", "r") as f:
                capacity = int(f.read().strip())
            
            # Get charging status
            is_charging = status == "Charging"
            is_discharging = status == "Discharging"
            
            # Get remaining time if available
            remaining_time = "Unknown"
            if os.path.exists(f"{battery_path}/current_now") and is_discharging:
                with open(f"{battery_path}/current_now", "r") as f:
                    current = int(f.read().strip()) / 1000000  # µA to A
                
                with open(f"{battery_path}/energy_now", "r") as f:
                    energy = int(f.read().strip()) / 1000000  # µWh to Wh
                
                if current > 0:
                    hours = energy / current
                    minutes = int((hours - int(hours)) * 60)
                    remaining_time = f"{int(hours)}h {minutes}m"
            
            # Format the output
            status_str = "Charging" if is_charging else "Discharging" if is_discharging else status
            print(f"  Battery: {capacity}% ({status_str})")
            
            if is_discharging:
                print(f"  Remaining time: {remaining_time}")
            
        except Exception as e:
            logger.error(f"Failed to read battery status: {e}")
            print("  Battery: Error reading status")
    
    def _show_scheduled_shutdowns(self) -> None:
        """
        Show scheduled shutdowns.
        """
        # Check if there's a scheduled shutdown
        if check_command_exists("shutdown"):
            return_code, stdout, stderr = run_command(["shutdown", "-c"], capture_stderr=True)
            
            if "No scheduled shutdown" not in stderr:
                # Extract scheduled shutdown time
                import re
                match = re.search(r"Shutdown scheduled for (.*)", stderr)
                if match:
                    time_str = match.group(1)
                    print(f"  Scheduled shutdown: {time_str}")
                    return
        
        print("  Scheduled shutdown: None")
    
    def _show_cpu_info(self) -> None:
        """
        Show CPU frequency and governor.
        """
        # Check if we have the cpufreq files
        cpu_path = "/sys/devices/system/cpu/cpu0/cpufreq"
        if not os.path.exists(cpu_path):
            print("  CPU governor: Unknown")
            return
        
        # Read CPU governor
        try:
            with open(f"{cpu_path}/scaling_governor", "r") as f:
                governor = f.read().strip()
            
            with open(f"{cpu_path}/scaling_cur_freq", "r") as f:
                freq = int(f.read().strip()) / 1000  # kHz to MHz
            
            print(f"  CPU governor: {governor}")
            print(f"  CPU frequency: {freq:.0f} MHz")
            
        except Exception as e:
            logger.error(f"Failed to read CPU info: {e}")
            print("  CPU info: Error reading status")
    
    def _get_shutdown_time(self, minutes: int) -> str:
        """
        Get the shutdown time as a string.

        Args:
            minutes: Minutes from now

        Returns:
            Time string
        """
        import datetime
        shutdown_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        return shutdown_time.strftime("%H:%M")