"""
basestation.py

Example showing how to configure a u-blox C94-M8P-2
Application Board.
Receiver to operate in RTK Base Station mode (either
Survey-In or Fixed Timing Mode). This can be used to
complement PyGPSClient's NTRIP Caster functionality.

It also optionally formats a user-defined preset
configuration message string suitable for copying
and pasting into the PyGPSClient ubxpresets file.

Modified on 20 August 2025

:author: semuadmin | juacastropa
:copyright: SEMU Consulting © 2022
:license: BSD 3-Clause
"""

# Route needed by python interpreter to read project's custom classes
# Add the path to the 'Modules' directory to the PYTHONPATH
import os, sys
import contextlib
import numpy as np
import struct
from time import sleep
from serial import Serial
from io import BufferedReader
from pyubx2 import (
    UBXMessage,
    UBXReader,
    val2sphp,
    UBX_PROTOCOL,
    ERR_IGNORE,
    GET,
    POLL
    )
import serial

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'Modules')))
from gps import GPS


TMODE_SVIN = 1
TMODE_FIXED = 2
SHOW_PRESET = True  # hide or show PyGPSClient preset string
MSG_CLASS = "NAV"
MSG_ID = "NAV-HPPOSLLH"

def clear_terminal():
    """
    Clear the terminal screen for a clean display.
    Works on both Windows and Unix-like systems.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def send_msg(serial: Serial, ubx: UBXMessage):
    """
    Send config message to receiver.
    """

    print("\nSending configuration message to receiver...")
    print(ubx)
    serial.write(ubx.serialize())


def read_nav_pvt(serial: Serial):
    """
    Read NAV-PVT message from receiver to get position fix type and coordinates.
    """
    try:
        if not serial.is_open:
            print("Serial port is not open, attempting to open...")
            serial.open()

        ubx_read = UBXReader(BufferedReader(serial),
                             protfilter=UBX_PROTOCOL,
                             quitonerror=ERR_IGNORE)

        # Request NAV-PVT message
        ubx_msg = UBXMessage("NAV", "NAV-PVT", POLL)
        
        print("\nRequesting NAV-PVT message...")
        serial.write(ubx_msg.serialize())
        sleep(0.5)  # Allow more time for the device to respond
        
        response = None
        retry_count = 0
        max_retries = 3
        
        while response is None and retry_count < max_retries:
            if serial.in_waiting:
                with contextlib.suppress(Exception):
                    (raw_data, response) = ubx_read.read()
            
            if response is None:
                retry_count += 1
                sleep(0.1)
        
        if response is None:
            print("No response received after retries")

        return response
    except Exception as e:
        print(f"Error reading NAV-PVT: {e}")
        return None


def read_nav_svin(serial: Serial):
    """
    Read NAV-SVIN message from receiver to get survey-in status and progress.
    """
    try:
        if not serial.is_open:
            print("Serial port is not open, attempting to open...")
            serial.open()

        ubx_read = UBXReader(BufferedReader(serial),
                             protfilter=UBX_PROTOCOL,
                             quitonerror=ERR_IGNORE)

        # Request NAV-SVIN message
        ubx_msg = UBXMessage("NAV", "NAV-SVIN", POLL)
        
        print("Requesting NAV-SVIN message...")
        serial.write(ubx_msg.serialize())
        sleep(0.5)  # Allow time for the device to respond
        
        response = None
        retry_count = 0
        max_retries = 3
        
        while response is None and retry_count < max_retries:
            if serial.in_waiting:
                with contextlib.suppress(Exception):
                    (raw_data, response) = ubx_read.read()
            
            if response is None:
                retry_count += 1
                sleep(0.1)
        
        if response is None:
            print("No NAV-SVIN response received after retries")

        return response
    except Exception as e:
        print(f"Error reading NAV-SVIN: {e}")
        return None


def parse_nav_svin_data(nav_svin_msg):
    """
    Parse NAV-SVIN message to extract survey-in status and progress.
    Based on u-blox documentation from PDF.
    """
    if not nav_svin_msg:
        return None
    
    try:
        # Extract data using pyubx2 attributes
        data = {
            'duration': getattr(nav_svin_msg, 'dur', 0),  # seconds
            'mean_x': getattr(nav_svin_msg, 'meanX', 0),  # cm
            'mean_y': getattr(nav_svin_msg, 'meanY', 0),  # cm
            'mean_z': getattr(nav_svin_msg, 'meanZ', 0),  # cm
            'mean_x_hp': getattr(nav_svin_msg, 'meanXHP', 0),  # 0.1mm
            'mean_y_hp': getattr(nav_svin_msg, 'meanYHP', 0),  # 0.1mm
            'mean_z_hp': getattr(nav_svin_msg, 'meanZHP', 0),  # 0.1mm
            'mean_accuracy': getattr(nav_svin_msg, 'meanAcc', 0),  # 0.1mm
            'observations': getattr(nav_svin_msg, 'obs', 0),  # number
            'valid': getattr(nav_svin_msg, 'valid', 0),  # 1=valid, 0=invalid
            'active': getattr(nav_svin_msg, 'active', 0),  # 1=in-progress, 0=stopped
        }
        
        # Calculate precise coordinates (cm)
        data['precise_x'] = data['mean_x'] + (0.01 * data['mean_x_hp'])
        data['precise_y'] = data['mean_y'] + (0.01 * data['mean_y_hp'])
        data['precise_z'] = data['mean_z'] + (0.01 * data['mean_z_hp'])
        
        return data
    except Exception as e:
        print(f"Error parsing NAV-SVIN data: {e}")
        return None


def display_survey_in_info(svin_data):
    """
    Display survey-in status information in a formatted way.
    """
    if not svin_data:
        print("No valid NAV-SVIN data available")
        return
    
    print("\n" + "="*60)
    print("              SURVEY-IN STATUS INFORMATION")
    print("="*60)
    
    # Status
    print(f'debug svin_data: {svin_data}')
    status = "✅ ACTIVE" if svin_data['active'] else "⏸️  STOPPED"
    validity = "✅ VALID" if svin_data['valid'] else "❌ INVALID"
    
    print(f"Survey-In Status: {status}")
    print(f"Position Validity: {validity}")
    
    # Progress
    print(f"\nPROGRESS:")
    print(f"  Duration: {svin_data['duration']} seconds")
    print(f"  Observations: {svin_data['observations']}")
    print(f"  Mean Accuracy: {svin_data['mean_accuracy']/10:.1f} mm")
    
    # Position (ECEF coordinates)
    print(f"\nECEF COORDINATES:")
    print(f"  X: {svin_data['precise_x']:.2f} cm")
    print(f"  Y: {svin_data['precise_y']:.2f} cm")
    print(f"  Z: {svin_data['precise_z']:.2f} cm")
    
    print("="*60)


def parse_nav_pvt_data(nav_pvt_msg):
    """
    Parse NAV-PVT message to extract position fix type and coordinates.
    Based on u-blox documentation from PDF.
    """
    if not nav_pvt_msg or not hasattr(nav_pvt_msg, 'fixType'):
        return None
    
    # Fix type mapping
    fix_types = {
        0: "NO FIX",
        1: "DEAD RECKONING", 
        2: "2D-FIX",
        3: "3D-FIX",
        4: "GNSS+DR",
        5: "TIME"  # This is what shows as "TIME" in u-center
    }
    
    try:
        # Extract data using pyubx2 attributes
        data = {
            'fix_type': fix_types.get(nav_pvt_msg.fixType, f"UNKNOWN({nav_pvt_msg.fixType})"),
            'fix_type_code': nav_pvt_msg.fixType,
            'longitude': getattr(nav_pvt_msg, 'lon', 0),  # degrees
            'latitude': getattr(nav_pvt_msg, 'lat', 0),   # degrees
            'height_ellipsoid': getattr(nav_pvt_msg, 'height', 0),  # mm
            'height_msl': getattr(nav_pvt_msg, 'hMSL', 0),  # mm
            'h_accuracy': getattr(nav_pvt_msg, 'hAcc', 0),  # mm
            'v_accuracy': getattr(nav_pvt_msg, 'vAcc', 0),  # mm
            'num_satellites': getattr(nav_pvt_msg, 'numSV', 0),
            'pdop': getattr(nav_pvt_msg, 'pDOP', 0) * 0.01 if hasattr(nav_pvt_msg, 'pDOP') else 0,
            'year': getattr(nav_pvt_msg, 'year', 0),
            'month': getattr(nav_pvt_msg, 'month', 0),
            'day': getattr(nav_pvt_msg, 'day', 0),
            'hour': getattr(nav_pvt_msg, 'hour', 0),
            'minute': getattr(nav_pvt_msg, 'min', 0),
            'second': getattr(nav_pvt_msg, 'sec', 0)
        }
        
        return data
    except Exception as e:
        print(f"Error parsing NAV-PVT data: {e}")
        return None


def display_basestation_info(pvt_data, clear_screen=True):
    """
    Display basestation position information in a formatted way.
    
    Args:
        pvt_data: Dictionary containing parsed NAV-PVT data
        clear_screen: Boolean to clear terminal before displaying (default: True)
    """
    if not pvt_data:
        print("No valid NAV-PVT data available")
        return
    
    # Clear terminal for a clean display
    if clear_screen:
        clear_terminal()
    
    print("\n" + "="*60)
    print("           BASESTATION POSITION INFORMATION")
    print("="*60)
    
    # Date and Time
    print(f"DateTime (UTC): {pvt_data['year']:04d}-{pvt_data['month']:02d}-{pvt_data['day']:02d} "
          f"{pvt_data['hour']:02d}:{pvt_data['minute']:02d}:{pvt_data['second']:02d}")
    
    # Position Fix Type (this is what shows as "TIME" in u-center)
    print(f"Position Fix Type: {pvt_data['fix_type']}")
    
    # Coordinates
    print(f"\nCOORDINATES:")
    print(f"  Latitude:  {pvt_data['latitude']:.9f}°")
    print(f"  Longitude: {pvt_data['longitude']:.9f}°")
    print(f"  Height (Ellipsoid): {pvt_data['height_ellipsoid']/1000:.3f} m")
    print(f"  Height (MSL):       {pvt_data['height_msl']/1000:.3f} m")
    
    # Accuracy
    print(f"\nACCURACY:")
    print(f"  Horizontal: {pvt_data['h_accuracy']/1000:.3f} m")
    print(f"  Vertical:   {pvt_data['v_accuracy']/1000:.3f} m")
    
    # Other info
    print(f"\nOTHER INFO:")
    print(f"  Satellites Used: {pvt_data['num_satellites']}")
    print(f"  PDOP: {pvt_data['pdop']:.2f}")
    
    print("="*60)


def monitor_basestation_configuration(serial_port, duration=300):
    """
    Monitor basestation configuration with both NAV-PVT and NAV-SVIN information.
    Shows the transition from NO FIX to TIME fix during survey-in process.
    """
    print(f"\nMonitoring basestation configuration for {duration} seconds...")
    print("This will show both Position Fix Type and Survey-In progress")
    print("Press Ctrl+C to stop monitoring early\n")
    
    import time
    start_time = time.time()
    update_count = 0
    
    try:
        # Open serial port once and keep it open
        stream = Serial(serial_port, BAUD, timeout=TIMEOUT)
        print(f"Serial port {serial_port} opened successfully")
        sleep(1)  # Brief pause after opening
        
        try:
            while True:
                update_count += 1
                elapsed = time.time() - start_time
                
                # Clear screen for clean display
                clear_terminal()
                
                print("="*60)
                print("        BASESTATION CONFIGURATION MONITORING")
                print("="*60)
                print(f"Update #{update_count} | Elapsed: {elapsed:.1f}s / {duration}s")
                print("="*60)
                
                # Get NAV-PVT data
                nav_pvt = read_nav_pvt(stream)
                pvt_data = None
                if nav_pvt:
                    pvt_data = parse_nav_pvt_data(nav_pvt)
                
                # Get NAV-SVIN data
                nav_svin = read_nav_svin(stream)
                svin_data = None
                if nav_svin:
                    svin_data = parse_nav_svin_data(nav_svin)
                
                # Display PVT information
                if pvt_data:
                    print(f"\n📡 POSITION FIX STATUS:")
                    print(f"   Fix Type: {pvt_data['fix_type']}")
                    print(f"   Satellites: {pvt_data['num_satellites']}")
                    print(f"   PDOP: {pvt_data['pdop']:.2f}")
                    print(f"   H.Accuracy: {pvt_data['h_accuracy']/1000:.3f} m")
                    
                    # Show coordinates if available
                    if pvt_data['fix_type'] != "NO FIX":
                        print(f"   Lat: {pvt_data['latitude']:.9f}°")
                        print(f"   Lon: {pvt_data['longitude']:.9f}°")
                        print(f"   Height MSL: {pvt_data['height_msl']/1000:.3f} m")
                else:
                    print(f"\n📡 POSITION FIX STATUS: No data")
                
                # Display Survey-In information
                if svin_data:
                    print(f"\n🔍 SURVEY-IN STATUS:")
                    status = "ACTIVE ⏳" if svin_data['active'] else "STOPPED ⏸️"
                    validity = "VALID ✅" if svin_data['valid'] else "INVALID ❌"
                    
                    print(f"   Status: {status}")
                    print(f"   Validity: {validity}")
                    print(f"   Duration: {svin_data['duration']}s")
                    print(f"   Observations: {svin_data['observations']}")
                    print(f"   Accuracy: {svin_data['mean_accuracy']/10:.1f} mm")
                    
                    if svin_data['observations'] > 0:
                        print(f"   ECEF X: {svin_data['precise_x']:.2f} cm")
                        print(f"   ECEF Y: {svin_data['precise_y']:.2f} cm")
                        print(f"   ECEF Z: {svin_data['precise_z']:.2f} cm")
                else:
                    print(f"\n🔍 SURVEY-IN STATUS: No data")
                
                # Overall status assessment
                print(f"\n" + "="*60)
                if pvt_data and svin_data:
                    if pvt_data['fix_type'] == "TIME" and svin_data['valid']:
                        print("🎉 BASESTATION READY - TIME FIX ACHIEVED!")
                    elif svin_data['active']:
                        print("⏳ SURVEY-IN IN PROGRESS - Please wait...")
                    elif pvt_data['fix_type'] in ["3D-FIX", "2D-FIX"]:
                        print("🔄 GPS ACQUIRED - Survey-In should start soon...")
                    else:
                        print("🔍 WAITING FOR GPS SIGNAL...")
                else:
                    print("📊 COLLECTING DATA...")
                
                print("="*60)
                
                # Check if we should continue monitoring
                if elapsed >= duration:
                    print(f"\nMonitoring completed after {elapsed:.1f} seconds")
                    break
                    
                sleep(5)  # Update every 5 seconds
                
        finally:
            # Always close the serial port
            if stream.is_open:
                stream.close()
                print("Serial port closed")
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error during monitoring: {e}")


def monitor_basestation_status_persistent(serial_port, duration=30):
    """
    Monitor basestation status with persistent serial connection.
    Alternative monitoring function that keeps the serial port open.
    """
    print(f"\nMonitoring basestation status for {duration} seconds...")
    print("Press Ctrl+C to stop monitoring early\n")
    
    import time
    start_time = time.time()
    update_count = 0
    
    try:
        # Open serial port once and keep it open
        stream = Serial(serial_port, BAUD, timeout=TIMEOUT)
        print(f"Serial port {serial_port} opened successfully")
        sleep(1)  # Brief pause after opening
        
        try:
            while True:
                # Get NAV-PVT data
                nav_pvt = read_nav_pvt(stream)
                if nav_pvt:
                    pvt_data = parse_nav_pvt_data(nav_pvt)
                    if pvt_data:
                        update_count += 1
                        elapsed = time.time() - start_time
                        
                        # Display the information with clear screen
                        display_basestation_info(pvt_data, clear_screen=True)
                        
                        # Add monitoring info
                        print(f"\nMONITORING INFO:")
                        print(f"  Update #: {update_count}")
                        print(f"  Elapsed Time: {elapsed:.1f}s / {duration}s")
                        print(f"  Next Update: {5}s")
                        
                        # Check if we have TIME fix (basestation mode)
                        if pvt_data['fix_type'] == "TIME":
                            print("\n✅ BASESTATION IS IN TIME FIX MODE - READY FOR RTK")
                        elif pvt_data['fix_type'] == "3D-FIX":
                            print("\n⚠️  BASESTATION HAS 3D FIX - Transitioning to TIME mode...")
                        else:
                            print(f"\n❌ BASESTATION FIX TYPE: {pvt_data['fix_type']} - Not ready for RTK")
                else:
                    print("⚠️  No NAV-PVT response received")
                
                # Check if we should continue monitoring
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    print(f"\nMonitoring completed after {elapsed:.1f} seconds")
                    break
                    
                sleep(5)  # Update every 5 seconds
                
        finally:
            # Always close the serial port
            if stream.is_open:
                stream.close()
                print("Serial port closed")
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error during monitoring: {e}")


def monitor_basestation_status(serial_port, duration=30):
    """
    Monitor basestation status for a specified duration.
    """
    print(f"\nMonitoring basestation status for {duration} seconds...")
    print("Press Ctrl+C to stop monitoring early\n")
    
    import time
    start_time = time.time()
    try:
        while True:
            # Open, read, and close the serial port for each reading
            try:
                with Serial(serial_port, BAUD, timeout=TIMEOUT) as stream:
                    # Get NAV-PVT data
                    nav_pvt = read_nav_pvt(stream)
                    if nav_pvt:
                        pvt_data = parse_nav_pvt_data(nav_pvt)
                        if pvt_data:
                            display_basestation_info(pvt_data)
                            
                            # Check if we have TIME fix (basestation mode)
                            if pvt_data['fix_type'] == "TIME":
                                print("✅ BASESTATION IS IN TIME FIX MODE - READY FOR RTK")
                            elif pvt_data['fix_type'] == "3D-FIX":
                                print("⚠️  BASESTATION HAS 3D FIX - Transitioning to TIME mode...")
                            else:
                                print(f"❌ BASESTATION FIX TYPE: {pvt_data['fix_type']} - Not ready for RTK")
                    else:
                        print("⚠️  No NAV-PVT response received")
                        
            except Exception as e:
                print(f"Error reading from GPS: {e}")
                print("Retrying in 5 seconds...")
            
            # Check if we should continue monitoring
            elapsed = time.time() - start_time
            if elapsed >= duration:
                print(f"\nMonitoring completed after {elapsed:.1f} seconds")
                break
                
            sleep(5)  # Update every 5 seconds
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error during monitoring: {e}")


def read_msg(serial: Serial):
    """
    Read response message from receiver.
    """
    try:
        if not serial.is_open:
            print("Serial port is not open")
            return None

        ubx_read = UBXReader(BufferedReader(serial),
                             protfilter=UBX_PROTOCOL,
                             quitonerror=ERR_IGNORE)

        ubx_msg = UBXMessage(MSG_CLASS, MSG_ID, POLL)

        send_msg(serial, ubx_msg)
        sleep(0.1)  # Allow time for the device to respond
        response = None
        if serial.in_waiting:
            with contextlib.suppress(Exception):
                (raw_data, response) = ubx_read.read()

        return response
    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in read_msg: {e}")
        return None



def config_rtcm(port_type: str) -> UBXMessage:
    """
    Configure which RTCM3 messages to output.
    """

    print("\nFormatting RTCM MSGOUT CFG-VALSET message...")
    layers = 1  # 1 = RAM, 2 = BBR, 4 = Flash (can be OR'd)
    transaction = 0
    cfg_data = []
    for rtcm_type in (
        "1005",
        "1077",
        "1087",
        "1097",
        "1127",
        "1230",
    ):
        cfg = f"CFG_MSGOUT_RTCM_3X_TYPE{rtcm_type}_{port_type}"
        cfg_data.append([cfg, 1])

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set C94-M8P RTCM3 MSGOUT Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx


def config_svin(port_type: str, acc_limit: int, svin_min_dur: int) -> UBXMessage:
    """
    Configure Survey-In mode with specied accuracy limit.
    """

    print("\nFormatting SVIN TMODE CFG-VALSET message...")
    tmode = TMODE_SVIN
    layers = 1
    transaction = 0
    acc_limit = int(round(acc_limit / 0.1, 0))
    cfg_data = [
        ("CFG_TMODE_MODE", tmode),
        ("CFG_TMODE_SVIN_ACC_LIMIT", acc_limit),
        ("CFG_TMODE_SVIN_MIN_DUR", svin_min_dur),
        (f"CFG_MSGOUT_UBX_NAV_SVIN_{port_type}", 1),
    ]

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set C94-M8P to Survey-In Timing Mode Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx


def config_fixed(acc_limit: int, lat: float, lon: float, height: float) -> UBXMessage:
    """
    Configure Fixed mode with specified coordinates.
    """

    print("\nFormatting FIXED TMODE CFG-VALSET message...")
    tmode = TMODE_FIXED
    pos_type = 1  # LLH (as opposed to ECEF)
    layers = 1
    transaction = 0
    acc_limit = int(round(acc_limit / 0.1, 0))
    lats, lath = val2sphp(lat)
    lons, lonh = val2sphp(lon)

    height = int(height)
    cfg_data = [
        ("CFG_TMODE_MODE", tmode),
        ("CFG_TMODE_POS_TYPE", pos_type),
        ("CFG_TMODE_FIXED_POS_ACC", acc_limit),
        ("CFG_TMODE_HEIGHT_HP", 0),
        ("CFG_TMODE_HEIGHT", height),
        ("CFG_TMODE_LAT", lats),
        ("CFG_TMODE_LAT_HP", lath),
        ("CFG_TMODE_LON", lons),
        ("CFG_TMODE_LON_HP", lonh),
    ]

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set C94-M8P to Fixed Timing Mode Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx


def quick_nav_pvt_test(port="COM3", baud=38400):
    """
    Quick test function to read NAV-PVT data without basestation configuration.
    Useful for testing the GPS receiver connection and data parsing.
    """
    print(f"Quick NAV-PVT test on {port} @ {baud} baud")
    print("="*50)
    
    try:
        with Serial(port, baud, timeout=2) as stream:
            nav_pvt = read_nav_pvt(stream)
            if nav_pvt:
                pvt_data = parse_nav_pvt_data(nav_pvt)
                if pvt_data:
                    # For quick test, don't clear screen to preserve connection info
                    display_basestation_info(pvt_data, clear_screen=False)
                    return pvt_data
                else:
                    print("Could not parse NAV-PVT data")
            else:
                print("No NAV-PVT response received")
                print("Check if GPS device is connected and responding")
    except Exception as e:
        print(f"Error in quick test: {e}")
    
    return None


if __name__ == "__main__":
    # Amend as required...
    PORT = "COM3"  # "/dev/tty.usbmodem2101" # Linux
    PORT_TYPE = "USB"  # choose from "USB", "UART1", "UART2"
    BAUD = 38400
    TIMEOUT = 2

    TMODE = TMODE_SVIN  # "TMODE_SVIN" or 1 = Survey-In, "TMODE_FIXED" or 2 = Fixed
    ACC_LIMIT = 25000    # accuracy in mm - 20 m = 20000 mm

    # only used if TMODE = SVIN ...
    SVIN_MIN_DUR = 300  # seconds

    # only used if TMODE = FIXED ...
    ARP_LON = -74.082731045
    ARP_LAT = 4.639207107
    ARP_HEIGHT = 256824  # cm

    print("="*60)
    print("           U-BLOX BASESTATION CONFIGURATION & MONITORING")
    print("="*60)
    print("1. Quick NAV-PVT test (check GPS connection and data)")
    print("2. Configure basestation + monitor NAV-PVT & NAV-SVIN")
    print("3. Monitor NAV-PVT only (no configuration)")
    print("4. Monitor NAV-PVT with persistent connection")
    print("="*60)
    
    choice = input("Select option (1-4, or Enter for default=1): ").strip()
    if not choice:
        choice = "1"
    
    if choice == "1":
        # Quick test
        print("\nRunning quick NAV-PVT test...")
        quick_nav_pvt_test(PORT, BAUD)
        
    elif choice == "2":
        # Full configuration + monitoring
        print(f"\nConfiguring receiver on {PORT} @ {BAUD:,} baud.\n")
        
        with Serial(PORT, BAUD, timeout=TIMEOUT) as stream:
            # configure RTCM3 outputs
            msg = config_rtcm(PORT_TYPE)
            send_msg(stream, msg)

            # configure either Survey-In or Fixed Timing Mode
            if TMODE == TMODE_SVIN:
                msg = config_svin(PORT_TYPE, ACC_LIMIT, SVIN_MIN_DUR)
            else:
                msg = config_fixed(ACC_LIMIT, ARP_LAT, ARP_LON, ARP_HEIGHT)
            
            send_msg(stream, msg)
            sleep(5)

            # Check responses
            try:
                response_count = 0
                while stream.is_open and stream.in_waiting and response_count < 5:
                    response = read_msg(stream)
                    if response:
                        print(f'Response {MSG_ID}: {response}')
                        response_count += 1
                    sleep(0.1)
            except Exception as e:
                print(f"Error reading configuration responses: {e}")

        # Start monitoring with both NAV-PVT and NAV-SVIN
        try:
            print("\n" + "="*60)
            print("Starting Basestation Configuration Monitoring...")
            print("This will show Position Fix Type transition and Survey-In progress")
            print("="*60)
            monitor_basestation_configuration(PORT, duration=300)
        except Exception as e:
            print(f"Error during basestation monitoring: {e}")
            
    elif choice == "3":
        # Monitor only
        try:
            print("\n" + "="*60)
            print("Starting NAV-PVT monitoring (no configuration)...")
            print("This will show Position Fix Type and coordinates as seen in u-center")
            print("="*60)
            monitor_basestation_status(PORT, duration=300)
        except Exception as e:
            print(f"Error during NAV-PVT monitoring: {e}")
            
    elif choice == "4":
        # Monitor with persistent connection
        try:
            print("\n" + "="*60)
            print("Starting NAV-PVT monitoring with persistent connection...")
            print("This will show Position Fix Type and coordinates as seen in u-center")
            print("="*60)
            monitor_basestation_status_persistent(PORT, duration=300)
        except Exception as e:
            print(f"Error during NAV-PVT monitoring: {e}")
    else:
        print("Invalid choice. Exiting.")
    
    print("\nProgram complete.")
