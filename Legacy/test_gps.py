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

timer = TicToc()

try:
    gps_rtk = GPS(port="COM5", baudrate=19200, timeout=0.1)
    gps_rtk.startGPSThread()
    # sleep(5)
    timer.tic()
    counter = 0
    while True:        
        if gps_rtk.gps_data is not None:
            print(gps_rtk.formatGPSData())
            counter += 1
            #timer.toc()
        if timer.tocvalue() >= 60.0:
            break
    #timer.toc()
        
except KeyboardInterrupt:
    print("Ctrl + c -> Stop reading position!!!")

finally:
    print("End of the program")
    print("Time elapsed: ", timer.tocvalue())
    print("Number of readings: ", counter)
    print("Reading rate: ", counter/timer.tocvalue(), "M/s.\t", 1000*timer.tocvalue()/counter, "ms/M.")
    gps_rtk.stopGPSThread()
