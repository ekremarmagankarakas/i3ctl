"""
Main window for the i3ctl GUI application.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
    QSystemTrayIcon, QMenu, QApplication, QMessageBox,
    QDialog
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

import os
import sys
import importlib
from typing import List, Dict, Any, Optional

from i3ctl.cli import execute_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import load_config, save_config
from i3ctl.commands.i3_wrapper import I3Wrapper


class MainWindow(QMainWindow):
    """Main window for the i3ctl GUI application."""
    
    def __init__(self, start_minimized=False):
        super().__init__()
        
        self.setWindowTitle("i3 Control Center")
        self.setMinimumSize(800, 600)
        
        # Try to ensure i3 is available
        try:
            I3Wrapper.ensure_i3()
        except Exception as e:
            logger.warning(f"i3 not found. Some features may not work: {e}")
        
        # Create system tray icon
        self.setup_tray_icon()
        
        # Setup UI
        self.setup_ui()
        
        # Setup menubar
        self.setup_menu()
        
        # Load settings
        self.load_settings()
        
        if start_minimized:
            self.hide()
        
    def setup_ui(self):
        """Setup the main UI components."""
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs for different features
        # Here we'll dynamically load available widgets
        self.add_feature_tabs()
        
        layout.addWidget(self.tabs)
    
    def add_feature_tabs(self):
        """Dynamically add feature tabs based on available widgets."""
        # Define the widgets to load and their tab names
        widget_modules = [
            {"module": "workspace_widget", "class": "WorkspaceWidget", "name": "Workspaces"},
            {"module": "keybind_widget", "class": "KeybindWidget", "name": "Keybindings"},
            {"module": "volume_widget", "class": "VolumeWidget", "name": "Volume"},
            {"module": "brightness_widget", "class": "BrightnessWidget", "name": "Brightness"},
            {"module": "power_widget", "class": "PowerWidget", "name": "Power"},
            {"module": "network_widget", "class": "NetworkWidget", "name": "Network"},
            {"module": "bluetooth_widget", "class": "BluetoothWidget", "name": "Bluetooth"},
            {"module": "bar_widget", "class": "BarWidget", "name": "Bar/Status"}
        ]
        
        # Try to import and add each widget
        for widget_info in widget_modules:
            try:
                module_name = f"i3ctl.gui.widgets.{widget_info['module']}"
                
                # Check if the module file exists
                module_path = module_name.replace('.', '/')
                if not os.path.exists(f"{module_path}.py"):
                    logger.warning(f"Widget module {module_name} not found")
                    # Create a placeholder widget instead
                    self.add_placeholder_tab(widget_info["name"])
                    continue
                
                module = importlib.import_module(module_name)
                widget_class = getattr(module, widget_info["class"])
                widget = widget_class()
                self.tabs.addTab(widget, widget_info["name"])
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not load widget {widget_info['module']}: {e}")
                # Create a placeholder widget instead
                self.add_placeholder_tab(widget_info["name"])
            except Exception as e:
                logger.error(f"Error adding tab {widget_info['name']}: {e}")
                # Create a placeholder widget instead
                self.add_placeholder_tab(widget_info["name"])
    
    def add_placeholder_tab(self, name: str):
        """Add a placeholder tab for features not yet implemented."""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        from PyQt6.QtWidgets import QLabel
        label = QLabel(f"The {name} feature is not yet implemented in the GUI.\n"
                      f"You can use the command line to access this feature:\n\n"
                      f"i3ctl {name.lower()} --help")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        self.tabs.addTab(placeholder, name)
    
    def setup_tray_icon(self):
        """Setup the system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a themed icon if available, otherwise default to system
        icon = QIcon.fromTheme("preferences-system", QIcon.fromTheme("system-run"))
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        
        # Create the tray menu
        tray_menu = QMenu()
        
        # Add menu actions
        restore_action = QAction("Show Window", self)
        restore_action.triggered.connect(self.show)
        restore_action.triggered.connect(self.activateWindow)
        tray_menu.addAction(restore_action)
        
        # Quick actions submenu
        quick_actions = tray_menu.addMenu("Quick Actions")
        
        # Volume actions
        volume_up = QAction("Volume Up", self)
        volume_up.triggered.connect(lambda: self.quick_action(["volume", "up", "5"]))
        quick_actions.addAction(volume_up)
        
        volume_down = QAction("Volume Down", self)
        volume_down.triggered.connect(lambda: self.quick_action(["volume", "down", "5"]))
        quick_actions.addAction(volume_down)
        
        volume_mute = QAction("Volume Mute Toggle", self)
        volume_mute.triggered.connect(lambda: self.quick_action(["volume", "mute"]))
        quick_actions.addAction(volume_mute)
        
        quick_actions.addSeparator()
        
        # Brightness actions
        brightness_up = QAction("Brightness Up", self)
        brightness_up.triggered.connect(lambda: self.quick_action(["brightness", "up", "10"]))
        quick_actions.addAction(brightness_up)
        
        brightness_down = QAction("Brightness Down", self)
        brightness_down.triggered.connect(lambda: self.quick_action(["brightness", "down", "10"]))
        quick_actions.addAction(brightness_down)
        
        # Add separator
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        # Set the tray icon's menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect double click to show window
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show a message when the application starts
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "i3 Control Center", 
                "Application is running in the system tray",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def setup_menu(self):
        """Setup the main menu bar."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        edit_menu = menubar.addMenu("&Edit")
        view_menu = menubar.addMenu("&View")
        help_menu = menubar.addMenu("&Help")
        
        # File menu actions
        reload_action = QAction("&Reload i3 Config", self)
        reload_action.triggered.connect(self.reload_i3_config)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(exit_action)
        
        # Help menu actions
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_settings(self):
        """Load application settings."""
        try:
            config = load_config()
            
            # Get GUI settings
            gui_settings = config.get("gui_settings", {})
            
            # Apply window geometry if saved
            geometry = gui_settings.get("window_geometry")
            if geometry:
                self.restoreGeometry(bytes.fromhex(geometry))
            
            # Apply window state if saved
            state = gui_settings.get("window_state")
            if state:
                self.restoreState(bytes.fromhex(state))
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save application settings."""
        try:
            config = load_config()
            
            # Initialize GUI settings if not present
            if "gui_settings" not in config:
                config["gui_settings"] = {}
            
            # Save window geometry and state
            config["gui_settings"]["window_geometry"] = self.saveGeometry().hex()
            config["gui_settings"]["window_state"] = self.saveState().hex()
            
            save_config(config)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings before closing
        self.save_settings()
        
        # Minimize to tray instead of closing if system tray is available
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            
            self.tray_icon.showMessage(
                "i3 Control Center", 
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # If no system tray, close normally
            event.accept()
    
    def quick_action(self, args):
        """Execute a quick action command."""
        try:
            logger.info(f"Executing quick action: {args}")
            execute_command(args)
        except Exception as e:
            logger.error(f"Error executing quick action: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to execute command: {e}"
            )
    
    def reload_i3_config(self):
        """Reload the i3 configuration."""
        try:
            self.quick_action(["config", "reload"])
            QMessageBox.information(
                self,
                "Success",
                "i3 configuration reloaded successfully."
            )
        except Exception as e:
            logger.error(f"Error reloading i3 config: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to reload i3 configuration: {e}"
            )
    
    def show_settings(self):
        """Show the settings dialog."""
        try:
            from i3ctl.gui.dialogs.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self,
                "Not Implemented",
                "Settings dialog is not yet implemented."
            )
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About i3 Control Center",
            "i3 Control Center\n\n"
            "A graphical user interface for managing i3 window manager settings.\n\n"
            "Version: 0.1.0\n"
            "License: MIT"
        )