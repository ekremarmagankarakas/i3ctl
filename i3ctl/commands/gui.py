"""
GUI launcher for i3ctl.
"""

import argparse
import sys
from typing import Any, Optional

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger


@register_command
class GuiCommand(BaseCommand):
    """
    Launch the i3ctl GUI.
    """

    name = "gui"
    help = "Launch the graphical user interface"

    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Set up command arguments.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        parser.add_argument(
            "--minimized", "-m",
            action="store_true",
            help="Start minimized to system tray"
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
        try:
            # Try to import PyQt6
            try:
                from PyQt6.QtWidgets import QApplication
                from i3ctl.gui.main_window import MainWindow
            except ImportError:
                logger.error("PyQt6 is not installed")
                print("Error: PyQt6 is not installed. Please install it with: pip install PyQt6")
                return 1
            
            logger.info("Starting i3ctl GUI")
            
            # Create QApplication instance
            app = QApplication(sys.argv)
            app.setApplicationName("i3ctl")
            app.setApplicationDisplayName("i3 Control Center")
            
            # Create and show main window
            window = MainWindow(start_minimized=args.minimized)
            
            if not args.minimized:
                window.show()
            
            # Run the application
            return app.exec()
            
        except Exception as e:
            logger.error(f"Error starting GUI: {e}")
            print(f"Error: Failed to start GUI: {e}")
            return 1