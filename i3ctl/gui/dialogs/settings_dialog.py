"""
Settings dialog for the i3ctl GUI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QCheckBox, QComboBox, QFormLayout,
    QTabWidget, QWidget, QGroupBox, QDialogButtonBox, QSpinBox
)
from PyQt6.QtCore import Qt

from i3ctl.utils.logger import logger
from i3ctl.utils.config import load_config, save_config, CONFIG_DIR


class SettingsDialog(QDialog):
    """Settings dialog for the i3ctl GUI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("i3ctl Settings")
        self.resize(600, 400)
        
        # Load current settings
        self.config = load_config()
        
        # Setup UI
        self.setup_ui()
        
        # Load settings into UI
        self.load_settings()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # i3 settings group
        i3_group = QGroupBox("i3 Settings")
        i3_form = QFormLayout(i3_group)
        
        self.i3_config_path = QLineEdit()
        i3_form.addRow("i3 config path:", self.i3_config_path)
        
        general_layout.addWidget(i3_group)
        
        # Editor settings group
        editor_group = QGroupBox("Editor")
        editor_form = QFormLayout(editor_group)
        
        self.editor = QLineEdit()
        editor_form.addRow("Default editor:", self.editor)
        
        general_layout.addWidget(editor_group)
        
        # GUI settings group
        gui_group = QGroupBox("GUI Settings")
        gui_form = QFormLayout(gui_group)
        
        self.start_minimized = QCheckBox("Start minimized to tray")
        gui_form.addRow("", self.start_minimized)
        
        self.minimize_on_close = QCheckBox("Minimize to tray on close")
        gui_form.addRow("", self.minimize_on_close)
        
        general_layout.addWidget(gui_group)
        
        # Add tabs
        self.tabs.addTab(general_tab, "General")
        
        # Add feature-specific settings tabs
        self.add_feature_tabs()
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def add_feature_tabs(self):
        """Add tabs for feature-specific settings."""
        # Example for volume settings
        volume_tab = QWidget()
        volume_layout = QVBoxLayout(volume_tab)
        
        volume_group = QGroupBox("Volume Control")
        volume_form = QFormLayout(volume_group)
        
        self.volume_step = QSpinBox()
        self.volume_step.setRange(1, 20)
        volume_form.addRow("Default step size:", self.volume_step)
        
        self.volume_tool = QComboBox()
        self.volume_tool.addItems(["auto", "pulseaudio", "alsa"])
        volume_form.addRow("Volume tool:", self.volume_tool)
        
        volume_layout.addWidget(volume_group)
        self.tabs.addTab(volume_tab, "Volume")
        
        # Example for brightness settings
        brightness_tab = QWidget()
        brightness_layout = QVBoxLayout(brightness_tab)
        
        brightness_group = QGroupBox("Brightness Control")
        brightness_form = QFormLayout(brightness_group)
        
        self.brightness_step = QSpinBox()
        self.brightness_step.setRange(1, 20)
        brightness_form.addRow("Default step size:", self.brightness_step)
        
        self.brightness_tool = QComboBox()
        self.brightness_tool.addItems(["auto", "xbacklight", "brightnessctl", "light"])
        brightness_form.addRow("Brightness tool:", self.brightness_tool)
        
        brightness_layout.addWidget(brightness_group)
        self.tabs.addTab(brightness_tab, "Brightness")
    
    def load_settings(self):
        """Load settings values into UI components."""
        try:
            # General settings
            self.i3_config_path.setText(self.config.get("i3_config_path", "~/.config/i3/config"))
            self.editor.setText(self.config.get("editor", ""))
            
            # GUI settings
            gui_settings = self.config.get("gui_settings", {})
            self.start_minimized.setChecked(gui_settings.get("start_minimized", False))
            self.minimize_on_close.setChecked(gui_settings.get("minimize_on_close", True))
            
            # Volume settings
            self.volume_step.setValue(self.config.get("volume_step", 5))
            self.volume_tool.setCurrentText(self.config.get("volume_tool", "auto"))
            
            # Brightness settings
            self.brightness_step.setValue(self.config.get("brightness_step", 10))
            self.brightness_tool.setCurrentText(self.config.get("brightness_tool", "auto"))
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def accept(self):
        """Save settings and close dialog."""
        try:
            # Save general settings
            self.config["i3_config_path"] = self.i3_config_path.text()
            self.config["editor"] = self.editor.text()
            
            # Save GUI settings
            if "gui_settings" not in self.config:
                self.config["gui_settings"] = {}
            
            self.config["gui_settings"]["start_minimized"] = self.start_minimized.isChecked()
            self.config["gui_settings"]["minimize_on_close"] = self.minimize_on_close.isChecked()
            
            # Save volume settings
            self.config["volume_step"] = self.volume_step.value()
            self.config["volume_tool"] = self.volume_tool.currentText()
            
            # Save brightness settings
            self.config["brightness_step"] = self.brightness_step.value()
            self.config["brightness_tool"] = self.brightness_tool.currentText()
            
            # Save config
            save_config(self.config)
            logger.info("Settings saved")
            
            super().accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save settings: {e}"
            )