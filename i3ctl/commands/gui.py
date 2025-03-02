"""
GUI launcher for i3ctl.
"""

import argparse
import os
import signal
import sys
import time
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
            
            # Set up signal handler for Ctrl+C
            def signal_handler(sig, frame):
                logger.info("Received interrupt signal, shutting down...")
                app.exit(0)  # Force immediate exit
                
            # Install signal handlers
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Enable basic application attributes
            # Note: HiDPI scaling is enabled automatically in PyQt6
            
            # Create and show main window
            window = MainWindow(start_minimized=args.minimized)
            
            if not args.minimized:
                window.show()
            
            # Run the application with signal handling
            try:
                # Use a custom event loop to better handle terminal signals
                from PyQt6.QtCore import QEventLoop, QTimer
                
                # Create an event loop
                event_loop = QEventLoop()
                
                # Setup a timer to allow interrupts to be processed
                def check_and_process():
                    # Check if we should continue
                    if not app.topLevelWidgets() or not any(w.isVisible() for w in app.topLevelWidgets() if w.isWindow()):
                        event_loop.quit()  # All windows closed
                
                # Create a timer that periodically checks for interrupt signals
                interrupt_timer = QTimer()
                interrupt_timer.timeout.connect(check_and_process)
                interrupt_timer.start(100)  # Check every 100ms
                
                # Run event loop, but allow keyboard interrupts
                try:
                    event_loop.exec()
                    return 0  # Normal exit
                except KeyboardInterrupt:
                    # Handle keyboard interrupt
                    logger.info("KeyboardInterrupt received, shutting down...")
                    app.quit()
                    return 130
            except KeyboardInterrupt:
                # Fallback KeyboardInterrupt handler
                logger.info("KeyboardInterrupt received during setup, shutting down...")
                app.quit()
                return 130  # Standard exit code for Ctrl+C
            
        except Exception as e:
            logger.error(f"Error starting GUI: {e}")
            print(f"Error: Failed to start GUI: {e}")
            return 1