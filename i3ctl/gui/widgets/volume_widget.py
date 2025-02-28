"""
Volume control widget for the i3ctl GUI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSlot
import argparse  # Add this import

from i3ctl.utils.logger import logger
from i3ctl.utils.config import load_config
from i3ctl.commands.volume import VolumeCommand


class VolumeWidget(QWidget):
    """Widget for controlling audio volume."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.volume_cmd = VolumeCommand()
        self.config = load_config()
        self.default_step = self.config.get("volume_step", 5)
        
        self.setup_ui()
        self.update_volume_display()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Volume control group
        volume_group = QGroupBox("Volume Control")
        volume_layout = QVBoxLayout(volume_group)
        
        # Volume level display
        level_layout = QHBoxLayout()
        self.volume_label = QLabel("Volume: 0%")
        level_layout.addWidget(self.volume_label)
        
        self.mute_indicator = QLabel("")
        level_layout.addWidget(self.mute_indicator)
        
        level_layout.addStretch()
        volume_layout.addLayout(level_layout)
        
        # Volume slider
        slider_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.slider_value_changed)
        slider_layout.addWidget(self.volume_slider)
        volume_layout.addLayout(slider_layout)
        
        # Volume buttons
        button_layout = QHBoxLayout()
        
        self.vol_down_btn = QPushButton("Down")
        self.vol_down_btn.clicked.connect(self.volume_down)
        button_layout.addWidget(self.vol_down_btn)
        
        self.mute_btn = QPushButton("Mute")
        self.mute_btn.clicked.connect(self.toggle_mute)
        button_layout.addWidget(self.mute_btn)
        
        self.vol_up_btn = QPushButton("Up")
        self.vol_up_btn.clicked.connect(self.volume_up)
        button_layout.addWidget(self.vol_up_btn)
        
        volume_layout.addLayout(button_layout)
        
        # Add separator
        volume_layout.addSpacing(20)
        
        # Volume level visual
        self.volume_progress = QProgressBar()
        self.volume_progress.setRange(0, 100)
        self.volume_progress.setValue(0)
        self.volume_progress.setTextVisible(True)
        self.volume_progress.setFormat("%v%")
        volume_layout.addWidget(self.volume_progress)
        
        # Add to main layout
        layout.addWidget(volume_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def update_volume_display(self):
        """Update the volume display with current volume level."""
        try:
            # Get current volume
            args = argparse.Namespace()
            args.subcommand = "get"
            
            # Redirect stdout to capture output
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                self.volume_cmd.handle(args)
            output = f.getvalue().strip()
            
            # Parse volume level
            volume_level = 0
            muted = False
            
            try:
                # Output format: "Volume: XX% [muted]"
                if "Volume:" in output:
                    volume_text = output.split("Volume:")[1].strip()
                    if "%" in volume_text:
                        volume_str = volume_text.split("%")[0].strip()
                        volume_level = int(volume_str)
                    
                    muted = "[muted]" in output
            except Exception as e:
                logger.error(f"Failed to parse volume output: {e}")
            
            # Update UI
            self.volume_label.setText(f"Volume: {volume_level}%")
            self.volume_slider.setValue(volume_level)
            self.volume_progress.setValue(volume_level)
            
            # Update mute indicator
            if muted:
                self.mute_indicator.setText("[MUTED]")
                self.mute_indicator.setStyleSheet("color: red;")
                self.mute_btn.setText("Unmute")
            else:
                self.mute_indicator.setText("")
                self.mute_btn.setText("Mute")
            
        except Exception as e:
            logger.error(f"Error updating volume display: {e}")
    
    @pyqtSlot(int)
    def slider_value_changed(self, value):
        """Handle volume slider value change."""
        try:
            # Only update if the change is significant to avoid too many calls
            current_vol = self.volume_progress.value()
            if abs(current_vol - value) >= 1:
                args = argparse.Namespace()
                args.subcommand = "set"
                args.value = value
                self.volume_cmd.handle(args)
                self.update_volume_display()
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def volume_up(self):
        """Increase volume."""
        try:
            args = argparse.Namespace()
            args.subcommand = "up"
            args.percent = self.default_step
            self.volume_cmd.handle(args)
            self.update_volume_display()
        except Exception as e:
            logger.error(f"Error increasing volume: {e}")
    
    def volume_down(self):
        """Decrease volume."""
        try:
            args = argparse.Namespace()
            args.subcommand = "down"
            args.percent = self.default_step
            self.volume_cmd.handle(args)
            self.update_volume_display()
        except Exception as e:
            logger.error(f"Error decreasing volume: {e}")
    
    def toggle_mute(self):
        """Toggle mute state."""
        try:
            args = argparse.Namespace()
            args.subcommand = "mute"
            args.state = None  # Toggle
            self.volume_cmd.handle(args)
            self.update_volume_display()
        except Exception as e:
            logger.error(f"Error toggling mute: {e}")
    
    def showEvent(self, event):
        """Update volume display when widget becomes visible."""
        self.update_volume_display()
        super().showEvent(event)