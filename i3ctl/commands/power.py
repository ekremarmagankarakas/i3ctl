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
        
        # Power profile command
        profile_parser = subparsers.add_parser("profile", help="Set or view power profile")
        profile_parser.add_argument(
            "mode", 
            nargs="?",
            choices=["performance", "balanced", "power-saver", "auto"],
            help="Power profile mode (omit to show current profile)"
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
        elif args.subcommand == "profile":
            self._manage_power_profile(args.mode)
            
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
        
        # Power profile (checks for ppd, tlp, and CPU governor)
        ppd_available = check_command_exists("powerprofilesctl")
        tlp_available = check_command_exists("tlp-stat") and check_command_exists("tlp")
        cpu_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        cpu_control_available = os.path.exists(cpu_path)
        
        self._show_power_profile(ppd_available, tlp_available, cpu_control_available)
    
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
        
    def _manage_power_profile(self, mode: Optional[str] = None) -> None:
        """
        Set or display power profile.

        Args:
            mode: Power profile mode to set, or None to show current profile
        """
        # First check if power-profiles-daemon is available (modern approach)
        ppd_available = check_command_exists("powerprofilesctl")
        
        # Then check for TLP (common power management tool)
        tlp_available = check_command_exists("tlp-stat") and check_command_exists("tlp")
        
        # Finally check direct CPU control
        cpu_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        cpu_control_available = os.path.exists(cpu_path)
        
        if not mode:
            # Just display current profile
            self._show_power_profile(ppd_available, tlp_available, cpu_control_available)
            return
            
        # Set the requested profile
        if ppd_available:
            # Map our modes to power-profiles-daemon modes
            mode_map = {
                "performance": "performance",
                "balanced": "balanced",
                "power-saver": "power-saver",
                "auto": "balanced"  # Default to balanced for auto
            }
            
            ppd_mode = mode_map.get(mode, "balanced")
            logger.info(f"Setting power profile to {ppd_mode} using power-profiles-daemon")
            print(f"Setting power profile to {ppd_mode}...")
            
            return_code, stdout, stderr = run_command(["powerprofilesctl", "set", ppd_mode])
            
            if return_code != 0:
                logger.error(f"Failed to set power profile: {stderr}")
                print(f"Error: Failed to set power profile: {stderr}")
                # Fall through to try other methods
            else:
                print(f"Power profile set to {ppd_mode}")
                return
                
        elif tlp_available:
            # Map our modes to TLP profiles
            if mode == "performance":
                tlp_cmd = ["tlp", "ac"]
                print("Setting high-performance power profile (AC mode)...")
            elif mode == "power-saver":
                tlp_cmd = ["tlp", "bat"]
                print("Setting power-saving profile (battery mode)...")
            else:  # balanced or auto
                tlp_cmd = ["tlp", "start"]
                print("Setting balanced power profile...")
                
            return_code, stdout, stderr = run_command(tlp_cmd)
            
            if return_code != 0:
                logger.error(f"Failed to set TLP profile: {stderr}")
                print(f"Error: Failed to set TLP profile: {stderr}")
                # Fall through to try other methods
            else:
                print("Power profile updated successfully")
                return
                
        elif cpu_control_available:
            # Map our modes to CPU governors
            governor_map = {
                "performance": "performance",
                "balanced": "ondemand",
                "power-saver": "powersave",
                "auto": "ondemand"  # Default to ondemand for auto
            }
            
            governor = governor_map.get(mode, "ondemand")
            logger.info(f"Setting CPU governor to {governor}")
            print(f"Setting CPU governor to {governor}...")
            
            # Get all available CPU cores
            cpu_cores = []
            cpu_dir = "/sys/devices/system/cpu"
            for entry in os.listdir(cpu_dir):
                if entry.startswith("cpu") and entry[3:].isdigit():
                    cpu_cores.append(entry)
            
            if not cpu_cores:
                logger.error("No CPU cores found")
                print("Error: No CPU cores found")
                return
                
            # Set governor for each core
            success = True
            for core in cpu_cores:
                governor_path = f"{cpu_dir}/{core}/cpufreq/scaling_governor"
                if os.path.exists(governor_path):
                    try:
                        with open(governor_path, "w") as f:
                            f.write(governor)
                    except (IOError, PermissionError) as e:
                        logger.error(f"Failed to set governor for {core}: {e}")
                        print(f"Error: Insufficient permissions to change CPU governor")
                        print("Try running with sudo or adjust permissions")
                        success = False
                        break
            
            if success:
                print(f"CPU governor set to {governor} for all cores")
            return
            
        else:
            logger.error("No power profile control methods available")
            print("Error: No power profile control methods available")
            print("Please install power-profiles-daemon, TLP, or ensure CPU governor control is accessible")
            
    def _show_power_profile(self, ppd_available: bool, tlp_available: bool, cpu_control_available: bool) -> None:
        """
        Show current power profile information.
        
        Args:
            ppd_available: Whether power-profiles-daemon is available
            tlp_available: Whether TLP is available
            cpu_control_available: Whether direct CPU control is available
        """
        print("\nPower Profile:")
        
        # Try power-profiles-daemon first
        if ppd_available:
            return_code, stdout, stderr = run_command(["powerprofilesctl", "get"])
            
            if return_code == 0 and stdout:
                print(f"  Current profile: {stdout.strip()}")
                # Also show available profiles
                return_code, stdout, stderr = run_command(["powerprofilesctl", "list"])
                if return_code == 0 and stdout:
                    print("  Available profiles:")
                    for line in stdout.strip().split("\n"):
                        if "*" in line:  # Active profile
                            print(f"    {line.strip()}")
                        elif line.strip() and not line.strip().startswith("Available"):
                            print(f"    {line.strip()}")
                return
                
        # Try TLP
        if tlp_available:
            return_code, stdout, stderr = run_command(["tlp-stat", "-s"])
            
            if return_code == 0 and stdout:
                tlp_mode = None
                for line in stdout.strip().split("\n"):
                    if "Mode:" in line:
                        tlp_mode = line.strip()
                        break
                
                if tlp_mode:
                    print(f"  TLP {tlp_mode}")
                    return
                    
        # Fall back to CPU governor
        if cpu_control_available:
            governors = set()
            cpu_dir = "/sys/devices/system/cpu"
            
            for entry in os.listdir(cpu_dir):
                if entry.startswith("cpu") and entry[3:].isdigit():
                    governor_path = f"{cpu_dir}/{entry}/cpufreq/scaling_governor"
                    if os.path.exists(governor_path):
                        try:
                            with open(governor_path, "r") as f:
                                governors.add(f.read().strip())
                        except IOError:
                            pass
            
            if governors:
                if len(governors) == 1:
                    governor = next(iter(governors))
                    print(f"  CPU Governor: {governor}")
                    
                    # Map governor to profile name for clarity
                    profile_map = {
                        "performance": "Performance",
                        "powersave": "Power Saver",
                        "ondemand": "Balanced (Dynamic)",
                        "conservative": "Balanced (Conservative)",
                        "schedutil": "Scheduler Based"
                    }
                    
                    profile = profile_map.get(governor, "Unknown")
                    print(f"  Profile: {profile}")
                else:
                    print(f"  CPU Governors: {', '.join(governors)} (mixed)")
                return
                
        print("  No power profile information available")
        print("  To control power profiles, install power-profiles-daemon or TLP")