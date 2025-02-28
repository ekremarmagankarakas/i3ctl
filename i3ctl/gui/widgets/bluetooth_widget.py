"""
Bluetooth control widget for the i3ctl GUI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QListWidget, QListWidgetItem,
    QCheckBox, QProgressBar, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QAction, QColor
import argparse
import io
import sys
import re
from contextlib import redirect_stdout

from i3ctl.utils.logger import logger
from i3ctl.utils.config import load_config
from i3ctl.utils.system import run_command
from i3ctl.commands.bluetooth import BluetoothCommand


class BluetoothDeviceItem(QListWidgetItem):
    """List item representing a Bluetooth device."""
    
    def __init__(self, name: str, mac_address: str, is_connected: bool = False, is_paired: bool = False):
        """Initialize BluetoothDeviceItem."""
        super().__init__(name)
        self.mac_address = mac_address
        self.device_name = name
        self.is_connected = is_connected
        self.is_paired = is_paired
        self.update_display()
    
    def update_display(self):
        """Update the item display based on current state."""
        display_text = f"{self.device_name} ({self.mac_address})"
        
        if self.is_connected:
            display_text += " [Connected]"
            self.setForeground(QColor(0, 128, 0))  # Green for connected
        elif self.is_paired:
            display_text += " [Paired]"
            self.setForeground(QColor(0, 0, 255))  # Blue for paired
            
        self.setText(display_text)


class BluetoothWidget(QWidget):
    """Widget for controlling Bluetooth devices."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.bluetooth_cmd = BluetoothCommand()
        self.config = load_config()
        
        # Dictionary to store device information
        self.devices = {}
        
        # Flag to track scanning state
        self.is_scanning = False
        
        # Flag to avoid recursive updates
        self.updating_ui = False
        
        # Set up update timer with a longer interval
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(10000)  # Update every 10 seconds instead of 5
        self.update_timer.timeout.connect(self.update_device_list)
        
        # Set up scan timer
        self.scan_timer = QTimer(self)
        self.scan_timer.setSingleShot(True)
        self.scan_timer.timeout.connect(self.stop_scan)
        
        # Manual refresh button clicked flag
        self.manual_refresh = False
        
        self.setup_ui()
        self.detect_bluetooth()
        
        # Start update timer - only if bluetooth is available
        # The timer will be started in detect_bluetooth if needed
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Status group
        status_group = QGroupBox("Bluetooth Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status indicator
        status_row = QHBoxLayout()
        self.status_label = QLabel("Status: Unknown")
        status_row.addWidget(self.status_label)
        
        self.power_checkbox = QCheckBox("Enabled")
        self.power_checkbox.toggled.connect(self.toggle_power)
        status_row.addWidget(self.power_checkbox)
        
        # Manual refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.manual_refresh_clicked)
        status_row.addWidget(self.refresh_button)
        
        status_row.addStretch()
        status_layout.addLayout(status_row)
        
        # Scanning indicator
        scan_row = QHBoxLayout()
        self.scan_label = QLabel("Scan:")
        scan_row.addWidget(self.scan_label)
        
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 0)  # Indeterminate progress
        self.scan_progress.setVisible(False)
        scan_row.addWidget(self.scan_progress)
        
        self.scan_button = QPushButton("Scan for Devices")
        self.scan_button.clicked.connect(self.start_scan)
        scan_row.addWidget(self.scan_button)
        
        status_layout.addLayout(scan_row)
        
        # Add status group to main layout
        layout.addWidget(status_group)
        
        # Devices group
        devices_group = QGroupBox("Bluetooth Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        # Devices list
        self.device_list = QListWidget()
        self.device_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self.show_device_context_menu)
        self.device_list.itemDoubleClicked.connect(self.device_double_clicked)
        self.device_list.itemClicked.connect(self.update_button_states)  # Update buttons when selection changes
        devices_layout.addWidget(self.device_list)
        
        # Device actions
        actions_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_selected_device)
        actions_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_selected_device)
        actions_layout.addWidget(self.disconnect_button)
        
        self.pair_button = QPushButton("Pair")
        self.pair_button.clicked.connect(self.pair_selected_device)
        actions_layout.addWidget(self.pair_button)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_device)
        actions_layout.addWidget(self.remove_button)
        
        devices_layout.addLayout(actions_layout)
        
        # Add devices group to main layout
        layout.addWidget(devices_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Update button states
        self.update_button_states()
    
    def manual_refresh_clicked(self):
        """Handle manual refresh button clicked."""
        self.manual_refresh = True
        self.update_timer.stop()  # Stop auto updates
        self.detect_bluetooth()   # Do full detection
        # Timer will be restarted in detect_bluetooth if appropriate
    
    def detect_bluetooth(self):
        """Detect bluetooth capabilities and update UI."""
        try:
            # First check if bluetoothctl is available
            return_code, stdout, stderr = run_command(["which", "bluetoothctl"])
            if return_code != 0:
                self.status_label.setText("Status: bluetoothctl not installed")
                self.power_checkbox.setChecked(False)
                self.power_checkbox.setEnabled(False)
                self.scan_button.setEnabled(False)
                self.refresh_button.setEnabled(True)  # Allow retry
                self.update_timer.stop()  # Don't auto-update if no bluetooth
                return
                
            # Try to run bluetoothctl directly to check daemon status
            return_code, stdout, stderr = run_command(["bluetoothctl", "--version"])
            if return_code != 0:
                self.status_label.setText("Status: bluetooth service not running")
                self.power_checkbox.setChecked(False)
                self.power_checkbox.setEnabled(False)
                self.scan_button.setEnabled(False)
                self.refresh_button.setEnabled(True)  # Allow retry
                self.update_timer.stop()  # Don't auto-update if no bluetooth service
                return
                
            # Check bluetooth status
            return_code, stdout, stderr = run_command(["bluetoothctl", "show"])
            if return_code != 0:
                self.status_label.setText("Status: Error getting bluetooth status")
                self.power_checkbox.setChecked(False)
                self.power_checkbox.setEnabled(False)
                self.scan_button.setEnabled(False)
                self.refresh_button.setEnabled(True)  # Allow retry
                self.update_timer.stop()  # Don't auto-update if error
                return
                
            # Update UI based on output
            if not stdout or "No default controller available" in stdout:
                self.status_label.setText("Status: No bluetooth controller found")
                self.power_checkbox.setChecked(False)
                self.power_checkbox.setEnabled(False)
                self.scan_button.setEnabled(False)
                self.refresh_button.setEnabled(True)  # Allow retry
                self.update_timer.stop()  # Don't auto-update if no controller
                return
                
            # Check if bluetooth is powered on
            powered_on = "Powered: yes" in stdout
            self.power_checkbox.setChecked(powered_on)
            self.power_checkbox.setEnabled(True)
            self.status_label.setText(f"Status: {'Available' if powered_on else 'Disabled'}")
            self.scan_button.setEnabled(powered_on)
            self.refresh_button.setEnabled(True)
            
            # Get initial device list
            if powered_on:
                self.update_device_list()
                
                # Start or restart the update timer only if bluetooth is powered on
                if not self.update_timer.isActive():
                    self.update_timer.start()
                
        except Exception as e:
            logger.error(f"Error detecting bluetooth: {e}")
            self.status_label.setText("Status: Error")
            self.power_checkbox.setEnabled(False)
            self.scan_button.setEnabled(False)
            self.refresh_button.setEnabled(True)  # Allow retry
            self.update_timer.stop()  # Don't auto-update if error
    
    def update_device_list(self):
        """Update the list of bluetooth devices."""
        if self.updating_ui or not self.power_checkbox.isChecked():
            return
            
        try:
            self.updating_ui = True
            
            # We'll use direct commands now instead of the command handler
            # This way we can better control the errors and avoid flooding the UI with messages
            
            # Get all devices - direct command execution
            return_code, output, stderr = run_command(["bluetoothctl", "devices"])
            if return_code != 0:
                logger.error(f"Failed to list devices: {stderr}")
                if self.manual_refresh:
                    self.status_label.setText(f"Status: Failed to list devices")
                    self.manual_refresh = False
                return
                
            # Get paired devices, only log the error without showing to user
            # since this is a secondary operation
            try:
                return_code, paired_output, stderr = run_command(["bluetoothctl", "paired-devices"])
                if return_code != 0:
                    logger.debug(f"Could not list paired devices: {stderr}")
                    paired_output = ""
            except Exception as e:
                logger.debug(f"Error listing paired devices: {e}")
                paired_output = ""
            
            # Parse device information
            device_info = {}
            
            # Parse all devices - the output directly from bluetoothctl command (no headers)
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip().startswith("Device"):
                    # Format: "Device XX:XX:XX:XX:XX:XX Name"
                    parts = line.strip().split(' ', 2)
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = parts[2]
                        device_info[mac] = {
                            'name': name,
                            'mac': mac,
                            'paired': False,
                            'connected': False
                        }
            
            # Mark paired devices - the output directly from bluetoothctl command
            paired_lines = paired_output.strip().split('\n')
            for line in paired_lines:
                if line.strip().startswith("Device"):
                    parts = line.strip().split(' ', 2)
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = parts[2]
                        if mac in device_info:
                            device_info[mac]['paired'] = True
                        else:
                            device_info[mac] = {
                                'name': name,
                                'mac': mac,
                                'paired': True,
                                'connected': False
                            }
            
            # Check connected status - use direct command again to avoid error messages
            try:
                return_code, status_output, stderr = run_command(["bluetoothctl", "show"])
                if return_code != 0:
                    logger.debug(f"Could not get bluetooth status: {stderr}")
                    status_output = ""
            except Exception as e:
                logger.debug(f"Error getting bluetooth status: {e}")
                status_output = ""
            
            # Get connected devices info differently - use info command for each device
            for mac in device_info:
                try:
                    # Get detailed info about each device 
                    return_code, device_status, stderr = run_command(["bluetoothctl", "info", mac])
                    
                    # Check if device is connected
                    if return_code == 0 and "Connected: yes" in device_status:
                        device_info[mac]['connected'] = True
                        logger.debug(f"Device {mac} is connected")
                except Exception as e:
                    logger.debug(f"Could not get info for device {mac}: {e}")
            
            # Update list widget
            self.device_list.clear()
            
            # Log found devices for debugging
            device_count = len(device_info)
            logger.debug(f"Found {device_count} bluetooth devices")
            
            if device_count == 0:
                # If no devices found, add a placeholder item
                item = QListWidgetItem("No devices found")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)  # Disable item
                self.device_list.addItem(item)
            else:
                # Add all found devices
                for mac, info in device_info.items():
                    logger.debug(f"Adding device: {info['name']} ({mac}), paired: {info['paired']}, connected: {info['connected']}")
                    item = BluetoothDeviceItem(
                        info['name'], 
                        mac, 
                        is_connected=info['connected'],
                        is_paired=info['paired']
                    )
                    self.device_list.addItem(item)
            
            # Store device info
            self.devices = device_info
            
            # Update button states
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"Error updating device list: {e}")
        finally:
            self.updating_ui = False
    
    def update_button_states(self):
        """Update button states based on selection and devices."""
        selected_items = self.device_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        # Default button states
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(False)
        self.pair_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        
        # Only enable buttons if we have a selection
        if has_selection:
            item = selected_items[0]
            # Make sure the item is a BluetoothDeviceItem
            if isinstance(item, BluetoothDeviceItem):
                # Enable actions based on device state
                self.connect_button.setEnabled(not item.is_connected)
                self.disconnect_button.setEnabled(item.is_connected)
                self.pair_button.setEnabled(not item.is_paired)
                self.remove_button.setEnabled(item.is_paired)
            else:
                # Not a device item
                logger.warning(f"Selected item is not a BluetoothDeviceItem: {type(item)}")
                
        # Force update the buttons to make sure they appear correctly
        self.connect_button.update()
        self.disconnect_button.update()
        self.pair_button.update()
        self.remove_button.update()
    
    def toggle_power(self, checked):
        """Toggle bluetooth power."""
        try:
            args = argparse.Namespace()
            args.subcommand = "power"
            args.state = "on" if checked else "off"
            
            # Execute command
            f = io.StringIO()
            with redirect_stdout(f):
                self.bluetooth_cmd.handle(args)
            
            # Update status
            self.status_label.setText(f"Status: {'Available' if checked else 'Disabled'}")
            self.scan_button.setEnabled(checked)
            
            # If turning off, clear device list
            if not checked:
                self.device_list.clear()
                self.devices = {}
            else:
                # If turning on, update device list
                self.update_device_list()
                
        except Exception as e:
            logger.error(f"Error toggling bluetooth power: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to change bluetooth power state: {e}"
            )
            
            # Restore checkbox state
            self.power_checkbox.setChecked(not checked)
    
    def start_scan(self):
        """Start scanning for bluetooth devices."""
        if self.is_scanning:
            return
            
        try:
            self.is_scanning = True
            self.scan_button.setText("Scanning...")
            self.scan_button.setEnabled(False)
            self.scan_progress.setVisible(True)
            
            # Run a new scan
            try:
                # Start scan
                logger.debug("Starting bluetooth scan")
                run_command(["bluetoothctl", "scan", "on"], capture_output=False)
                
                # Update the status message
                self.status_label.setText("Status: Scanning for devices...")
                
                # Schedule updates while scanning is active
                QTimer.singleShot(3000, self.update_during_scan)
            except Exception as e:
                logger.error(f"Error starting scan: {e}")
                self.stop_scan()
            
            # Start timer to stop scan after timeout
            self.scan_timer.start(10000)  # 10 seconds
            
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            self.stop_scan()
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to start bluetooth scan: {e}"
            )
    
    def update_during_scan(self):
        """Update device list during active scan."""
        # Only update if still scanning
        if not self.is_scanning:
            return
        
        # Update the list
        self.update_device_list()
        
        # Schedule another update if still scanning
        if self.is_scanning:
            QTimer.singleShot(2000, self.update_during_scan)
    
    def stop_scan(self):
        """Stop scanning for bluetooth devices."""
        if not self.is_scanning:
            return
            
        self.is_scanning = False
        self.scan_button.setText("Scan for Devices")
        self.scan_button.setEnabled(True)
        self.scan_progress.setVisible(False)
        
        # Stop the scan command if it's still running
        try:
            logger.debug("Stopping bluetooth scan")
            run_command(["bluetoothctl", "scan", "off"])
        except Exception as e:
            logger.error(f"Error stopping scan: {e}")
            
        # Update device list with a short delay to allow scan to complete
        QTimer.singleShot(500, self.update_device_list)
    
    def show_device_context_menu(self, position):
        """Show context menu for device list."""
        item = self.device_list.itemAt(position)
        if not item or not isinstance(item, BluetoothDeviceItem):
            return
            
        menu = QMenu()
        
        # Add actions based on device state
        if not item.is_connected:
            connect_action = QAction("Connect", self)
            connect_action.triggered.connect(self.connect_selected_device)
            menu.addAction(connect_action)
        else:
            disconnect_action = QAction("Disconnect", self)
            disconnect_action.triggered.connect(self.disconnect_selected_device)
            menu.addAction(disconnect_action)
        
        menu.addSeparator()
        
        if not item.is_paired:
            pair_action = QAction("Pair", self)
            pair_action.triggered.connect(self.pair_selected_device)
            menu.addAction(pair_action)
        else:
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(self.remove_selected_device)
            menu.addAction(remove_action)
        
        # Show menu
        menu.exec(self.device_list.mapToGlobal(position))
    
    def device_double_clicked(self, item):
        """Handle double-click on device item."""
        if not isinstance(item, BluetoothDeviceItem):
            return
            
        if item.is_connected:
            self.disconnect_device(item.mac_address)
        else:
            self.connect_device(item.mac_address)
    
    def get_selected_device(self):
        """Get the currently selected device."""
        selected_items = self.device_list.selectedItems()
        if not selected_items:
            return None
            
        item = selected_items[0]
        if not isinstance(item, BluetoothDeviceItem):
            return None
            
        return item.mac_address
    
    def connect_selected_device(self):
        """Connect to the selected device."""
        device_mac = self.get_selected_device()
        if not device_mac:
            return
            
        self.connect_device(device_mac)
    
    def disconnect_selected_device(self):
        """Disconnect from the selected device."""
        device_mac = self.get_selected_device()
        if not device_mac:
            return
            
        self.disconnect_device(device_mac)
    
    def pair_selected_device(self):
        """Pair with the selected device."""
        device_mac = self.get_selected_device()
        if not device_mac:
            return
            
        try:
            # Show message about manual pairing
            QMessageBox.information(
                self,
                "Pairing",
                "Pairing requires confirmation on both devices.\n"
                "Please watch for prompts on your device and respond to them."
            )
            
            # Execute pairing command
            args = argparse.Namespace()
            args.subcommand = "pair"
            args.device = device_mac
            
            # Run pairing command
            self.bluetooth_cmd.handle(args)
            
            # Update device list after pairing
            self.update_device_list()
            
        except Exception as e:
            logger.error(f"Error pairing device: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to pair with device: {e}"
            )
    
    def remove_selected_device(self):
        """Remove the selected device."""
        device_mac = self.get_selected_device()
        if not device_mac:
            return
            
        try:
            # Confirm removal
            confirm = QMessageBox.question(
                self,
                "Remove Device",
                "Are you sure you want to remove this paired device?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # Execute removal command
            args = argparse.Namespace()
            args.subcommand = "remove"
            args.device = device_mac
            
            # Run command
            f = io.StringIO()
            with redirect_stdout(f):
                self.bluetooth_cmd.handle(args)
            
            # Update device list after removal
            self.update_device_list()
            
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to remove device: {e}"
            )
    
    def connect_device(self, device_mac):
        """Connect to a device."""
        try:
            # Show connecting message
            self.status_label.setText("Status: Connecting...")
            
            # Direct command for better error handling
            return_code, output, stderr = run_command(["bluetoothctl", "connect", device_mac], timeout=15)
            
            # Check for success
            if return_code == 0 and "Connection successful" in output:
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to device."
                )
            else:
                # If failed but output is empty, show stderr instead
                if not output.strip() and stderr:
                    error_msg = stderr
                else:
                    error_msg = output
                    
                QMessageBox.warning(
                    self,
                    "Connection Status",
                    f"Connection attempt completed with status code {return_code}.\n\n{error_msg}"
                )
            
            # Update device list - delay slightly to let connection settle
            QTimer.singleShot(500, self.update_device_list)
            
        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to connect to device: {e}"
            )
        finally:
            # Reset status with a slight delay to show connection status briefly
            QTimer.singleShot(2000, self.detect_bluetooth)
    
    def disconnect_device(self, device_mac):
        """Disconnect from a device."""
        try:
            # Direct command for better error handling
            self.status_label.setText("Status: Disconnecting...")
            return_code, output, stderr = run_command(["bluetoothctl", "disconnect", device_mac])
            
            # Update device list with a slight delay
            QTimer.singleShot(500, self.update_device_list)
            
            # Reset status after a short delay
            QTimer.singleShot(1500, lambda: self.detect_bluetooth())
            
        except Exception as e:
            logger.error(f"Error disconnecting from device: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to disconnect from device: {e}"
            )
    
    def showEvent(self, event):
        """Update device list when widget becomes visible."""
        # Run detect_bluetooth, which will start timer if appropriate
        self.detect_bluetooth()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """Stop timer when widget is hidden."""
        self.update_timer.stop()
        if self.is_scanning:
            self.stop_scan()
        super().hideEvent(event)