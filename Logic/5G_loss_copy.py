import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

from usrp import USRP
from gps import GPS
from aiming import RAiming
from pytictoc import TicToc
from filewriter import FileCSV

# Serial ports
aim_port = "COM3"
gps_port = "COM5"

# Baudrates
aim_baudrate = 19200
gps_baudrate = 19200

# USRP parameters
frequency = 500e6
gain_rx = 24.7

# Measure instruments objects
usrp_UT = USRP(rx_center_freq=frequency, rx_gain=gain_rx)
aiming_UT = RAiming(baudrate=aim_baudrate, serial_port=aim_port)
gps_UT = GPS(port=gps_port, baudrate=gps_baudrate, timeout=0.1)

# Files instantiation
file = FileCSV(name="Data/5G_loss/5G_loss", frequency=None, header=["Dist_N","Dist_E","Dist_D", "PowerRx","XZ","YZ", "MAG"], type="MEAS")
file_metadata = FileCSV(name="Data/5G_loss/Metadata/5G_loss", frequency=None, header=["time_elapsed","mumber_of_readings","reading_rate","time_per_reading","usrp_rx_thread","aiming_thread","gps_thread"], type="METADATA")