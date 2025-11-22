# models.py - Data models and application state management

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Any
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
import time
from datetime import datetime


class MeasurementState(Enum):
    """States for measurement recording"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class ConnectionConfig:
    """Configuration for COM port connections"""
    device: Optional[str] = None
    baudrate: int = 19200
    is_connected: bool = False


@dataclass
class MultiPortConfig:
    """Configuration for multiple COM ports (AIM, GPS, USRP)"""
    aim_port: Optional[str] = "COM8"
    aim_baudrate: int = 19200
    aim_connected: bool = False
    
    gps_port: Optional[str] = "COM9"
    gps_baudrate: int = 19200
    gps_connected: bool = False
    
    usrp_frequency: float = 500e6
    usrp_gain_rx: float = 24.7
    usrp_connected: bool = False
    
    def all_connected(self) -> bool:
        """Check if all sensors are connected"""
        return self.aim_connected and self.gps_connected and self.usrp_connected


@dataclass
class GPSData:
    """Data structure for GPS readings"""
    timestamp: str = ""
    r_n_lon: float = 0.0
    r_e_lat: float = 0.0
    r_d_hgt: float = 0.0
    acc_n_hmsl: float = 0.0
    acc_e_hacc: float = 0.0
    acc_d_vacc: float = 0.0
    pos_type: str = ""


@dataclass
class USRPData:
    """Data structure for USRP readings"""
    power_rx: float = 0.0
    timestamp: float = 0.0


@dataclass
class MeasurementRecord:
    """Complete measurement record as saved to CSV"""
    counter: int = 0
    timestamp: str = ""
    gps_data: GPSData = field(default_factory=GPSData)
    usrp_data: USRPData = field(default_factory=USRPData)
    sensor_data: 'SensorData' = field(default_factory=lambda: SensorData())
    
    def to_csv_row(self) -> List[Any]:
        """Convert to CSV row format matching 5G_loss_with_pause.py"""
        return [
            self.timestamp,
            self.gps_data.r_n_lon, self.gps_data.r_e_lat, self.gps_data.r_d_hgt,
            self.gps_data.acc_n_hmsl, self.gps_data.acc_e_hacc, self.gps_data.acc_d_vacc,
            self.gps_data.pos_type, self.usrp_data.power_rx,
            self.sensor_data.bearing, self.sensor_data.roll, self.sensor_data.pitch, 
            self.sensor_data.calibration_status, self.sensor_data.temperature
        ]
    

@dataclass 
class SensorData:
    """Data structure for sensor readings"""
    bearing: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    temperature: float = 0.0
    calibration_status: int = 0
    timestamp: float = 0.0
    
    
@dataclass
class MeasurementData:
    """Data structure for measurement readings - Updated for power vs time and GPS trajectory"""
    # Power vs Time data (changed from distance-based)
    time_data: List[float] = field(default_factory=list)
    power_data: List[float] = field(default_factory=list)
    
    # GPS trajectory data (East vs North in cm relative to base station)
    east_trace: List[float] = field(default_factory=list)  # East position in cm
    north_trace: List[float] = field(default_factory=list)  # North position in cm
    
    # Base station position (reference point at 0,0)
    base_station_east: float = 0.0
    base_station_north: float = 0.0
    
    # Current rover position
    current_east: float = 0.0
    current_north: float = 0.0
    
    max_buffer_size: int = 1000
    start_time: float = field(default_factory=time.time)
    
    def add_power_measurement(self, power: float, timestamp: Optional[float] = None):
        """Add a power vs time measurement data point"""
        if timestamp is None:
            timestamp = time.time()
        
        elapsed_time = timestamp - self.start_time
        self.time_data.append(elapsed_time)
        self.power_data.append(power)
        self._trim_buffers()
    
    def add_gps_measurement(self, east_cm: float, north_cm: float):
        """Add GPS trajectory measurement data point (in cm relative to base station)"""
        self.current_east = east_cm
        self.current_north = north_cm
        self.east_trace.append(east_cm)
        self.north_trace.append(north_cm)
        self._trim_buffers()
    
    def reset_measurements(self):
        """Reset all measurement data and restart timing"""
        self.time_data.clear()
        self.power_data.clear()
        self.east_trace.clear()
        self.north_trace.clear()
        self.start_time = time.time()
        self.current_east = 0.0
        self.current_north = 0.0
    
    def _trim_buffers(self):
        """Keep only the last max_buffer_size points"""
        if len(self.time_data) > self.max_buffer_size:
            self.time_data = self.time_data[-self.max_buffer_size:]
            self.power_data = self.power_data[-self.max_buffer_size:]
        
        if len(self.east_trace) > self.max_buffer_size:
            self.east_trace = self.east_trace[-self.max_buffer_size:]
            self.north_trace = self.north_trace[-self.max_buffer_size:]


class AppState(QObject):
    """Central application state manager with signal emission for UI updates"""
    
    # Signals for state changes
    connection_changed = pyqtSignal(bool, str)  # connected, status_message
    multi_port_connection_changed = pyqtSignal(object)  # MultiPortConfig object
    sensor_data_updated = pyqtSignal(object)     # SensorData object
    measurement_data_updated = pyqtSignal(object)  # MeasurementData object
    measurement_state_changed = pyqtSignal(object)  # MeasurementState enum
    terminal_log_updated = pyqtSignal(str)      # log message
    window_resize_requested = pyqtSignal(int)   # tab_index
    
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()
        
        # Application state - Updated for multi-sensor setup
        self.connection_config = ConnectionConfig()  # Keep for backward compatibility
        self.multi_port_config = MultiPortConfig()
        self.sensor_data = SensorData()
        self.measurement_data = MeasurementData()
        
        # Measurement state
        self.measurement_state = MeasurementState.DISCONNECTED
        self.recording_counter = 0
        self.measurement_records: List[MeasurementRecord] = []
        
        # Terminal log buffer
        self.terminal_log_buffer: List[str] = []
        self.max_log_lines = 1000
        
        # UI state
        self.current_tab_index = 0
        self.window_maximized = False
        
        # Sensor connection objects (will be managed by controller)
        self.aiming_sensor = None
        self.gps_sensor = None
        self.usrp_sensor = None
        self.csv_file_writer = None
        
    def get_connection_config(self) -> ConnectionConfig:
        """Get current connection configuration"""
        with self._lock:
            return self.connection_config
    
    def update_connection_config(self, device: str, baudrate: int, connected: bool = False):
        """Update connection configuration"""
        with self._lock:
            self.connection_config.device = device
            self.connection_config.baudrate = baudrate
            self.connection_config.is_connected = connected
            
            status = f"Conectado a {device}" if connected else "Desconectado"
            self.connection_changed.emit(connected, status)
    
    def set_connection_status(self, connected: bool, status_message: str = ""):
        """Set connection status"""
        with self._lock:
            self.connection_config.is_connected = connected
            if not status_message:
                status_message = "Conectado" if connected else "Desconectado"
            self.connection_changed.emit(connected, status_message)
    
    def update_sensor_data(self, bearing: float, pitch: float, roll: float, 
                          temperature: float = 0.0, calibration_status: int = 0):
        """Update sensor data and emit signal"""
        with self._lock:
            import time
            self.sensor_data.bearing = bearing
            self.sensor_data.pitch = pitch
            self.sensor_data.roll = roll
            self.sensor_data.temperature = temperature
            self.sensor_data.calibration_status = calibration_status
            self.sensor_data.timestamp = time.time()
            
            self.sensor_data_updated.emit(self.sensor_data)
    
    def add_power_measurement(self, power: float, timestamp: Optional[float] = None):
        """Add power measurement data (power vs time)"""
        with self._lock:
            self.measurement_data.add_power_measurement(power, timestamp)
            self.measurement_data_updated.emit(self.measurement_data)
    
    def add_gps_measurement(self, east_cm: float, north_cm: float):
        """Add GPS trajectory measurement data"""
        with self._lock:
            self.measurement_data.add_gps_measurement(east_cm, north_cm)
            self.measurement_data_updated.emit(self.measurement_data)
    
    def update_multi_port_connection(self, config: MultiPortConfig):
        """Update multi-port connection configuration"""
        with self._lock:
            self.multi_port_config = config
            self.multi_port_connection_changed.emit(config)
    
    def set_measurement_state(self, state: MeasurementState):
        """Set measurement recording state"""
        with self._lock:
            self.measurement_state = state
            self.measurement_state_changed.emit(state)
    
    def add_terminal_log(self, message: str):
        """Add message to terminal log"""
        with self._lock:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}"
            self.terminal_log_buffer.append(log_entry)
            
            # Trim buffer if needed
            if len(self.terminal_log_buffer) > self.max_log_lines:
                self.terminal_log_buffer = self.terminal_log_buffer[-self.max_log_lines:]
            
            self.terminal_log_updated.emit(log_entry)
    
    def get_terminal_log(self) -> List[str]:
        """Get current terminal log buffer"""
        with self._lock:
            return self.terminal_log_buffer.copy()
    
    def add_measurement_record(self, record: MeasurementRecord):
        """Add a complete measurement record"""
        with self._lock:
            self.recording_counter += 1
            record.counter = self.recording_counter
            self.measurement_records.append(record)
            
            # Add to graph data
            self.add_power_measurement(record.usrp_data.power_rx)
            # Convert GPS data to relative position (this would need proper GPS conversion)
            # For now, using placeholder values
            self.add_gps_measurement(record.gps_data.r_e_lat * 100, record.gps_data.r_n_lon * 100)
            
            # Add to terminal log
            log_msg = f"{record.counter} | {record.timestamp} | GPS: {record.gps_data.pos_type} | Power: {record.usrp_data.power_rx:.2f} dBm"
            self.add_terminal_log(log_msg)
    
    def get_sensor_data(self) -> SensorData:
        """Get current sensor data"""
        with self._lock:
            return self.sensor_data
    
    def get_measurement_data(self) -> MeasurementData:
        """Get current measurement data"""
        with self._lock:
            return self.measurement_data
    
    def set_current_tab(self, tab_index: int):
        """Set current tab and request appropriate window resize"""
        with self._lock:
            self.current_tab_index = tab_index
            self.window_resize_requested.emit(tab_index)
    
    def set_aiming_sensor(self, sensor):
        """Set the aiming sensor object"""
        with self._lock:
            self.aiming_sensor = sensor
    
    def get_aiming_sensor(self):
        """Get the aiming sensor object"""
        with self._lock:
            return self.aiming_sensor
    
    def set_gps_sensor(self, sensor):
        """Set the GPS sensor object"""
        with self._lock:
            self.gps_sensor = sensor
    
    def get_gps_sensor(self):
        """Get the GPS sensor object"""
        with self._lock:
            return self.gps_sensor
    
    def set_usrp_sensor(self, sensor):
        """Set the USRP sensor object"""
        with self._lock:
            self.usrp_sensor = sensor
    
    def get_usrp_sensor(self):
        """Get the USRP sensor object"""
        with self._lock:
            return self.usrp_sensor
    
    def set_csv_file_writer(self, writer):
        """Set the CSV file writer object"""
        with self._lock:
            self.csv_file_writer = writer
    
    def get_csv_file_writer(self):
        """Get the CSV file writer object"""
        with self._lock:
            return self.csv_file_writer
    
    def get_multi_port_config(self) -> MultiPortConfig:
        """Get current multi-port configuration"""
        with self._lock:
            return self.multi_port_config
    
    def get_measurement_state(self) -> MeasurementState:
        """Get current measurement state"""
        with self._lock:
            return self.measurement_state
    
    def reset_measurement_data(self):
        """Reset all measurement data for new recording session"""
        with self._lock:
            self.measurement_data.reset_measurements()
            self.measurement_records.clear()
            self.recording_counter = 0
            self.add_terminal_log("Measurement data reset for new recording session")