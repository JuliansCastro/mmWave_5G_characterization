# controllers.py - Business logic and event handling (Controller layer)

from PyQt6.QtCore import QTimer, QObject, pyqtSlot
from PyQt6.QtWidgets import QMessageBox
import sys
import os
import time
import numpy as np
import threading
from datetime import datetime
from typing import Optional, Dict

# Add path to modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Modules'))
from aiming import RAiming
from gps import GPS
from usrp import USRP
from filewriter import FileCSV

from models import AppState, MeasurementState, MultiPortConfig, MeasurementRecord, GPSData, USRPData
from views import (
    SerialPortSelectorView, MultiPortSelectorView, RealTimePlotView, 
    MainWindowView, TerminalLogView
)


class ConnectionController(QObject):
    """Controller for managing sensor connections"""
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
    
    def connect_sensor(self, device: str, baudrate: int) -> bool:
        """Attempt to connect to the aiming sensor"""
        try:
            # Create sensor connection
            aiming_sensor = RAiming(
                serial_port=device,
                baudrate=baudrate
            )
            
            # Store sensor in app state
            self.app_state.set_aiming_sensor(aiming_sensor)
            
            # Update connection configuration
            self.app_state.update_connection_config(device, baudrate, connected=True)
            
            return True
            
        except Exception as e:
            error_msg = f"Could not connect to sensor:\n{str(e)}"
            self.app_state.set_connection_status(False, f"Error: {str(e)}")
            raise Exception(error_msg)
    
    def disconnect_sensor(self):
        """Disconnect from the aiming sensor"""
        aiming_sensor = self.app_state.get_aiming_sensor()
        
        if aiming_sensor:
            try:
                aiming_sensor.serial.close()
            except:
                pass  # Ignore close errors
            
            self.app_state.set_aiming_sensor(None)
        
        self.app_state.set_connection_status(False, "Desconectado")


class DataController(QObject):
    """Controller for managing real-time data acquisition and processing"""
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.data_timer = None
        
    def start_data_acquisition(self):
        """Start real-time data acquisition"""
        if self.data_timer:
            return  # Already running
            
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_real_data)
        self.data_timer.start(100)  # Update every 100ms
    
    def stop_data_acquisition(self):
        """Stop real-time data acquisition"""
        if self.data_timer:
            self.data_timer.stop()
            self.data_timer = None
    
    @pyqtSlot()
    def update_real_data(self):
        """Update real-time data from sensor"""
        aiming_sensor = self.app_state.get_aiming_sensor()
        
        if aiming_sensor:
            try:
                # Get real aiming data: [bearing, pitch_yz, roll_xz, cal_stat_aim, temp]
                aiming_data = aiming_sensor.getAiming()

                if aiming_data and len(aiming_data) >= 3:
                    bearing = aiming_data[0]    # bearing/yaw
                    pitch = aiming_data[1]      # Pitch (pitch_yz)
                    roll = aiming_data[2]       # Roll (roll_xz)
                    
                    # Get additional data if available
                    temperature = aiming_data[4] if len(aiming_data) > 4 else 0.0
                    cal_status = aiming_data[3] if len(aiming_data) > 3 else 0
                    
                    # Update sensor data in app state
                    self.app_state.update_sensor_data(
                        bearing, pitch, roll, temperature, cal_status
                    )

                    # Simulate power and position until you connect real USRP/GPS
                    self._simulate_measurements()

            except Exception as e:
                print(f"Error reading sensor data: {e}")
                # Could emit a signal here to show error in UI
    
    def _simulate_measurements(self):
        """Simulate power and position measurements until real hardware is connected"""
        current_time = time.time()

        # Simulate power vs distance
        distance = (current_time % 60) * 0.5  # Reset every minute
        power = -30 + 5 * np.sin(distance / 5)
        self.app_state.add_power_measurement(distance, power)

        # Simulate GPS position
        east = np.cos(current_time / 10) * 500  # cm
        north = np.sin(current_time / 10) * 500  # cm
        self.app_state.add_gps_measurement(east, north)


class MultiSensorController(QObject):
    """Controller for managing multiple sensors (AIM, GPS, USRP) and measurements"""
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        
        # Sensor objects
        self.aiming_sensor: Optional[RAiming] = None
        self.gps_sensor: Optional[GPS] = None
        self.usrp_sensor: Optional[USRP] = None
        
        # CSV file writer
        self.csv_writer: Optional[FileCSV] = None
        self.metadata_writer: Optional[FileCSV] = None
        
        # Data acquisition timing
        self.data_timer: Optional[QTimer] = None
        self.measurement_start_time = 0.0
        self.recording_active = False
        self.paused = False
        
        # Measurement counters
        self.measurement_counter = 0
        self.last_rate_update = time.time()
        self.last_measurement_count = 0
    
    def connect_all_sensors(self, config: Dict) -> bool:
        """Connect all sensors with the given configuration"""
        try:
            success_count = 0
            sensor_statuses = {"aim": False, "gps": False, "usrp": False}
            
            # Connect Aiming sensor
            if config.get('aim_port'):
                try:
                    self.aiming_sensor = RAiming(
                        serial_port=config['aim_port'],
                        baudrate=config['aim_baudrate']
                    )
                    self.app_state.set_aiming_sensor(self.aiming_sensor)
                    sensor_statuses["aim"] = True
                    success_count += 1
                    self.app_state.add_terminal_log(f"Aiming sensor connected to {config['aim_port']}")
                except Exception as e:
                    self.app_state.add_terminal_log(f"Failed to connect Aiming sensor: {str(e)}")
            
            # Connect GPS sensor
            if config.get('gps_port'):
                try:
                    self.gps_sensor = GPS(
                        port=config['gps_port'],
                        baudrate=config['gps_baudrate'],
                        timeout=0.1,
                        type="all"
                    )
                    self.gps_sensor.startGPSThread()
                    self.app_state.set_gps_sensor(self.gps_sensor)
                    sensor_statuses["gps"] = True
                    success_count += 1
                    self.app_state.add_terminal_log(f"GPS sensor connected to {config['gps_port']}")
                    # Wait for GPS to stabilize
                    time.sleep(2)
                except Exception as e:
                    self.app_state.add_terminal_log(f"Failed to connect GPS sensor: {str(e)}")
            
            # Connect USRP
            try:
                self.usrp_sensor = USRP(
                    rx_center_freq=config.get('usrp_frequency', 500e6),
                    rx_gain=config.get('usrp_gain_rx', 24.7)
                )
                self.usrp_sensor.startRxThread()
                self.app_state.set_usrp_sensor(self.usrp_sensor)
                sensor_statuses["usrp"] = True
                success_count += 1
                self.app_state.add_terminal_log(f"USRP connected with freq={config.get('usrp_frequency', 500e6)/1e6:.1f}MHz, gain={config.get('usrp_gain_rx', 24.7)}dB")
            except Exception as e:
                self.app_state.add_terminal_log(f"Failed to connect USRP: {str(e)}")
            
            # Update multi-port configuration
            multi_config = MultiPortConfig(
                aim_port=config.get('aim_port'),
                aim_baudrate=config.get('aim_baudrate', 19200),
                aim_connected=sensor_statuses["aim"],
                gps_port=config.get('gps_port'),
                gps_baudrate=config.get('gps_baudrate', 19200),
                gps_connected=sensor_statuses["gps"],
                usrp_frequency=config.get('usrp_frequency', 500e6),
                usrp_gain_rx=config.get('usrp_gain_rx', 24.7),
                usrp_connected=sensor_statuses["usrp"]
            )
            
            self.app_state.update_multi_port_connection(multi_config)
            
            all_connected = success_count == 3
            if all_connected:
                self.app_state.set_measurement_state(MeasurementState.CONNECTED)
                self.app_state.add_terminal_log("All sensors connected successfully!")
                # Start real-time data acquisition for visualization (without recording)
                self._switch_to_live_data_mode()
            else:
                self.app_state.add_terminal_log(f"Connected {success_count}/3 sensors")
            
            return all_connected
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Connection error: {str(e)}")
            return False
    
    def disconnect_all_sensors(self):
        """Disconnect all sensors"""
        try:
            # Stop any active recording or live data acquisition
            self.stop_recording()
            
            # Stop live data timer if running
            if self.data_timer and self.data_timer.isActive():
                self.data_timer.stop()
                self.app_state.add_terminal_log("Live data acquisition stopped")
            
            # Disconnect sensors
            if self.aiming_sensor:
                try:
                    self.aiming_sensor.serial.close()
                    self.app_state.add_terminal_log("Aiming sensor disconnected")
                except:
                    pass
                self.aiming_sensor = None
                self.app_state.set_aiming_sensor(None)
            
            if self.gps_sensor:
                try:
                    self.gps_sensor.stopGPSThread()
                    self.app_state.add_terminal_log("GPS sensor disconnected")
                except:
                    pass
                self.gps_sensor = None
                self.app_state.set_gps_sensor(None)
            
            if self.usrp_sensor:
                try:
                    self.usrp_sensor.stopRxThread()
                    self.usrp_sensor.stopRxStream()
                    self.app_state.add_terminal_log("USRP disconnected")
                except:
                    pass
                self.usrp_sensor = None
                self.app_state.set_usrp_sensor(None)
            
            # Update connection state
            disconnected_config = MultiPortConfig(
                aim_connected=False,
                gps_connected=False,
                usrp_connected=False
            )
            self.app_state.update_multi_port_connection(disconnected_config)
            self.app_state.set_measurement_state(MeasurementState.DISCONNECTED)
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Disconnection error: {str(e)}")
    
    def start_recording(self):
        """Start data recording to CSV file"""
        try:
            if not self._all_sensors_connected():
                self.app_state.add_terminal_log("Cannot start recording: not all sensors are connected")
                return False
            
            # Create CSV file writer if not exists
            if not self.csv_writer:
                # Create timestamps - one for day directory, one for session files
                now = datetime.now()
                day_timestamp = now.strftime("%d-%m-%Y")
                full_timestamp = now.strftime("%d-%m-%Y-%H-%M-%S")
                
                # Get the project root directory (one level up from GUI)
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Create day directory and session subdirectory
                day_dir_name = f"5G_loss_MEAS_{day_timestamp}"
                session_dir_name = f"5G_loss_MEAS_{full_timestamp}"
                
                day_path = os.path.join(project_root, "Data", "5G_loss", day_dir_name)
                session_path = os.path.join(day_path, session_dir_name)
                metadata_path = os.path.join(session_path, "Metadata")
                
                # Ensure day, session and metadata directories exist
                os.makedirs(day_path, exist_ok=True)
                os.makedirs(session_path, exist_ok=True)
                os.makedirs(metadata_path, exist_ok=True)
                
                self.csv_writer = FileCSV(
                    name=os.path.join(session_path, f"5G_loss_MEAS_{full_timestamp}"),
                    frequency=None,
                    header=["Timestamp", "R_N/Lon", "R_E/Lat", "R_D/Hgt",
                           "accN/hMSL", "accE/hAcc", "accD/vAcc", "PosType", "PowerRx",
                           "Bearing", "Roll_XZ", "Pitch_YZ", "cal_stat_aim", "Temp"],
                    type="MEAS"
                )
                
                self.metadata_writer = FileCSV(
                    name=os.path.join(metadata_path, f"5G_loss_MEAS_{full_timestamp}"),
                    frequency=None,
                    header=["time_elapsed", "number_of_readings", "reading_rate",
                           "time_per_reading", "usrp_rx_thread", "aiming_thread", "gps_thread"],
                    type="METADATA"
                )
                
                self.app_state.set_csv_file_writer(self.csv_writer)
            
            # Reset measurement data
            self.app_state.reset_measurement_data()
            self.measurement_counter = 0
            self.measurement_start_time = time.time()
            self.last_rate_update = self.measurement_start_time
            self.last_measurement_count = 0
            
            # Switch from live data acquisition to recording mode
            self._switch_to_recording_mode()
            self.recording_active = True
            self.paused = False
            
            self.app_state.set_measurement_state(MeasurementState.RECORDING)
            self.app_state.add_terminal_log(f"Recording started - Day: {day_dir_name}")
            self.app_state.add_terminal_log(f"Session: {session_dir_name}")
            self.app_state.add_terminal_log(f"Data file: {self.csv_writer.filename}")
            if self.metadata_writer:
                self.app_state.add_terminal_log(f"Metadata file: {self.metadata_writer.filename}")
            
            return True
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Failed to start recording: {str(e)}")
            return False
    
    def pause_recording(self):
        """Pause data recording"""
        if self.recording_active and not self.paused:
            self.paused = True
            self.app_state.set_measurement_state(MeasurementState.PAUSED)
            self.app_state.add_terminal_log("Recording paused")
    
    def resume_recording(self):
        """Resume data recording"""
        if self.recording_active and self.paused:
            self.paused = False
            self.app_state.set_measurement_state(MeasurementState.RECORDING)
            self.app_state.add_terminal_log("Recording resumed")
    
    def stop_recording(self):
        """Stop data recording and save metadata"""
        try:
            if self.data_timer:
                self.data_timer.stop()
            
            self.recording_active = False
            self.paused = False
            
            # Calculate final statistics
            if self.measurement_counter > 0 and self.measurement_start_time > 0:
                elapsed_time = time.time() - self.measurement_start_time
                reading_rate = self.measurement_counter / elapsed_time if elapsed_time > 0 else 0
                time_per_reading = (elapsed_time / self.measurement_counter * 1000) if self.measurement_counter > 0 else 0
                
                # Save metadata
                if self.metadata_writer:
                    self.metadata_writer.saveData([
                        elapsed_time, self.measurement_counter, reading_rate, time_per_reading,
                        str(self.usrp_sensor.rx_thread) if self.usrp_sensor else "None",
                        str(self.aiming_sensor.aiming_thread) if self.aiming_sensor else "None", 
                        str(self.gps_sensor.gps_thread) if self.gps_sensor else "None"
                    ])
                
                self.app_state.add_terminal_log(f"Recording stopped - Total measurements: {self.measurement_counter}")
                self.app_state.add_terminal_log(f"Elapsed time: {elapsed_time:.1f}s, Rate: {reading_rate:.1f} Hz")
            
            # Reset file writers for next session
            self.csv_writer = None
            self.metadata_writer = None
            
            # Transition back to CONNECTED state and resume live data acquisition
            if self._all_sensors_connected():
                self.app_state.set_measurement_state(MeasurementState.CONNECTED)
                self.app_state.add_terminal_log("Ready for new measurement session")
                # Switch back to live data acquisition mode
                self._switch_to_live_data_mode()
            else:
                self.app_state.set_measurement_state(MeasurementState.DISCONNECTED)
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Error stopping recording: {str(e)}")
    
    def _all_sensors_connected(self) -> bool:
        """Check if all sensors are connected"""
        return (self.aiming_sensor is not None and 
                self.gps_sensor is not None and 
                self.usrp_sensor is not None)
    
    def _start_live_data_acquisition(self):
        """Start live data acquisition for real-time visualization (without CSV recording)"""
        try:
            if not self.data_timer:
                self.data_timer = QTimer()
                self.data_timer.timeout.connect(self._acquire_live_data)
            
            if not self.data_timer.isActive():
                self.data_timer.start(100)  # 10 Hz data acquisition for live visualization
                self.app_state.add_terminal_log("Started live data visualization")
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Failed to start live data acquisition: {str(e)}")
    
    def _stop_live_data_acquisition(self):
        """Stop live data acquisition"""
        if self.data_timer and self.data_timer.isActive():
            if not self.recording_active:  # Only stop if not recording
                self.data_timer.stop()
                self.app_state.add_terminal_log("Stopped live data visualization")
    
    @pyqtSlot()
    def _acquire_measurement_data(self):
        """Acquire measurement data from all sensors"""
        if not self.recording_active or self.paused:
            return
        
        try:
            # Get data from all sensors
            power_rx = self.usrp_sensor.getPower_dBm(self.usrp_sensor.rx_samples) if self.usrp_sensor else 0.0
            gps_data_raw = self.gps_sensor.format_GPSData() if self.gps_sensor else [0]*7
            aiming_data = self.aiming_sensor.getAiming() if self.aiming_sensor else [0]*5
            
            # Create measurement record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            gps_data = GPSData(
                timestamp=timestamp,
                r_n_lon=gps_data_raw[0],
                r_e_lat=gps_data_raw[1], 
                r_d_hgt=gps_data_raw[2],
                acc_n_hmsl=gps_data_raw[3],
                acc_e_hacc=gps_data_raw[4],
                acc_d_vacc=gps_data_raw[5],
                pos_type=str(gps_data_raw[6]) if len(gps_data_raw) > 6 else "Unknown"
            )
            
            usrp_data = USRPData(power_rx=power_rx, timestamp=time.time())
            
            # Update sensor data in app state 
            if len(aiming_data) >= 5:
                self.app_state.update_sensor_data(
                    bearing=float(aiming_data[0]) if aiming_data[0] is not None else 0.0,
                    pitch=float(aiming_data[1]) if aiming_data[1] is not None else 0.0,
                    roll=float(aiming_data[2]) if aiming_data[2] is not None else 0.0,
                    temperature=float(aiming_data[4]) if aiming_data[4] is not None else 0.0,
                    calibration_status=int(aiming_data[3]) if aiming_data[3] is not None else 0
                )
            
            # Create complete measurement record
            record = MeasurementRecord(
                timestamp=timestamp,
                gps_data=gps_data,
                usrp_data=usrp_data,
                sensor_data=self.app_state.get_sensor_data()
            )
            
            # Save to CSV and update app state
            if self.csv_writer:
                self.csv_writer.saveData(record.to_csv_row())
            
            self.app_state.add_measurement_record(record)
            self.measurement_counter += 1
            
            # Update rate calculation periodically
            current_time = time.time()
            if current_time - self.last_rate_update >= 1.0:  # Update every second
                time_diff = current_time - self.last_rate_update
                count_diff = self.measurement_counter - self.last_measurement_count
                current_rate = count_diff / time_diff if time_diff > 0 else 0.0
                
                # Emit rate update (this would be handled by a signal/slot mechanism)
                self.last_rate_update = current_time
                self.last_measurement_count = self.measurement_counter
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Data acquisition error: {str(e)}")
    
    @pyqtSlot()
    def _acquire_live_data(self):
        """Acquire live sensor data for real-time visualization (without CSV recording)"""
        if not self._all_sensors_connected():
            return
        
        try:
            # Get data from all sensors (same as recording, but without CSV saving)
            power_rx = self.usrp_sensor.getPower_dBm(self.usrp_sensor.rx_samples) if self.usrp_sensor else 0.0
            gps_data_raw = self.gps_sensor.format_GPSData() if self.gps_sensor else [0]*7
            aiming_data = self.aiming_sensor.getAiming() if self.aiming_sensor else [0]*5
            
            # Update sensor data in app state for real-time display
            if len(aiming_data) >= 5:
                self.app_state.update_sensor_data(
                    bearing=float(aiming_data[0]) if aiming_data[0] is not None else 0.0,
                    pitch=float(aiming_data[1]) if aiming_data[1] is not None else 0.0,
                    roll=float(aiming_data[2]) if aiming_data[2] is not None else 0.0,
                    temperature=float(aiming_data[4]) if aiming_data[4] is not None else 0.0,
                    calibration_status=int(aiming_data[3]) if aiming_data[3] is not None else 0
                )
            
            # Create GPS data for live visualization
            gps_data = GPSData(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                r_n_lon=gps_data_raw[0],
                r_e_lat=gps_data_raw[1], 
                r_d_hgt=gps_data_raw[2],
                acc_n_hmsl=gps_data_raw[3],
                acc_e_hacc=gps_data_raw[4],
                acc_d_vacc=gps_data_raw[5],
                pos_type=str(gps_data_raw[6]) if len(gps_data_raw) > 6 else "Unknown"
            )
            
            usrp_data = USRPData(power_rx=power_rx, timestamp=time.time())
            
            # Create measurement record for live visualization (not saved to CSV)
            record = MeasurementRecord(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                gps_data=gps_data,
                usrp_data=usrp_data,
                sensor_data=self.app_state.get_sensor_data()
            )
            
            # Update app state for live visualization (without CSV recording)
            self.app_state.add_measurement_record(record)
            
        except Exception as e:
            self.app_state.add_terminal_log(f"Live data acquisition error: {str(e)}")

    def _switch_to_live_data_mode(self):
        """Switch data acquisition timer to live data mode"""
        if self.data_timer and self.data_timer.isActive():
            self.data_timer.stop()
            
        # Disconnect from recording function and connect to live data function
        if self.data_timer:
            self.data_timer.timeout.disconnect()
            self.data_timer.timeout.connect(self._acquire_live_data)
            self.data_timer.start(100)  # 10Hz for live data
        else:
            self.data_timer = QTimer()
            self.data_timer.timeout.connect(self._acquire_live_data)
            self.data_timer.start(100)  # 10Hz for live data
        
        self.app_state.add_terminal_log("Switched to live data visualization mode")

    def _switch_to_recording_mode(self):
        """Switch data acquisition timer to recording mode"""
        if self.data_timer and self.data_timer.isActive():
            self.data_timer.stop()
            
        # Disconnect from live data function and connect to recording function
        if self.data_timer:
            self.data_timer.timeout.disconnect()
            self.data_timer.timeout.connect(self._acquire_measurement_data)
            self.data_timer.start(100)  # 10Hz for recording
        else:
            self.data_timer = QTimer()
            self.data_timer.timeout.connect(self._acquire_measurement_data)
            self.data_timer.start(100)  # 10Hz for recording
        
        self.app_state.add_terminal_log("Switched to recording mode")


class KeyboardController(QObject):
    """Controller for handling keyboard shortcuts for measurement control"""
    
    def __init__(self, app_state: AppState, multi_sensor_controller: MultiSensorController):
        super().__init__()
        self.app_state = app_state
        self.multi_sensor_controller = multi_sensor_controller
        self.key_listener = None
        
    def start_keyboard_listener(self):
        """Start keyboard listener for measurement control"""
        try:
            from pynput import keyboard
            self.key_listener = keyboard.Listener(on_press=self._on_key_press)
            self.key_listener.start()
            self.app_state.add_terminal_log("Keyboard control enabled: ESC=Pause, ENTER=Resume")
        except ImportError:
            self.app_state.add_terminal_log("pynput not available - keyboard shortcuts disabled")
        except Exception as e:
            self.app_state.add_terminal_log(f"Failed to start keyboard listener: {str(e)}")
    
    def stop_keyboard_listener(self):
        """Stop keyboard listener"""
        if self.key_listener:
            try:
                self.key_listener.stop()
                self.key_listener = None
                self.app_state.add_terminal_log("Keyboard control disabled")
            except:
                pass
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            from pynput import keyboard
            current_state = self.app_state.get_measurement_state()
            
            if key == keyboard.Key.esc:
                # ESC key - Pause recording
                if current_state == MeasurementState.RECORDING:
                    self.multi_sensor_controller.pause_recording()
                    self.app_state.add_terminal_log("Recording paused (ESC pressed)")
                    
            elif key == keyboard.Key.enter:
                # ENTER key - Resume recording
                if current_state == MeasurementState.PAUSED:
                    self.multi_sensor_controller.resume_recording()
                    self.app_state.add_terminal_log("Recording resumed (ENTER pressed)")
                elif current_state == MeasurementState.CONNECTED:
                    self.multi_sensor_controller.start_recording()
                    self.app_state.add_terminal_log("Recording started (ENTER pressed)")
                    
        except Exception as e:
            # Don't spam the log with keyboard errors
            pass


class SerialPortController(QObject):
    """Controller for managing serial port selection"""
    
    def __init__(self, app_state: AppState, view: SerialPortSelectorView):
        super().__init__()
        self.app_state = app_state
        self.view = view
        self._connect_signals()
        
        # Initial refresh
        self.refresh_ports()
    
    def _connect_signals(self):
        """Connect view signals to controller methods"""
        self.view.port_refresh_requested.connect(self.refresh_ports)
        self.app_state.connection_changed.connect(self.view.update_status)
    
    @pyqtSlot()
    def refresh_ports(self):
        """Refresh available COM ports"""
        self.view.refresh_ports()


class MultiPortController(QObject):
    """Controller for managing multi-port sensor selection"""
    
    def __init__(self, app_state: AppState, view: MultiPortSelectorView):
        super().__init__()
        self.app_state = app_state
        self.view = view
        self.multi_sensor_controller = MultiSensorController(app_state)
        self._connect_signals()
        
        # Initial refresh
        self.refresh_ports()
    
    def _connect_signals(self):
        """Connect view signals to controller methods"""
        self.view.port_refresh_requested.connect(self.refresh_ports)
        self.view.multi_connection_requested.connect(self._handle_multi_connection_request)
        self.view.multi_disconnection_requested.connect(self._handle_multi_disconnection_request)
        self.app_state.multi_port_connection_changed.connect(self._update_connection_status)
    
    @pyqtSlot()
    def refresh_ports(self):
        """Refresh available COM ports"""
        self.view.refresh_ports()
    
    @pyqtSlot(dict)
    def _handle_multi_connection_request(self, config: dict):
        """Handle multi-sensor connection request"""
        try:
            success = self.multi_sensor_controller.connect_all_sensors(config)
            if success:
                self.view.update_overall_status(True)
            else:
                self.view.update_overall_status(False)
        except Exception as e:
            QMessageBox.critical(self.view, "Connection Error", str(e))
    
    @pyqtSlot()
    def _handle_multi_disconnection_request(self):
        """Handle multi-sensor disconnection request"""
        self.multi_sensor_controller.disconnect_all_sensors()
        self.view.update_overall_status(False)
        # Update individual sensor statuses
        self.view.update_connection_status("aim", False)
        self.view.update_connection_status("gps", False)
        self.view.update_connection_status("usrp", False)
    
    @pyqtSlot(object)
    def _update_connection_status(self, config: MultiPortConfig):
        """Update view connection status based on MultiPortConfig"""
        self.view.update_connection_status("aim", config.aim_connected)
        self.view.update_connection_status("gps", config.gps_connected)  
        self.view.update_connection_status("usrp", config.usrp_connected)
        self.view.update_overall_status(config.all_connected())
    
    def get_multi_sensor_controller(self) -> MultiSensorController:
        """Get the multi-sensor controller for other components"""
        return self.multi_sensor_controller


class TerminalLogController(QObject):
    """Controller for managing terminal log display"""
    
    def __init__(self, app_state: AppState, view: TerminalLogView):
        super().__init__()
        self.app_state = app_state
        self.view = view
        self._connect_signals()
        
        # Initialize with existing log buffer
        self.view.set_log_buffer(self.app_state.get_terminal_log())
    
    def _connect_signals(self):
        """Connect app state signals to view updates"""
        self.app_state.terminal_log_updated.connect(self.view.add_log_message)
        self.app_state.measurement_state_changed.connect(self._update_recording_status)
    
    @pyqtSlot(object)
    def _update_recording_status(self, state: MeasurementState):
        """Update recording status display"""
        is_recording = state in [MeasurementState.RECORDING, MeasurementState.PAUSED]
        
        # Get current measurement stats (this would come from the measurement controller)
        record_count = len(self.app_state.measurement_records)
        # Calculate rate based on measurement timing
        rate = 0.0  # This would be calculated from actual measurement timing
        
        self.view.update_recording_status(is_recording, record_count, rate)


class RealTimePlotController(QObject):
    """Controller for managing enhanced real-time plot interactions and measurements"""
    
    def __init__(self, app_state: AppState, view: RealTimePlotView, multi_sensor_controller: MultiSensorController):
        super().__init__()
        self.app_state = app_state
        self.view = view
        self.multi_sensor_controller = multi_sensor_controller
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect enhanced view signals and app state signals"""
        # New enhanced view signals
        self.view.connect_sensors_requested.connect(self._handle_multi_connect_request)
        self.view.disconnect_sensors_requested.connect(self._handle_multi_disconnect_request)
        self.view.start_recording_requested.connect(self._handle_start_recording_request)
        self.view.pause_recording_requested.connect(self._handle_pause_recording_request)
        self.view.stop_recording_requested.connect(self._handle_stop_recording_request)
        
        # App state signals
        self.app_state.multi_port_connection_changed.connect(self._update_multi_connection_status)
        self.app_state.sensor_data_updated.connect(self._update_sensor_displays)
        self.app_state.measurement_data_updated.connect(self._update_measurement_displays)
        self.app_state.measurement_state_changed.connect(self._update_recording_status)
    
    @pyqtSlot()
    def _handle_multi_connect_request(self):
        """Handle multi-sensor connection request - delegated to main controller"""
        # This will be handled by the main controller which has access to port config
        pass
    
    @pyqtSlot()
    def _handle_multi_disconnect_request(self):
        """Handle multi-sensor disconnection request"""
        self.multi_sensor_controller.disconnect_all_sensors()
    
    @pyqtSlot()
    def _handle_start_recording_request(self):
        """Handle start/resume recording request"""
        current_state = self.app_state.get_measurement_state()
        
        if current_state == MeasurementState.CONNECTED:
            self.multi_sensor_controller.start_recording()
        elif current_state == MeasurementState.PAUSED:
            self.multi_sensor_controller.resume_recording()
    
    @pyqtSlot()
    def _handle_pause_recording_request(self):
        """Handle pause recording request""" 
        self.multi_sensor_controller.pause_recording()
    
    @pyqtSlot()
    def _handle_stop_recording_request(self):
        """Handle stop recording request"""
        self.multi_sensor_controller.stop_recording()
    
    @pyqtSlot(object)
    def _update_multi_connection_status(self, config: MultiPortConfig):
        """Update multi-sensor connection status in view"""
        sensor_statuses = {
            "aim": config.aim_connected,
            "gps": config.gps_connected,
            "usrp": config.usrp_connected
        }
        self.view.update_multi_sensor_connection_status(config.all_connected(), sensor_statuses)
    
    @pyqtSlot(object)
    def _update_recording_status(self, state: MeasurementState):
        """Update recording status in view"""
        record_count = len(self.app_state.measurement_records)
        
        # Calculate measurement rate
        rate = 0.0
        if hasattr(self.multi_sensor_controller, 'measurement_counter') and hasattr(self.multi_sensor_controller, 'measurement_start_time'):
            if self.multi_sensor_controller.measurement_start_time > 0:
                elapsed = time.time() - self.multi_sensor_controller.measurement_start_time
                if elapsed > 0:
                    rate = self.multi_sensor_controller.measurement_counter / elapsed
        
        # Get filename
        filename = ""
        if self.app_state.get_csv_file_writer():
            filename = getattr(self.app_state.get_csv_file_writer(), 'filename', '')
        
        self.view.update_recording_status(state.value, record_count, rate, filename)
    
    @pyqtSlot(object)
    def _update_sensor_displays(self, sensor_data):
        """Update sensor-related displays (bearing, pitch, roll)"""
        self.view.update_bearing(sensor_data.bearing, sensor_data.calibration_status)
        self.view.update_pitch(sensor_data.pitch)
        self.view.update_roll(sensor_data.roll)
    
    @pyqtSlot(object)
    def _update_measurement_displays(self, measurement_data):
        """Update measurement displays (Power vs Time and GPS Trajectory)"""
        # Update Power vs Time plot
        self.view.update_power_vs_time_plot(
            measurement_data.time_data,
            measurement_data.power_data
        )
        
        # Update GPS Trajectory plot
        if measurement_data.east_trace and measurement_data.north_trace:
            self.view.update_gps_trajectory_plot(
                measurement_data.east_trace,
                measurement_data.north_trace,
                measurement_data.current_east,
                measurement_data.current_north
            )


class MainController(QObject):
    """Enhanced main application controller coordinating all 5G measurement components"""
    
    def __init__(self):
        super().__init__()
        
        # Create app state
        self.app_state = AppState()
        
        # Create views
        self.main_window = MainWindowView()
        self.multi_port_selector_view = MultiPortSelectorView()  # New multi-sensor port selector
        self.realtime_view = RealTimePlotView()
        self.terminal_log_view = TerminalLogView()  # New terminal log view
        
        # Create sub-controllers
        self.multi_port_controller = MultiPortController(self.app_state, self.multi_port_selector_view)
        
        # Pass multi_sensor_controller to realtime controller
        multi_sensor_controller = self.multi_port_controller.get_multi_sensor_controller()
        self.realtime_controller = RealTimePlotController(self.app_state, self.realtime_view, multi_sensor_controller)
        
        self.terminal_log_controller = TerminalLogController(self.app_state, self.terminal_log_view)
        
        # Keyboard control
        self.keyboard_controller = KeyboardController(self.app_state, multi_sensor_controller)
        
        self._setup_main_window()
        self._connect_signals()
        
        # Start keyboard listener
        self.keyboard_controller.start_keyboard_listener()
    
    def _setup_main_window(self):
        """Setup main window with enhanced 3-tab layout"""
        self.main_window.add_tab(self.multi_port_selector_view, "COM Ports")
        self.main_window.add_tab(self.realtime_view, "Real Time")
        self.main_window.add_tab(self.terminal_log_view, "Terminal Log")
    
    def _connect_signals(self):
        """Connect main window and cross-controller signals"""
        self.main_window.tab_changed.connect(self._handle_tab_change)
        self.app_state.window_resize_requested.connect(self.main_window.set_tab_resize_behavior)
        
        # Connect realtime controller's connection request to multi-port controller
        self.realtime_view.connect_sensors_requested.connect(self._handle_multi_sensor_connection_request)
        
        # Connect multi-port selector's tab switching signal
        self.multi_port_selector_view.switch_to_realtime_tab.connect(self._switch_to_realtime_tab)
    
    @pyqtSlot(int)
    def _handle_tab_change(self, tab_index):
        """Handle tab changes for 3-tab layout"""
        self.app_state.set_current_tab(tab_index)
    
    @pyqtSlot()
    def _handle_multi_sensor_connection_request(self):
        """Handle multi-sensor connection request from real-time view"""
        port_config = self.multi_port_selector_view.get_port_configuration()
        
        if port_config:
            # Validate that required ports are selected
            if not port_config.get('aim_port') or not port_config.get('gps_port'):
                self.realtime_view.show_warning_message(
                    "Configuration Error", 
                    "Please select both AIM and GPS ports in the 'COM Ports' tab"
                )
                return
            
            # Delegate to multi-port controller
            self.multi_port_controller._handle_multi_connection_request(port_config)
        else:
            self.realtime_view.show_warning_message(
                "Configuration Error", 
                "Invalid port configuration. Please check settings in 'COM Ports' tab"
            )
    
    @pyqtSlot()
    def _switch_to_realtime_tab(self):
        """Switch to the Real Time tab (index 1) when all sensors are connected"""
        self.main_window.central_widget.setCurrentIndex(1)  # Real Time tab is at index 1
    
    def get_main_window(self):
        """Get the main window for display"""
        return self.main_window