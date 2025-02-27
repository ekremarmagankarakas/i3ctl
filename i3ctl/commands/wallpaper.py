"""
Wallpaper management commands.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_config_value, load_config, save_config
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class WallpaperCommand(BaseCommand):
    """
    Command for managing desktop wallpaper.
    """

    name = "wallpaper"
    help = "Manage desktop wallpaper"

    def __init__(self) -> None:
        """
        Initialize command.
        """
        super().__init__()
        self._wallpaper_handlers = {
            "feh": self._use_feh,
            "nitrogen": self._use_nitrogen,
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
        # Set wallpaper from path
        self.parser.add_argument(
            "path", 
            nargs="?",
            help="Path to wallpaper image"
        )
        
        # List saved wallpapers
        self.parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="List saved wallpaper history"
        )
        
        # Random wallpaper from a directory
        self.parser.add_argument(
            "--random", "-r",
            action="store_true",
            help="Set random wallpaper from a directory"
        )
        
        # Restore last wallpaper
        self.parser.add_argument(
            "--restore", "-R",
            action="store_true",
            help="Restore last wallpaper"
        )
        
        # Specific wallpaper tool
        self.parser.add_argument(
            "--tool", "-t",
            choices=list(self._wallpaper_handlers.keys()),
            help="Specific wallpaper tool to use"
        )
        
        # Specify scaling mode
        self.parser.add_argument(
            "--mode", "-m",
            choices=["fill", "center", "tile", "scale", "max"],
            default="fill",
            help="Wallpaper scaling mode (default: fill)"
        )

    def handle(self, args: argparse.Namespace) -> int:
        """
        Handle command execution.

        Args:
            args: Command arguments
            
        Returns:
            Exit code
        """
        # Get wallpaper tool from args, config, or auto-detect
        tool = args.tool or get_config_value("wallpaper_tool", "auto")
        
        if tool == "auto":
            tool = self._detect_wallpaper_tool()
            if not tool:
                print("Error: No wallpaper tool found.")
                print("Please install feh or nitrogen.")
                return 1
        elif tool not in self._wallpaper_handlers:
            logger.error(f"Unsupported wallpaper tool: {tool}")
            print(f"Error: Unsupported wallpaper tool: {tool}")
            print(f"Supported tools: {', '.join(self._wallpaper_handlers.keys())}")
            return 1
        
        logger.info(f"Using wallpaper tool: {tool}")
        
        # Call appropriate handler for the tool
        handler = self._wallpaper_handlers[tool]
        
        if args.list:
            self._list_wallpapers()
        elif args.restore:
            self._restore_wallpaper(handler, args.mode)
        elif args.random:
            path = args.path or get_config_value("wallpaper_directory", os.path.expanduser("~/Pictures"))
            self._set_random_wallpaper(handler, path, args.mode)
        elif args.path:
            self._set_wallpaper(handler, args.path, args.mode)
        else:
            # No action specified, show help
            self.parser.print_help()
        
        return 0
    
    def _detect_wallpaper_tool(self) -> Optional[str]:
        """
        Detect available wallpaper tool.

        Returns:
            Name of detected tool or None if no tool is found
        """
        for tool in self._wallpaper_handlers.keys():
            if check_command_exists(tool):
                logger.info(f"Detected wallpaper tool: {tool}")
                return tool
        
        logger.error("No wallpaper tool found")
        return None
    
    def _set_wallpaper(self, handler: callable, path: str, mode: str) -> None:
        """
        Set wallpaper using the given handler.

        Args:
            handler: Wallpaper handler function
            path: Path to wallpaper image
            mode: Scaling mode
        """
        # Expand path if needed
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            logger.error(f"Wallpaper file not found: {path}")
            print(f"Error: Wallpaper file not found: {path}")
            return
        
        # Check if file is an image
        if not self._is_image_file(path):
            logger.error(f"File is not a recognized image format: {path}")
            print(f"Error: File is not a recognized image format: {path}")
            return
        
        # Set wallpaper
        handler(path, mode)
        
        # Save to history
        self._save_wallpaper_history(path)
    
    def _restore_wallpaper(self, handler: callable, mode: str) -> None:
        """
        Restore the last wallpaper.

        Args:
            handler: Wallpaper handler function
            mode: Scaling mode
        """
        # Get last wallpaper from history
        config = load_config()
        history = config.get("wallpaper_history", [])
        
        if not history:
            logger.warning("No wallpaper history found")
            print("No wallpaper history found.")
            return
        
        last_wallpaper = history[0]
        
        if not os.path.exists(last_wallpaper):
            logger.error(f"Last wallpaper not found: {last_wallpaper}")
            print(f"Error: Last wallpaper not found: {last_wallpaper}")
            return
        
        logger.info(f"Restoring wallpaper: {last_wallpaper}")
        print(f"Restoring wallpaper: {last_wallpaper}")
        
        # Set wallpaper
        handler(last_wallpaper, mode)
    
    def _list_wallpapers(self) -> None:
        """
        List saved wallpaper history.
        """
        config = load_config()
        history = config.get("wallpaper_history", [])
        
        if not history:
            print("No wallpaper history found.")
            return
        
        print("Wallpaper History:")
        for i, path in enumerate(history):
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"{i+1}. {exists} {path}")
    
    def _set_random_wallpaper(self, handler: callable, directory: str, mode: str) -> None:
        """
        Set a random wallpaper from the given directory.

        Args:
            handler: Wallpaper handler function
            directory: Directory containing wallpapers
            mode: Scaling mode
        """
        directory = os.path.expanduser(directory)
        
        if not os.path.isdir(directory):
            logger.error(f"Directory not found: {directory}")
            print(f"Error: Directory not found: {directory}")
            return
        
        # Find all image files in directory
        image_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if self._is_image_file(file):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            logger.error(f"No image files found in {directory}")
            print(f"Error: No image files found in {directory}")
            return
        
        # Choose random image
        import random
        random_image = random.choice(image_files)
        
        logger.info(f"Selected random wallpaper: {random_image}")
        print(f"Selected random wallpaper: {random_image}")
        
        # Set wallpaper
        self._set_wallpaper(handler, random_image, mode)
    
    def _save_wallpaper_history(self, path: str) -> None:
        """
        Save wallpaper to history.

        Args:
            path: Path to wallpaper
        """
        config = load_config()
        
        # Get current history or create new one
        history = config.get("wallpaper_history", [])
        
        # Remove path if already in history
        if path in history:
            history.remove(path)
        
        # Add to front of history
        history.insert(0, path)
        
        # Keep only the last 10 wallpapers
        history = history[:10]
        
        # Save updated history
        config["wallpaper_history"] = history
        save_config(config)
    
    def _is_image_file(self, path: str) -> bool:
        """
        Check if file is an image.

        Args:
            path: Path to file

        Returns:
            True if file is an image, False otherwise
        """
        image_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", 
            ".tiff", ".webp", ".svg"
        ]
        
        extension = os.path.splitext(path)[1].lower()
        return extension in image_extensions
    
    def _use_feh(self, path: str, mode: str) -> None:
        """
        Set wallpaper using feh.

        Args:
            path: Path to wallpaper image
            mode: Scaling mode
        """
        # Map mode to feh options
        mode_mapping = {
            "fill": "--bg-fill",
            "center": "--bg-center",
            "tile": "--bg-tile",
            "scale": "--bg-scale",
            "max": "--bg-max",
        }
        
        feh_mode = mode_mapping.get(mode, "--bg-fill")
        
        cmd = ["feh", feh_mode, path]
        msg = f"Setting wallpaper with feh: {path}"
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"feh command failed: {stderr}")
            print(f"Error: {stderr}")
            return
        
        print("Wallpaper set successfully.")
    
    def _use_nitrogen(self, path: str, mode: str) -> None:
        """
        Set wallpaper using nitrogen.

        Args:
            path: Path to wallpaper image
            mode: Scaling mode
        """
        # Map mode to nitrogen options
        mode_mapping = {
            "fill": "zoom-fill",
            "center": "centered",
            "tile": "tiled",
            "scale": "scaled",
            "max": "zoomed",
        }
        
        nitrogen_mode = mode_mapping.get(mode, "zoom-fill")
        
        cmd = ["nitrogen", "--set-zoom-fill", "--save", path]
        msg = f"Setting wallpaper with nitrogen: {path}"
        
        # If not zoom-fill, use the appropriate mode
        if nitrogen_mode != "zoom-fill":
            cmd = ["nitrogen", f"--set-{nitrogen_mode}", "--save", path]
        
        logger.info(msg)
        print(msg)
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"nitrogen command failed: {stderr}")
            print(f"Error: {stderr}")
            return
        
        print("Wallpaper set successfully.")