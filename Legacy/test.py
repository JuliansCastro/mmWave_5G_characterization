import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

from gps import GPS
from usrp import USRP
from time import sleep
from aiming import RAiming
from pytictoc import TicToc
from filewriter import FileCSV

# gps_t = GPS(port="COM9", baudrate=19200, type="abs")

# print(gps_t.msg)

list = [0,3,5,6,7]

for i in list:
    print(i)