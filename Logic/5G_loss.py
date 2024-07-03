import sys
sys.path.append('C:/Users/JuliansCastro/Documents/5G_characterization/Modules')

import uhd
import csv
import numpy as np
import threading
import scipy.io as sio
from tkinter import *
from tkinter import ttk
from datetime import datetime 
from time import sleep
from io import BufferedReader
from serial import Serial
from usrp import USRP
from gps import GPS
from aiming import RAiming
from pytictoc import TicToc
from filewriter import FileCSV



try:
    gps = GPS(port="COM4", baudrate=19200, timeout=0.1)
    gps.startGPSThread()
    # sleep(5)
    while True:
        if gps.gps_data is not None:
            print(gps.formatGPSData())
        
except KeyboardInterrupt:
    print("Ctrl + c -> Stop reading position!!!")

finally:
    print("End of the program")
    gps.stopGPSThread()
