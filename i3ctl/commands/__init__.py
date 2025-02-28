"""
Command modules for i3ctl.
"""

from i3ctl.commands.base import BaseCommand

# Command registry for automatic registration
_commands = {}

def register_command(command_class):
    """
    Register a command class with the command registry.
    
    Args:
        command_class: The command class to register
    """
    if not issubclass(command_class, BaseCommand):
        raise ValueError(f"{command_class.__name__} must be a subclass of BaseCommand")
    
    # Register the command
    _commands[command_class.name] = command_class
    return command_class

def get_command_classes():
    """
    Get all registered command classes.
    
    Returns:
        Dictionary of command name to command class
    """
    # Ensure all commands are imported
    from i3ctl.commands.config import ConfigCommand  
    from i3ctl.commands.brightness import BrightnessCommand
    from i3ctl.commands.volume import VolumeCommand
    from i3ctl.commands.wallpaper import WallpaperCommand
    from i3ctl.commands.layout import LayoutCommand
    from i3ctl.commands.startup import StartupCommand
    from i3ctl.commands.power import PowerCommand
    from i3ctl.commands.network import NetworkCommand
    from i3ctl.commands.bluetooth import BluetoothCommand
    from i3ctl.commands.bar import BarCommand
    
    return _commands

__all__ = [
    "BaseCommand",
    "register_command",
    "get_command_classes"
]