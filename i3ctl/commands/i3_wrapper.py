"""
Wrapper for i3-msg commands.
"""

import json
import contextlib
from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import i3ipc

from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists
from i3ctl.commands.base import BaseCommand


class I3NotFoundError(Exception):
    """Exception raised when i3 is not found on the system."""
    pass


@contextlib.contextmanager
def i3ipc_connection() -> Generator[i3ipc.Connection, None, None]:
    """
    Context manager for i3ipc connection to ensure proper cleanup.
    
    Yields:
        An i3ipc Connection object
    
    Raises:
        I3NotFoundError: If i3 is not running or accessible
    """
    conn = None
    try:
        conn = i3ipc.Connection()
        yield conn
    except Exception as e:
        logger.error(f"Failed to connect to i3: {e}")
        raise I3NotFoundError(f"Could not connect to i3: {e}")
    finally:
        if conn:
            conn.main_quit()


class I3Wrapper:
    """Class for interacting with i3 window manager."""
    
    @staticmethod
    def check_i3() -> bool:
        """
        Check if i3 is running and i3-msg is available.

        Returns:
            True if i3 is available, False otherwise
        """
        return check_command_exists("i3-msg")
    
    @classmethod
    def ensure_i3(cls) -> None:
        """
        Ensure i3 is available, raising an exception if not.
        
        Raises:
            I3NotFoundError: If i3 is not found
        """
        if not cls.check_i3():
            logger.error("i3-msg command not found")
            raise I3NotFoundError("i3-msg command not found. Is i3 installed?")
    
    @classmethod
    def get_i3_version(cls) -> str:
        """
        Get i3 version.

        Returns:
            i3 version string
            
        Raises:
            I3NotFoundError: If i3 is not found
        """
        cls.ensure_i3()
        
        return_code, stdout, stderr = run_command(["i3-msg", "-v"])
        
        if return_code != 0:
            error_msg = f"Failed to get i3 version: {stderr}"
            logger.error(error_msg)
            raise I3NotFoundError(error_msg)
        
        return stdout.strip() if stdout else "Unknown version"
    
    @classmethod
    def i3_command(cls, command: List[str]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Run an i3-msg command.

        Args:
            command: Command to run as a list of strings

        Returns:
            Tuple of (success, result)
            
        Raises:
            I3NotFoundError: If i3 is not found
        """
        cls.ensure_i3()
        
        cmd = ["i3-msg"] + command
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            error_msg = f"i3-msg command failed: {stderr}"
            logger.error(error_msg)
            return False, []
        
        try:
            # i3-msg returns a JSON array
            result = json.loads(stdout) if stdout else []
            return True, result
        except json.JSONDecodeError:
            logger.error(f"Failed to parse i3-msg output: {stdout}")
            return False, []
    
    @classmethod
    def i3_reload(cls) -> bool:
        """
        Reload i3 configuration.

        Returns:
            True if successful, False otherwise
        """
        try:
            success, result = cls.i3_command(["reload"])
            
            if success and result and all(item.get("success", False) for item in result):
                logger.info("i3 configuration reloaded successfully")
                return True
            
            logger.error("Failed to reload i3 configuration")
            return False
        except I3NotFoundError:
            return False
    
    @classmethod
    def i3_restart(cls) -> bool:
        """
        Restart i3.

        Returns:
            True if successful, False otherwise
        """
        try:
            success, result = cls.i3_command(["restart"])
            
            if success and result and all(item.get("success", False) for item in result):
                logger.info("i3 restarted successfully")
                return True
            
            logger.error("Failed to restart i3")
            return False
        except I3NotFoundError:
            return False
    
    @classmethod
    def get_workspaces(cls) -> List[Dict[str, Any]]:
        """
        Get list of i3 workspaces.

        Returns:
            List of workspace information dictionaries
        """
        try:
            # Use i3ipc with context manager for proper cleanup
            with i3ipc_connection() as i3:
                workspaces = i3.get_workspaces()
                return [workspace.__dict__ for workspace in workspaces]
        except Exception as e:
            logger.error(f"Failed to get workspaces using i3ipc: {e}")
            
            try:
                # Fallback to i3-msg
                success, result = cls.i3_command(["get_workspaces"])
                
                if success and result:
                    return result
                
                logger.error("Failed to get workspaces")
            except I3NotFoundError:
                pass
            
            return []
    
    @classmethod
    def get_outputs(cls) -> List[Dict[str, Any]]:
        """
        Get list of i3 outputs.

        Returns:
            List of output information dictionaries
        """
        try:
            success, result = cls.i3_command(["get_outputs"])
            
            if success and result:
                return result
            
            logger.error("Failed to get outputs")
            return []
        except I3NotFoundError:
            return []


class I3Command(BaseCommand):
    """
    Command for interacting with i3 window manager.
    Provides commands to reload, restart, and get information about i3.
    """
    
    def _setup_arguments(self, parser):
        """
        Set up command line arguments.
        
        Args:
            parser: ArgumentParser to configure
        """
        subparsers = parser.add_subparsers(dest="i3_subcommand", help="i3 subcommands")
        
        # Reload command
        reload_parser = subparsers.add_parser("reload", help="Reload i3 configuration")
        
        # Restart command
        restart_parser = subparsers.add_parser("restart", help="Restart i3")
        
        # Version command
        version_parser = subparsers.add_parser("version", help="Get i3 version")
        
        # Workspaces command
        workspaces_parser = subparsers.add_parser("workspaces", help="List i3 workspaces")
        
        # Outputs command
        outputs_parser = subparsers.add_parser("outputs", help="List i3 outputs")
        
        return parser
    
    def handle(self, args):
        """
        Handle i3 commands based on arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Command result
        """
        # Check i3 availability early
        try:
            I3Wrapper.ensure_i3()
        except I3NotFoundError as e:
            logger.error(str(e))
            return 1
        
        if args.i3_subcommand == "reload":
            success = I3Wrapper.i3_reload()
            return 0 if success else 1
        
        elif args.i3_subcommand == "restart":
            success = I3Wrapper.i3_restart()
            return 0 if success else 1
        
        elif args.i3_subcommand == "version":
            try:
                version = I3Wrapper.get_i3_version()
                print(f"i3 version: {version}")
                return 0
            except I3NotFoundError:
                return 1
        
        elif args.i3_subcommand == "workspaces":
            workspaces = I3Wrapper.get_workspaces()
            for workspace in workspaces:
                print(f"Workspace {workspace.get('name', 'Unknown')}: "
                      f"{'Focused' if workspace.get('focused', False) else 'Not focused'}")
            return 0
        
        elif args.i3_subcommand == "outputs":
            outputs = I3Wrapper.get_outputs()
            for output in outputs:
                print(f"Output {output.get('name', 'Unknown')}: "
                      f"{'Active' if output.get('active', False) else 'Not active'}")
            return 0
        
        else:
            # No subcommand specified
            logger.error("No i3 subcommand specified")
            return 1


# Backward compatibility functions that use the class methods
def check_i3() -> bool:
    """Backward compatibility function."""
    return I3Wrapper.check_i3()

def get_i3_version() -> Optional[str]:
    """Backward compatibility function."""
    try:
        return I3Wrapper.get_i3_version()
    except I3NotFoundError:
        return None

def i3_command(command: List[str]) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """Backward compatibility function."""
    try:
        success, result = I3Wrapper.i3_command(command)
        return success, result if result else None
    except I3NotFoundError:
        return False, None

def i3_reload() -> bool:
    """Backward compatibility function."""
    return I3Wrapper.i3_reload()

def i3_restart() -> bool:
    """Backward compatibility function."""
    return I3Wrapper.i3_restart()

def get_workspaces() -> List[Dict[str, Any]]:
    """Backward compatibility function."""
    return I3Wrapper.get_workspaces()

def get_outputs() -> List[Dict[str, Any]]:
    """Backward compatibility function."""
    return I3Wrapper.get_outputs()