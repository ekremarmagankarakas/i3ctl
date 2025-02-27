"""
System utility functions for i3ctl.
"""

import os
import shutil
import subprocess
import asyncio
from typing import List, Optional, Tuple, Dict, Any, Union, Callable

from i3ctl.utils.logger import logger


class CommandNotFoundError(Exception):
    """Exception raised when a required command is not found."""
    pass


class SystemUtils:
    """Class for system utility functions."""
    
    @staticmethod
    def check_command_exists(command: str) -> bool:
        """
        Check if a command exists in the system PATH.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        return shutil.which(command) is not None
    
    @staticmethod
    def require_command(command: str, error_message: Optional[str] = None) -> None:
        """
        Ensure a command exists, raising an exception if not.
        
        Args:
            command: Command name to check
            error_message: Custom error message
            
        Raises:
            CommandNotFoundError: If command is not found
        """
        if not SystemUtils.check_command_exists(command):
            msg = error_message or f"Required command '{command}' not found. Please install it."
            logger.error(msg)
            raise CommandNotFoundError(msg)
    
    @staticmethod
    def run_command(
        command: List[str], 
        capture_output: bool = True,
        check: bool = False,
        timeout: Optional[float] = None,
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Run a system command synchronously.

        Args:
            command: Command to run as a list of strings
            capture_output: Whether to capture stdout and stderr
            check: Whether to raise an exception on non-zero return code
            timeout: Timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        logger.debug(f"Running command: {' '.join(command)}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    text=True,
                    capture_output=True,
                    check=check,
                    timeout=timeout,
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command,
                    text=True,
                    check=check,
                    timeout=timeout,
                )
                return result.returncode, None, None
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return e.returncode, e.stdout, e.stderr
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
            return -1, None, f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return -1, None, str(e)
    
    @staticmethod
    async def run_command_async(
        command: List[str],
        capture_output: bool = True,
        check: bool = False,
        timeout: Optional[float] = None,
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Run a system command asynchronously.

        Args:
            command: Command to run as a list of strings
            capture_output: Whether to capture stdout and stderr
            check: Whether to raise an exception on non-zero return code
            timeout: Timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        logger.debug(f"Running async command: {' '.join(command)}")
        
        try:
            if capture_output:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    text=True,
                )
                
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=timeout
                    )
                    
                    return_code = process.returncode
                    if check and return_code != 0:
                        logger.error(f"Command failed with return code {return_code}: {stderr_bytes}")
                    
                    # Process objects return bytes, so we need to decode
                    stdout = stdout_bytes.decode('utf-8') if stdout_bytes else None
                    stderr = stderr_bytes.decode('utf-8') if stderr_bytes else None
                    
                    return return_code, stdout, stderr
                
                except asyncio.TimeoutError:
                    logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
                    process.kill()
                    return -1, None, f"Command timed out after {timeout} seconds"
            else:
                process = await asyncio.create_subprocess_exec(*command)
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=timeout)
                    return process.returncode, None, None
                
                except asyncio.TimeoutError:
                    logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
                    process.kill()
                    return -1, None, f"Command timed out after {timeout} seconds"
        
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return -1, None, str(e)
    
    @staticmethod
    def detect_tools() -> Dict[str, Dict[str, bool]]:
        """
        Detect available system tools.

        Returns:
            Dict of available tools
        """
        tools = {
            "brightness": {
                "xbacklight": SystemUtils.check_command_exists("xbacklight"),
                "brightnessctl": SystemUtils.check_command_exists("brightnessctl"),
                "light": SystemUtils.check_command_exists("light"),
            },
            "volume": {
                "pulseaudio": SystemUtils.check_command_exists("pactl"),
                "alsa": SystemUtils.check_command_exists("amixer"),
            },
            "wallpaper": {
                "feh": SystemUtils.check_command_exists("feh"),
                "nitrogen": SystemUtils.check_command_exists("nitrogen"),
            },
            "i3": {
                "i3-msg": SystemUtils.check_command_exists("i3-msg"),
                "i3-save-tree": SystemUtils.check_command_exists("i3-save-tree"),
            },
            "editors": {
                "nano": SystemUtils.check_command_exists("nano"),
                "vim": SystemUtils.check_command_exists("vim"),
                "nvim": SystemUtils.check_command_exists("nvim"),
                "emacs": SystemUtils.check_command_exists("emacs"),
            },
            "power": {
                "systemd": SystemUtils.check_command_exists("systemctl"),
                "i3lock": SystemUtils.check_command_exists("i3lock"),
                "xscreensaver": SystemUtils.check_command_exists("xscreensaver-command"),
                "power-profiles-daemon": SystemUtils.check_command_exists("powerprofilesctl"),
                "tlp": SystemUtils.check_command_exists("tlp") and SystemUtils.check_command_exists("tlp-stat"),
            },
            "network": {
                "networkmanager": SystemUtils.check_command_exists("nmcli"),
                "iwd": SystemUtils.check_command_exists("iwctl"),
                "rfkill": SystemUtils.check_command_exists("rfkill"),
            },
            "keyboard": {
                "setxkbmap": SystemUtils.check_command_exists("setxkbmap"),
                "localectl": SystemUtils.check_command_exists("localectl"),
            }
        }
        
        # Add system default editor
        default_editor = os.environ.get("EDITOR")
        if default_editor and SystemUtils.check_command_exists(default_editor):
            if default_editor not in tools["editors"]:
                tools["editors"][default_editor] = True
        
        return tools
    
    @staticmethod
    def get_best_tool(category: str, tools: Optional[Dict[str, Dict[str, bool]]] = None) -> Optional[str]:
        """
        Get the best available tool for a category.
        
        Args:
            category: Tool category (brightness, volume, etc.)
            tools: Predetected tools or None to detect
            
        Returns:
            Name of the best available tool or None if none available
        """
        if tools is None:
            tools = SystemUtils.detect_tools()
            
        if category not in tools:
            logger.error(f"Unknown tool category: {category}")
            return None
            
        category_tools = tools[category]
        for tool_name, available in category_tools.items():
            if available:
                return tool_name
                
        return None
    
    @classmethod
    def with_fallbacks(cls, 
                       commands: List[Tuple[str, Callable[..., Any]]], 
                       error_message: str = "All commands failed") -> Any:
        """
        Try multiple commands with fallbacks.
        
        Args:
            commands: List of (name, function) tuples to try
            error_message: Message to log if all commands fail
            
        Returns:
            Result of the first successful command or None if all fail
        """
        for name, func in commands:
            if cls.check_command_exists(name):
                try:
                    return func()
                except Exception as e:
                    logger.warning(f"Command {name} failed: {e}")
        
        logger.error(error_message)
        return None


# Backward compatibility functions
def check_command_exists(command: str) -> bool:
    """Backward compatibility function."""
    return SystemUtils.check_command_exists(command)

def run_command(
    command: List[str], 
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[float] = None,
    capture_stderr: bool = True,  # Added parameter for backwards compatibility
) -> Tuple[int, Optional[str], Optional[str]]:
    """Backward compatibility function."""
    # The capture_stderr parameter is ignored since we always capture stderr
    # when capture_output is True in the new implementation
    return SystemUtils.run_command(command, capture_output, check, timeout)

def detect_tools() -> Dict[str, Dict[str, bool]]:
    """Backward compatibility function."""
    return SystemUtils.detect_tools()