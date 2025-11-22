# views.py - User interface components and widgets (View layer)

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QMessageBox, QGridLayout,
    QLineEdit, QHBoxLayout, QTextEdit, QScrollArea
)
from PyQt6.QtGui import QBrush, QColor, QFont
from typing import Optional, List

import serial.tools.list_ports
import pyqtgraph as pg
import numpy as np


class MultiPortSelectorView(QWidget):
    """View for multiple COM port selection interface (AIM, GPS, USRP)"""
    
    # Signals for user interactions
    port_refresh_requested = pyqtSignal()
    multi_connection_requested = pyqtSignal(dict)  # config dict with all ports
    multi_disconnection_requested = pyqtSignal()
    switch_to_realtime_tab = pyqtSignal()  # Signal to switch to Real Time tab
    
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Multi-Sensor COM Port Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Create grid layout for organized port selection
        grid_layout = QGridLayout()
        
        # Headers
        grid_layout.addWidget(QLabel("Sensor"), 0, 0)
        grid_layout.addWidget(QLabel("COM Port"), 0, 1)
        grid_layout.addWidget(QLabel("Baudrate"), 0, 2)
        grid_layout.addWidget(QLabel("Status"), 0, 3)
        
        # AIM sensor configuration
        grid_layout.addWidget(QLabel("Aiming:"), 1, 0)
        self.aim_port_combo = QComboBox()
        self.aim_baudrate_input = QLineEdit("19200")
        self.aim_status_label = QLabel("Disconnected")
        grid_layout.addWidget(self.aim_port_combo, 1, 1)
        grid_layout.addWidget(self.aim_baudrate_input, 1, 2)
        grid_layout.addWidget(self.aim_status_label, 1, 3)
        
        # GPS sensor configuration
        grid_layout.addWidget(QLabel("GPS:"), 2, 0)
        self.gps_port_combo = QComboBox()
        self.gps_baudrate_input = QLineEdit("19200")
        self.gps_status_label = QLabel("Disconnected")
        grid_layout.addWidget(self.gps_port_combo, 2, 1)
        grid_layout.addWidget(self.gps_baudrate_input, 2, 2)
        grid_layout.addWidget(self.gps_status_label, 2, 3)
        
        # USRP configuration
        grid_layout.addWidget(QLabel("USRP:"), 3, 0)
        usrp_config_layout = QVBoxLayout()
        self.usrp_freq_input = QLineEdit("500e6")
        self.usrp_gain_input = QLineEdit("24.7")
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Freq:"))
        freq_layout.addWidget(self.usrp_freq_input)
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Gain:"))
        gain_layout.addWidget(self.usrp_gain_input)
        usrp_config_layout.addLayout(freq_layout)
        usrp_config_layout.addLayout(gain_layout)
        usrp_widget = QWidget()
        usrp_widget.setLayout(usrp_config_layout)
        self.usrp_status_label = QLabel("Disconnected")
        grid_layout.addWidget(usrp_widget, 3, 1, 1, 2)
        grid_layout.addWidget(self.usrp_status_label, 3, 3)
        
        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        layout.addWidget(grid_widget)

        # Control buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Ports")
        self.connect_button = QPushButton("Connect All Sensors")
        self.disconnect_button = QPushButton("Disconnect All")
        self.disconnect_button.setEnabled(False)
        
        self.refresh_button.clicked.connect(self.port_refresh_requested.emit)
        self.connect_button.clicked.connect(self._on_connect_requested)
        self.disconnect_button.clicked.connect(self.multi_disconnection_requested.emit)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        layout.addWidget(button_widget)

        # Overall status
        self.overall_status_label = QLabel("Status: All sensors disconnected")
        layout.addWidget(self.overall_status_label)
        
        # Set default ports
        self._set_default_ports()

    def _set_default_ports(self):
        """Set default port selections"""
        # This will be called after refresh_ports to set defaults
        pass

    def _on_connect_requested(self):
        """Handle connect button click"""
        config = self.get_port_configuration()
        if config:
            self.multi_connection_requested.emit(config)

    def refresh_ports(self):
        """Refresh the available COM ports for all selectors"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        
        # Clear and repopulate all combo boxes
        self.aim_port_combo.clear()
        self.gps_port_combo.clear()
        
        if port_list:
            self.aim_port_combo.addItems(port_list)
            self.gps_port_combo.addItems(port_list)
            
            # Set default selections if available
            for i, port_info in enumerate(port_list):
                if "COM8" in port_info:
                    self.aim_port_combo.setCurrentIndex(i)
                elif "COM9" in port_info:
                    self.gps_port_combo.setCurrentIndex(i)
            
            self.overall_status_label.setText(f"Status: Found {len(ports)} COM ports")
        else:
            self.overall_status_label.setText("Status: No COM ports found")

    def get_port_configuration(self) -> Optional[dict]:
        """Get the current port configuration"""
        try:
            config = {
                'aim_port': self.aim_port_combo.currentText().split(' - ')[0] if self.aim_port_combo.currentText() else None,
                'aim_baudrate': int(self.aim_baudrate_input.text()) if self.aim_baudrate_input.text() else 19200,
                'gps_port': self.gps_port_combo.currentText().split(' - ')[0] if self.gps_port_combo.currentText() else None,
                'gps_baudrate': int(self.gps_baudrate_input.text()) if self.gps_baudrate_input.text() else 19200,
                'usrp_frequency': float(self.usrp_freq_input.text()) if self.usrp_freq_input.text() else 500e6,
                'usrp_gain_rx': float(self.usrp_gain_input.text()) if self.usrp_gain_input.text() else 24.7
            }
            return config
        except ValueError as e:
            QMessageBox.warning(self, "Configuration Error", f"Invalid configuration values: {str(e)}")
            return None

    def update_connection_status(self, sensor_type: str, connected: bool, message: str = ""):
        """Update connection status for a specific sensor"""
        status_labels = {
            'aim': self.aim_status_label,
            'gps': self.gps_status_label,
            'usrp': self.usrp_status_label
        }
        
        if sensor_type in status_labels:
            label = status_labels[sensor_type]
            if connected:
                label.setText(f"Connected{': ' + message if message else ''}")
                label.setStyleSheet("color: green;")
            else:
                label.setText(f"Disconnected{': ' + message if message else ''}")
                label.setStyleSheet("color: red;")

    def _set_configuration_controls_enabled(self, enabled: bool):
        """Enable or disable all configuration controls (ports, baudrates, USRP settings)"""
        # COM port selectors
        self.aim_port_combo.setEnabled(enabled)
        self.gps_port_combo.setEnabled(enabled)
        
        # Baudrate inputs
        self.aim_baudrate_input.setEnabled(enabled)
        self.gps_baudrate_input.setEnabled(enabled)
        
        # USRP configuration inputs
        self.usrp_freq_input.setEnabled(enabled)
        self.usrp_gain_input.setEnabled(enabled)
        
        # Refresh button
        self.refresh_button.setEnabled(enabled)

    def update_overall_status(self, all_connected: bool):
        """Update overall connection status"""
        if all_connected:
            self.overall_status_label.setText("Status: All sensors connected")
            self.overall_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            # Lock all configuration controls when connected
            self._set_configuration_controls_enabled(False)
            # Emit signal to switch to Real Time tab
            self.switch_to_realtime_tab.emit()
        else:
            self.overall_status_label.setText("Status: Sensors disconnected")
            self.overall_status_label.setStyleSheet("color: red;")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            # Unlock all configuration controls when disconnected
            self._set_configuration_controls_enabled(True)


class TerminalLogView(QWidget):
    """View for displaying terminal log messages in real-time"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the terminal log UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Terminal Log - Real-time Data Recording")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))  # Monospace font
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        layout.addWidget(self.log_display)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: No data recording")
        self.record_count_label = QLabel("Records: 0")
        self.rate_label = QLabel("Rate: 0.0 Hz")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.record_count_label)
        status_layout.addWidget(self.rate_label)
        status_layout.addStretch()  # Push labels to the left
        
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        layout.addWidget(status_widget)

        # Control buttons
        control_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("Clear Log")
        self.save_log_button = QPushButton("Save Log to File")
        self.auto_scroll_button = QPushButton("Auto Scroll: ON")
        self.auto_scroll_button.setCheckable(True)
        self.auto_scroll_button.setChecked(True)
        
        self.clear_log_button.clicked.connect(self.clear_log)
        self.auto_scroll_button.clicked.connect(self.toggle_auto_scroll)
        
        control_layout.addWidget(self.clear_log_button)
        control_layout.addWidget(self.save_log_button)
        control_layout.addWidget(self.auto_scroll_button)
        control_layout.addStretch()
        
        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)
        
        # Auto-scroll enabled by default
        self.auto_scroll_enabled = True

    def add_log_message(self, message: str):
        """Add a new log message to the display"""
        self.log_display.append(message)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll_enabled:
            scrollbar = self.log_display.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())

    def update_recording_status(self, is_recording: bool, record_count: int = 0, rate: float = 0.0):
        """Update the recording status indicators"""
        if is_recording:
            self.status_label.setText("Status: Recording data")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("Status: No data recording")
            self.status_label.setStyleSheet("color: red;")
        
        self.record_count_label.setText(f"Records: {record_count}")
        self.rate_label.setText(f"Rate: {rate:.1f} Hz")

    def clear_log(self):
        """Clear the log display"""
        self.log_display.clear()

    def toggle_auto_scroll(self):
        """Toggle auto-scroll functionality"""
        self.auto_scroll_enabled = self.auto_scroll_button.isChecked()
        if self.auto_scroll_enabled:
            self.auto_scroll_button.setText("Auto Scroll: ON")
            # Scroll to bottom
            scrollbar = self.log_display.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        else:
            self.auto_scroll_button.setText("Auto Scroll: OFF")

    def set_log_buffer(self, log_messages: List[str]):
        """Set the entire log buffer (for initialization)"""
        self.log_display.clear()
        for message in log_messages:
            self.log_display.append(message)
        
        if self.auto_scroll_enabled:
            scrollbar = self.log_display.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())


class SerialPortSelectorView(QWidget):
    """View for single COM port selection interface - kept for backward compatibility"""
    
    # Signals for user interactions
    port_refresh_requested = pyqtSignal()
    connection_requested = pyqtSignal(str, int)  # device, baudrate
    
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("COM Port Selector")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("COM Port:"))
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.port_refresh_requested.emit)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)

        port_widget = QWidget()
        port_widget.setLayout(port_layout)
        layout.addWidget(port_widget)

        # Baudrate selection
        baudrate_layout = QHBoxLayout()
        baudrate_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_input = QLineEdit("19200")  # Default baudrate
        self.baudrate_input.setPlaceholderText("Ex: 9600, 19200, 115200")
        baudrate_layout.addWidget(self.baudrate_input)

        baudrate_widget = QWidget()
        baudrate_widget.setLayout(baudrate_layout)
        layout.addWidget(baudrate_widget)

        # Status
        self.status_label = QLabel("Estado: No conectado")
        layout.addWidget(self.status_label)

    def refresh_ports(self):
        """Refresh the available COM ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

        if ports:
            self.status_label.setText(f"Found {len(ports)} ports")
        else:
            self.status_label.setText("No COM ports found")

    def get_selected_port_info(self):
        """Returns information about the selected port"""
        if self.port_combo.currentText():
            device = self.port_combo.currentText().split(' - ')[0]
            try:
                baudrate = int(self.baudrate_input.text())
            except ValueError:
                baudrate = 19200  # Default fallback

            return {
                'device': device,
                'baudrate': baudrate
            }
        return None

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(f"Estado: {message}")


class BearingCompassView(QWidget):
    """Bearing compass widget for displaying orientation"""
    
    def __init__(self, title="Bearing"):
        super().__init__()
        self._setup_ui(title)

    def _setup_ui(self, title):
        """Setup the compass UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(title)
        layout.addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setXRange(-110, 110)
        self.plot.setYRange(-110, 110)
        layout.addWidget(self.plot)

        # Draw reference circle
        from PyQt6.QtWidgets import QGraphicsEllipseItem
        circle_item = QGraphicsEllipseItem(-100, -100, 200, 200)
        circle_item.setPen(pg.mkPen('#eff5fa', width=2))
        self.plot.addItem(circle_item)

        # Cardinal markers (light color for high visibility)
        self.text_items = {}
        for angle, label in zip([90, 0, 270, 180], ['N', 'E', 'S', 'W']):
            x = 90 * np.cos(np.radians(angle))
            y = 90 * np.sin(np.radians(angle))
            text = pg.TextItem(label, anchor=(0.5, 0.5), color='#eff5fa')
            text.setPos(x, y)
            self.plot.addItem(text)
            self.text_items[label] = text

        # Compass-style direction needle (medium blue for maximum visibility)
        self.arrow = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=2), 
                                   brush=pg.mkBrush('#5374ac'))
        self.plot.addItem(self.arrow)

        # Central cross that rotates with the needle (10 units wide)
        self.center_cross_h = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=2))
        self.center_cross_v = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=2))
        self.plot.addItem(self.center_cross_h)
        self.plot.addItem(self.center_cross_v)

        # Angle text - positioned at the top (light blue for contrast)
        self.angle_text = pg.TextItem("Bearing: 0.0°", anchor=(0.5, 0.5), color='#8bafd0')
        self.angle_text.setPos(0, 110)
        self.plot.addItem(self.angle_text)
        
        # Calibration status text - positioned at the bottom (light blue for contrast)
        self.cal_status_text = pg.TextItem("Cal Status: 0", anchor=(0.5, 0.5), color='#8bafd0')
        self.cal_status_text.setPos(0, -110)
        self.plot.addItem(self.cal_status_text)

    def update_bearing(self, angle_deg: float, cal_status: int = 0):
        """Update the bearing display with optional calibration status"""
        # Convert angle so that 0° is North (coordinate adjustment)
        angle_rad = np.radians(90 - angle_deg)
        
        # Create diamond/triangular shape for the compass needle
        # Tip point (towards the direction)
        tip_length = 70
        tip_x = tip_length * np.cos(angle_rad)
        tip_y = tip_length * np.sin(angle_rad)
        
        # Side points of the diamond (perpendicular to the direction)
        side_length = 15
        side_angle_1 = angle_rad + np.pi/2
        side_angle_2 = angle_rad - np.pi/2
        
        side1_x = side_length * np.cos(side_angle_1)
        side1_y = side_length * np.sin(side_angle_1)
        side2_x = side_length * np.cos(side_angle_2)
        side2_y = side_length * np.sin(side_angle_2)
        
        # Rear point (tail of the diamond)
        tail_length = 20
        tail_x = -tail_length * np.cos(angle_rad)
        tail_y = -tail_length * np.sin(angle_rad)
        
        # Create the diamond polygon: tip -> side1 -> tail -> side2 -> tip
        x_points = [tip_x, side1_x, tail_x, side2_x, tip_x]
        y_points = [tip_y, side1_y, tail_y, side2_y, tip_y]
        
        self.arrow.setData(x_points, y_points)
        
        # Update central cross that rotates with the needle (10 units wide)
        cross_half_width = 5  # 10 total units / 2
        
        # Horizontal line of the cross (rotated)
        cross_h_x1 = -cross_half_width * np.cos(angle_rad + np.pi/2)
        cross_h_y1 = -cross_half_width * np.sin(angle_rad + np.pi/2)
        cross_h_x2 = cross_half_width * np.cos(angle_rad + np.pi/2)
        cross_h_y2 = cross_half_width * np.sin(angle_rad + np.pi/2)
        
        # Vertical line of the cross (rotated)
        cross_v_x1 = -cross_half_width * np.cos(angle_rad)
        cross_v_y1 = -cross_half_width * np.sin(angle_rad)
        cross_v_x2 = cross_half_width * np.cos(angle_rad)
        cross_v_y2 = cross_half_width * np.sin(angle_rad)
        
        self.center_cross_h.setData([cross_h_x1, cross_h_x2], [cross_h_y1, cross_h_y2])
        self.center_cross_v.setData([cross_v_x1, cross_v_x2], [cross_v_y1, cross_v_y2])
        
        # Update angle and calibration status text
        self.angle_text.setText(f"Bearing: {angle_deg:.1f}°")
        
        # Update calibration status with color coding
        cal_status_msg = self._get_calibration_status_message(cal_status)
        cal_color = self._get_calibration_status_color(cal_status)
        self.cal_status_text.setText(cal_status_msg)
        self.cal_status_text.setColor(cal_color)
    
    def _get_calibration_status_message(self, cal_status: int) -> str:
        """Get calibration status message based on status value
        
        Calibration state, bits 0 and 1 reflect the calibration status 
        (0 un-calibrated, 3 fully calibrated)
        """
        status_messages = {
            0: "Cal Status: Un-calibrated",
            1: "Cal Status: Partially Calibrated", 
            2: "Cal Status: Mostly Calibrated",
            3: "Cal Status: Fully Calibrated"
        }
        return status_messages.get(cal_status, f"Cal Status: Unknown ({cal_status})")
    
    def _get_calibration_status_color(self, cal_status: int) -> str:
        """Get color for calibration status based on status value"""
        status_colors = {
            0: '#ff6b6b',  # Red - Uncalibrated
            1: '#ffa500',  # Orange - Partially calibrated
            2: '#ffeb3b',  # Yellow - Mostly calibrated  
            3: '#4caf50'   # Green - Fully calibrated
        }
        return status_colors.get(cal_status, '#8bafd0')  # Default light blue


class AttitudeIndicatorView(QWidget):
    """Attitude indicator widget for displaying pitch and roll"""
    
    def __init__(self, title="Attitude Indicator"):
        super().__init__()
        self.current_pitch = 0.0
        self.current_roll = 0.0
        self._setup_ui(title)

    def _setup_ui(self, title):
        """Setup the attitude indicator UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(title)
        layout.addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.setXRange(-100, 100)
        self.plot.setYRange(-100, 100)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        layout.addWidget(self.plot)

        self._create_horizon_elements()
        self._create_pitch_elements()
        self._create_aircraft_symbol()
        self._create_roll_indicator()
        self._create_text_displays()

        # Initialize positions
        self.update_attitude(0, 0)

    def _create_horizon_elements(self):
        """Create artificial horizon elements"""
        from PyQt6.QtWidgets import QGraphicsRectItem
        
        # Simple rectangles for sky and ground
        self.sky_rect = QGraphicsRectItem(-100, -100, 200, 100)
        self.sky_rect.setBrush(QBrush(QColor(20, 28, 51)))  # #141c33
        self.sky_rect.setPen(pg.mkPen(None))
        self.plot.addItem(self.sky_rect)
        
        self.ground_rect = QGraphicsRectItem(-100, 0, 200, 100)
        self.ground_rect.setBrush(QBrush(QColor(47, 69, 111)))  # #2f456f
        self.ground_rect.setPen(pg.mkPen(None))
        self.plot.addItem(self.ground_rect)

        # Main horizon line (bright light blue for high contrast)
        self.horizon_line = pg.PlotDataItem(pen=pg.mkPen('#8bafd0', width=4))
        self.plot.addItem(self.horizon_line)

    def _create_pitch_elements(self):
        """Create pitch lines and labels"""
        # Pitch lines every 10 degrees (light color for maximum contrast)
        self.pitch_lines = []
        self.pitch_texts = []
        for angle in range(-30, 35, 10):
            if angle == 0:
                continue  # We already have the main horizon line
                
            # Longer lines for main angles
            if abs(angle) % 20 == 0:
                line_width = 50
                pen_width = 2
            else:
                line_width = 30
                pen_width = 1
            
            line = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=pen_width))
            self.plot.addItem(line)
            self.pitch_lines.append((line, angle, line_width))
            
            # Angle labels (bright light blue for high visibility)
            if angle != 0:
                text_left = pg.TextItem(f"{angle}°", anchor=(1, 0.5), color='#8bafd0')
                text_right = pg.TextItem(f"{angle}°", anchor=(0, 0.5), color='#8bafd0')
                self.plot.addItem(text_left)
                self.plot.addItem(text_right)
                self.pitch_texts.append((text_left, text_right, angle))

    def _create_aircraft_symbol(self):
        """Create aircraft symbol"""
        # Aircraft symbol (medium bright blue for maximum visibility)
        self.aircraft_wings = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=4))
        self.aircraft_center = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=3))
        self.plot.addItem(self.aircraft_wings)
        self.plot.addItem(self.aircraft_center)
        
        # Draw aircraft symbol
        self.aircraft_wings.setData([-40, -15, -15, 15, 15, 40], [0, 0, -3, -3, 0, 0])
        self.aircraft_center.setData([0, 0], [-8, 8])

    def _create_roll_indicator(self):
        """Create roll indicator elements"""
        # Roll indicator (upper arc) - light color for maximum contrast
        self.roll_scale = []
        for angle in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            angle_rad = np.radians(angle)
            x = 85 * np.sin(angle_rad)
            y = 85 * np.cos(angle_rad)
            
            # Longer marks for main angles
            if angle % 30 == 0:
                mark_length = 10
                pen_width = 2
            else:
                mark_length = 5
                pen_width = 1
                
            # Mark line
            x2 = (85 - mark_length) * np.sin(angle_rad)
            y2 = (85 - mark_length) * np.cos(angle_rad)
            
            mark = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=pen_width))
            mark.setData([x2, x], [y2, y])
            self.plot.addItem(mark)
            
            # Labels for main angles (bright light blue)
            if angle % 30 == 0 and angle != 0:
                text = pg.TextItem(f"{abs(angle)}°", anchor=(0.5, 0.5), color='#8bafd0')
                text_x = (85 + 15) * np.sin(angle_rad)
                text_y = (85 + 15) * np.cos(angle_rad)
                text.setPos(text_x, text_y)
                self.plot.addItem(text)

        # Roll indicator triangle (medium bright blue)
        self.roll_triangle = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=2), 
                                           brush=pg.mkBrush('#5374ac'))
        self.plot.addItem(self.roll_triangle)

    def _create_text_displays(self):
        """Create text displays for numerical values"""
        # Texts to show numerical values (light blue for high contrast)
        self.pitch_text = pg.TextItem("Pitch: 0.0°", anchor=(0, 1), color='#8bafd0')
        self.pitch_text.setPos(-95, 95)
        self.plot.addItem(self.pitch_text)
        
        self.roll_text = pg.TextItem("Roll: 0.0°", anchor=(1, 1), color='#8bafd0')
        self.roll_text.setPos(95, 95)
        self.plot.addItem(self.roll_text)

    def update_attitude(self, pitch_deg: float, roll_deg: float):
        """Update the attitude display"""
        self.current_pitch = pitch_deg
        self.current_roll = roll_deg
        
        # Convert roll to radians
        roll_rad = np.radians(roll_deg)
        
        # Update main horizon
        horizon_y = -pitch_deg * 2  # Scale pitch
        horizon_points = self._rotate_line(-100, 100, horizon_y, horizon_y, roll_rad)
        self.horizon_line.setData(horizon_points[0], horizon_points[1])
        
        # Update pitch lines
        for line, angle, width in self.pitch_lines:
            line_y = (angle - pitch_deg) * 2
            points = self._rotate_line(-width/2, width/2, line_y, line_y, roll_rad)
            line.setData(points[0], points[1])
        
        # Update pitch texts
        for text_left, text_right, angle in self.pitch_texts:
            text_y = (angle - pitch_deg) * 2
            # Calculate rotated positions for texts
            left_pos = self._rotate_point(-40, text_y, roll_rad)
            right_pos = self._rotate_point(40, text_y, roll_rad)
            text_left.setPos(left_pos[0], left_pos[1])
            text_right.setPos(right_pos[0], right_pos[1])
        
        # Update roll indicator triangle
        triangle_angle = np.radians(-roll_deg)  # Negative to rotate in correct direction
        triangle_x = 75 * np.sin(triangle_angle)
        triangle_y = 75 * np.cos(triangle_angle)
        
        # Create triangle pointing towards center
        tri_size = 5
        triangle_points = [
            [triangle_x, triangle_x - tri_size * np.cos(triangle_angle + np.pi/2), 
             triangle_x - tri_size * np.cos(triangle_angle - np.pi/2)],
            [triangle_y, triangle_y - tri_size * np.sin(triangle_angle + np.pi/2), 
             triangle_y - tri_size * np.sin(triangle_angle - np.pi/2)]
        ]
        self.roll_triangle.setData(triangle_points[0], triangle_points[1])
        
        # Update numerical texts
        self.pitch_text.setText(f"Pitch: {pitch_deg:.1f}°")
        self.roll_text.setText(f"Roll: {roll_deg:.1f}°")

    def update_pitch(self, pitch_deg: float):
        """Update only pitch value"""
        self.update_attitude(pitch_deg, self.current_roll)
    
    def update_roll(self, roll_deg: float):
        """Update only roll value"""
        self.update_attitude(self.current_pitch, roll_deg)

    def _rotate_point(self, x, y, angle):
        """Rotate a point around the origin"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
    
    def _rotate_line(self, x1, x2, y1, y2, angle):
        """Rotate a line around the origin"""
        point1 = self._rotate_point(x1, y1, angle)
        point2 = self._rotate_point(x2, y2, angle)
        return ([point1[0], point2[0]], [point1[1], point2[1]])


class RealTimePlotView(QWidget):
    """Real-time plot visualization interface with enhanced 5G measurement controls"""
    
    # Signals for user interactions
    connect_sensors_requested = pyqtSignal()    # Connect all sensors (AIM, GPS, USRP)
    disconnect_sensors_requested = pyqtSignal() # Disconnect all sensors
    start_recording_requested = pyqtSignal()    # Start/Resume recording
    pause_recording_requested = pyqtSignal()    # Pause recording
    stop_recording_requested = pyqtSignal()     # Stop recording completely
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._recording_state = "disconnected"  # disconnected, connected, recording, paused

    def _setup_ui(self):
        """Setup the real-time plot UI with enhanced 5G measurement controls"""
        layout = QGridLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("Real-Time 5G Measurement Visualization")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label, 0, 0, 1, 3)

        # Enhanced control buttons row
        self.controls_layout = QHBoxLayout()
        
        # Connection buttons
        self.connect_sensors_button = QPushButton("Connect Sensors")
        self.connect_sensors_button.clicked.connect(self.connect_sensors_requested.emit)
        self.connect_sensors_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.disconnect_sensors_button = QPushButton("Disconnect")
        self.disconnect_sensors_button.clicked.connect(self.disconnect_sensors_requested.emit)
        self.disconnect_sensors_button.setEnabled(False)
        
        # Recording control buttons
        self.save_pause_button = QPushButton("Save")
        self.save_pause_button.clicked.connect(self._on_save_pause_clicked)
        self.save_pause_button.setEnabled(False)
        self.save_pause_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        self.save_pause_button.setToolTip("Start recording measurement data to CSV file\n(Changes to Pause/Resume when recording)")
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_recording_requested.emit)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.stop_button.setToolTip("Stop recording and save metadata\n(Ends current measurement session)")

        # Add buttons to layout
        self.controls_layout.addWidget(self.connect_sensors_button)
        self.controls_layout.addWidget(self.disconnect_sensors_button)
        self.controls_layout.addWidget(QLabel("|"))  # Visual separator
        self.controls_layout.addWidget(self.save_pause_button)
        self.controls_layout.addWidget(self.stop_button)
        self.controls_layout.addStretch()  # Push buttons to left

        controls_widget = QWidget()
        controls_widget.setLayout(self.controls_layout)
        layout.addWidget(controls_widget, 1, 0, 1, 3)

        # Multi-line status display
        status_layout = QVBoxLayout()
        self.connection_status = QLabel("Status: All sensors disconnected")
        self.recording_status = QLabel("Recording: Not started")
        self.measurement_stats = QLabel("Measurements: 0 | Rate: 0.0 Hz | File: None")
        
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(self.recording_status)
        status_layout.addWidget(self.measurement_stats)
        
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        layout.addWidget(status_widget, 2, 0, 1, 3)

        # Create plot widgets
        self._create_plots(layout)
        
        # Create orientation widgets
        self._create_orientation_widgets(layout)

    def _create_plots(self, main_layout):
        """Create enhanced plot widgets for 5G measurements"""
        
        # 1D Graph: Power vs Time (changed from Power vs Distance)
        self.plot1d = pg.PlotWidget(title="5G Power Reception vs Time")
        self.plot1d.setLabel('left', 'Power Reception', units='dBm')
        self.plot1d.setLabel('bottom', 'Time Elapsed', units='s')
        self.plot1d.showGrid(True, True, alpha=0.3)
        self.curve1d = self.plot1d.plot(pen=pg.mkPen('#8bafd0', width=2))
        main_layout.addWidget(self.plot1d, 3, 0, 1, 2)

        # 2D Graph: GPS Trajectory Real-Time (changed from generic position)
        self.plot2d = pg.PlotWidget(title="GPS Trajectory Real-Time")
        self.plot2d.setLabel('left', 'North Position', units='cm')
        self.plot2d.setLabel('bottom', 'East Position', units='cm')
        self.plot2d.setAspectLocked(True)
        self.plot2d.showGrid(True, True, alpha=0.3)
        
        # Base Station marker (red dot at origin)
        self.base_station_point = self.plot2d.plot(
            [0], [0], pen=None, symbol='o', symbolBrush='red', symbolSize=15, name='Base Station')
        
        # GPS trajectory trace (green line)
        self.gps_trace_curve = self.plot2d.plot(pen=pg.mkPen('green', width=2), name='GPS Path')
        
        # Current rover position (blue moving dot)
        self.rover_current_point = self.plot2d.plot(
            [0], [0], pen=None, symbol='o', symbolBrush='blue', symbolSize=12, name='Rover Position')
        
        # Add legend
        self.plot2d.addLegend()
        
        main_layout.addWidget(self.plot2d, 3, 2)

    def _create_orientation_widgets(self, main_layout):
        """Create orientation display widgets (unchanged - maintain Bearing and Attitude)"""
        
        # Aiming system label
        aiming_label = QLabel("Aiming System")
        aiming_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(aiming_label, 4, 0, 1, 3)
        
        # Bearing compass (NO CHANGES - keep as is)
        self.bearing_widget = BearingCompassView("Bearing")
        main_layout.addWidget(self.bearing_widget, 5, 0)

        # Attitude indicator (NO CHANGES - keep as is)
        self.attitude_widget = AttitudeIndicatorView("Attitude Indicator")
        main_layout.addWidget(self.attitude_widget, 5, 1, 1, 2)  # Spans 2 columns

    def _on_save_pause_clicked(self):
        """Handle Save/Pause button click - toggles between Save/Pause/Resume"""
        if self._recording_state == "connected":
            # Start recording
            self.start_recording_requested.emit()
        elif self._recording_state == "recording":
            # Pause recording  
            self.pause_recording_requested.emit()
        elif self._recording_state == "paused":
            # Resume recording
            self.start_recording_requested.emit()
        elif self._recording_state == "stopped":
            # Start new recording session after previous one was stopped
            self.start_recording_requested.emit()

    def update_multi_sensor_connection_status(self, all_connected: bool, sensor_statuses: dict):
        """Update connection status for multi-sensor setup"""
        if all_connected:
            self.connection_status.setText("Status: All sensors connected (AIM + GPS + USRP)")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.connect_sensors_button.setEnabled(False)
            self.disconnect_sensors_button.setEnabled(True)
            self.save_pause_button.setEnabled(True)
            self._recording_state = "connected"
            self.save_pause_button.setText("Save")
        else:
            # Show which sensors are connected/disconnected
            aim_status = "✓" if sensor_statuses.get("aim", False) else "✗"
            gps_status = "✓" if sensor_statuses.get("gps", False) else "✗"
            usrp_status = "✓" if sensor_statuses.get("usrp", False) else "✗"
            
            self.connection_status.setText(f"Status: AIM {aim_status} | GPS {gps_status} | USRP {usrp_status}")
            self.connection_status.setStyleSheet("color: red;")
            self.connect_sensors_button.setEnabled(True)
            self.disconnect_sensors_button.setEnabled(False)
            self.save_pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self._recording_state = "disconnected"

    def update_recording_status(self, state: str, record_count: int = 0, rate: float = 0.0, filename: str = ""):
        """Update recording status and measurement statistics"""
        self._recording_state = state
        
        if state == "recording":
            self.recording_status.setText("Recording: ACTIVE")
            self.recording_status.setStyleSheet("color: green; font-weight: bold;")
            self.save_pause_button.setText("Pause")
            self.save_pause_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
            self.save_pause_button.setToolTip("Pause the current recording session\n(Data will be temporarily stopped)")
            self.stop_button.setEnabled(True)
            self.stop_button.setToolTip("Stop recording and save metadata\n(Ends current measurement session)")
        elif state == "paused":
            self.recording_status.setText("Recording: PAUSED")
            self.recording_status.setStyleSheet("color: orange; font-weight: bold;")
            self.save_pause_button.setText("Resume")
            self.save_pause_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            self.save_pause_button.setToolTip("Resume the paused recording session\n(Continue collecting measurement data)")
            self.stop_button.setEnabled(True)
            self.stop_button.setToolTip("Stop recording and save metadata\n(Ends current measurement session)")
        elif state == "stopped":
            self.recording_status.setText("Recording: STOPPED")
            self.recording_status.setStyleSheet("color: red;")
            self.save_pause_button.setText("Save")
            self.save_pause_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
            self.save_pause_button.setToolTip("Start recording measurement data to CSV file\n(Begin new measurement session)")
            self.stop_button.setEnabled(False)
            self.stop_button.setToolTip("Stop recording (disabled - not recording)")
        elif state == "connected":
            # Sensors are connected and ready for new measurement
            self.recording_status.setText("Recording: Ready")
            self.recording_status.setStyleSheet("color: blue; font-weight: bold;")
            self.save_pause_button.setText("Save")
            self.save_pause_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
            self.save_pause_button.setToolTip("Start new recording measurement data to CSV file\n(All sensors connected and ready)")
            self.save_pause_button.setEnabled(True)  # Ensure button is enabled
            self.stop_button.setEnabled(False)
            self.stop_button.setToolTip("Stop recording (disabled - not recording)")
        else:  # disconnected or other states
            self.recording_status.setText("Recording: Not started")
            self.recording_status.setStyleSheet("color: gray;")
            self.save_pause_button.setText("Save")
            self.save_pause_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
            self.save_pause_button.setToolTip("Start recording measurement data to CSV file\n(Connect all sensors first)")
            self.save_pause_button.setEnabled(False)  # Disabled when not connected
            self.stop_button.setToolTip("Stop recording (disabled - not recording)")
        
        # Update measurement statistics
        file_display = filename if filename else "None"
        self.measurement_stats.setText(f"Measurements: {record_count} | Rate: {rate:.1f} Hz | File: {file_display}")

    def update_power_vs_time_plot(self, time_data, power_data):
        """Update Power vs Time plot with new data"""
        self.curve1d.setData(time_data, power_data)

    def update_gps_trajectory_plot(self, east_trace, north_trace, current_east=None, current_north=None):
        """Update GPS trajectory plot with new data"""
        # Update GPS path trace
        self.gps_trace_curve.setData(east_trace, north_trace)
        
        # Update current rover position if provided
        if current_east is not None and current_north is not None:
            self.rover_current_point.setData([current_east], [current_north])

    # Keep existing methods for backward compatibility
    def update_1d_plot(self, time_data, power_data):
        """Update 1D plot - redirects to power vs time"""
        self.update_power_vs_time_plot(time_data, power_data)

    def update_2d_plot(self, east_trace, north_trace, current_east=None, current_north=None, ref_east=0, ref_north=0):
        """Update 2D plot - redirects to GPS trajectory"""
        self.update_gps_trajectory_plot(east_trace, north_trace, current_east, current_north)

    def update_bearing(self, angle_deg: float, cal_status: int = 0):
        """Update bearing display"""
        self.bearing_widget.update_bearing(angle_deg, cal_status)

    def update_pitch(self, angle_deg: float):
        """Update pitch display"""
        self.attitude_widget.update_pitch(angle_deg)

    def update_roll(self, angle_deg: float):
        """Update roll display"""
        self.attitude_widget.update_roll(angle_deg)

    def show_error_message(self, title: str, message: str):
        """Show error message box"""
        QMessageBox.critical(self, title, message)

    def show_warning_message(self, title: str, message: str):
        """Show warning message box"""
        QMessageBox.warning(self, title, message)


class MainWindowView(QMainWindow):
    """Main application window view"""
    
    # Signals for window events
    tab_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup main window UI with enhanced 5G measurement capabilities"""
        self.setWindowTitle("5G mmWave Characterization System - Real-Time Analysis")
        
        # Configure window with initial normal size
        self.setGeometry(50, 50, 800, 600)

        # Central widget with tabs
        self.central_widget = QTabWidget()
        self.central_widget.currentChanged.connect(self.tab_changed.emit)
        self.setCentralWidget(self.central_widget)

    def add_tab(self, widget: QWidget, title: str):
        """Add a tab to the main window"""
        self.central_widget.addTab(widget, title)

    def set_tab_resize_behavior(self, tab_index: int):
        """Handle tab-specific resize behavior for 3-tab layout"""
        if tab_index == 0:  # "COM Ports" tab - Multi-sensor configuration
            if self.isMaximized():  # Only change if it's maximized
                self.showNormal()  # Return to normal size
                # Use QTimer to give time for the window to normalize before changing geometry
                QTimer.singleShot(
                    50, lambda: self.setGeometry(50, 50, 800, 600))
        elif tab_index == 1:  # "Real Time" tab - Measurements and plots
            if not self.isMaximized():  # Only maximize if not already maximized
                self.showMaximized()  # Maximize window for better plot visibility
        elif tab_index == 2:  # "Terminal Log" tab - Log display
            if self.isMaximized():  # Return to normal size for better log readability
                self.showNormal()
                QTimer.singleShot(
                    50, lambda: self.setGeometry(100, 100, 900, 700))