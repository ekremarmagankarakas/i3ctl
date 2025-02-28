"""
Volume control widget for the i3ctl GUI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QWheelEvent
import argparse
import re

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
        
        # Track if slider is being dragged to avoid unnecessary updates
        self.slider_dragging = False
        
        # Flag to avoid recursive slider updates
        self.updating_ui = False
        
        # Set up update timer for real-time feedback
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(500)  # Update every 500ms
        self.update_timer.timeout.connect(self.update_volume_display)
        
        self.setup_ui()
        self.update_volume_display()
        
        # Start update timer
        self.update_timer.start()
    
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
        
        # Connect to slider signals
        self.volume_slider.valueChanged.connect(self.slider_value_changed)
        self.volume_slider.sliderPressed.connect(self.slider_pressed)
        self.volume_slider.sliderReleased.connect(self.slider_released)
        
        # Set slider to allow mouse wheel
        self.volume_slider.wheelEvent = self.slider_wheel_event
        
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
            # Skip update if slider is being dragged
            if self.slider_dragging:
                return
            
            # Set flag to prevent recursive updates
            self.updating_ui = True
            
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
                # Parse both formats: "Current volume: XX%" or "Volume: XX% [muted]"
                volume_pattern = r"(?:Current |)(?:V|v)olume:?\s*(\d+)%"
                volume_match = re.search(volume_pattern, output)
                if volume_match:
                    volume_level = int(volume_match.group(1))
                
                # Check for mute state
                muted = "[muted]" in output.lower() or "muted: yes" in output.lower()
                
            except Exception as e:
                logger.error(f"Failed to parse volume output: {e}")
            
            # Update UI elements
            self.volume_label.setText(f"Volume: {volume_level}%")
            
            # Use blockSignals to prevent recursive updates
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(volume_level)
            self.volume_slider.blockSignals(False)
            
            # Update progress bar with proper styling
            self.volume_progress.setValue(volume_level)
            
            # Set color based on volume level
            if volume_level > 75:
                self.volume_progress.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
            elif volume_level > 40:
                self.volume_progress.setStyleSheet("QProgressBar::chunk { background-color: #3498db; }")
            else:
                self.volume_progress.setStyleSheet("QProgressBar::chunk { background-color: #9b59b6; }")
            
            # Update mute indicator
            if muted:
                self.mute_indicator.setText("[MUTED]")
                self.mute_indicator.setStyleSheet("color: red; font-weight: bold;")
                self.mute_btn.setText("Unmute")
                # Gray out progress bar when muted
                self.volume_progress.setStyleSheet("QProgressBar::chunk { background-color: #7f8c8d; }")
            else:
                self.mute_indicator.setText("")
                self.mute_btn.setText("Mute")
            
        except Exception as e:
            logger.error(f"Error updating volume display: {e}")
        finally:
            # Clear updating flag
            self.updating_ui = False
    
    def slider_pressed(self):
        """Handle slider press event."""
        self.slider_dragging = True
        # Pause the update timer while dragging to avoid jumps
        self.update_timer.stop()
    
    def slider_released(self):
        """Handle slider release event."""
        self.slider_dragging = False
        # Apply the final value when slider is released
        self.apply_slider_value()
        # Resume the update timer
        self.update_timer.start()
    
    def apply_slider_value(self):
        """Apply the current slider value to the volume."""
        try:
            value = self.volume_slider.value()
            args = argparse.Namespace()
            args.subcommand = "set"
            args.value = value
            self.volume_cmd.handle(args)
            self.update_volume_display()
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def slider_wheel_event(self, event: QWheelEvent):
        """Handle mouse wheel events on the slider."""
        try:
            # Get angle delta to determine direction
            delta = event.angleDelta().y()
            
            if delta > 0:
                # Wheel up - increase volume
                self.volume_up()
            else:
                # Wheel down - decrease volume
                self.volume_down()
                
            event.accept()
        except Exception as e:
            logger.error(f"Error handling wheel event: {e}")
    
    @pyqtSlot(int)
    def slider_value_changed(self, value):
        """Handle volume slider value change."""
        try:
            # Avoid recursive updates and only process when dragging
            if self.updating_ui:
                return
                
            if self.slider_dragging:
                # Update progress bar while dragging
                self.volume_progress.setValue(value)
                self.volume_label.setText(f"Volume: {value}%")
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
        # Start the update timer when widget becomes visible
        self.update_timer.start()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """Stop timer when widget is hidden."""
        # Stop the update timer when widget is hidden to save resources
        self.update_timer.stop()
        super().hideEvent(event)
        
    def wheelEvent(self, event):
        """Handle wheel events on the widget."""
        # Redirect wheel events to the slider's wheel handler
        self.slider_wheel_event(event)