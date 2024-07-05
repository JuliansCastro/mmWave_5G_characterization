import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

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
from aiming import RAiming
from pytictoc import TicToc
from filewriter import FileCSV

def doubleThreading() -> None:
    frequency = 500e6
    gain_rx = 24.7
    aim_port = "COM3"
    aim_baudrate = 19200

    usrp_UT = USRP(rx_center_freq=frequency, rx_gain=gain_rx)
    aiming_UT = RAiming(baudrate=aim_baudrate, serial_port=aim_port)
    t = TicToc()


    try:
        usrp_UT.startRxThread()
        aiming_UT.startAimingThread()
        while True:
            t.tic()
            bw_data=[]
            powerRx = usrp_UT.getPower_dBm(usrp_UT.rx_samples)
            bw_data += aiming_UT.aiming_data
            bw_data.append(powerRx)
            t.toc()
            sleep(0.030)
            print(bw_data)
    except KeyboardInterrupt:
        print('\nCtrl + C -> Interrupted!')
        usrp_UT.stopRxThread()
        aiming_UT.stopAimingThread()
        print("T1: ", usrp_UT.rx_thread, "T2: ", aiming_UT.aiming_thread)
    finally:
        usrp_UT.stopRxStream()

def oneShotAim():
    # Elapsed time: +- 12ms
    frequency = 500e6
    gain_rx = 24.7
    aim_port = "COM3"
    aim_baudrate = 19200

    usrp_UT = USRP(rx_center_freq=frequency, rx_gain=gain_rx)
    aiming_UT = RAiming(serial_port=aim_port, baudrate=aim_baudrate)
    t = TicToc()

    # bw_file = FileCSV(name="Measures\\BWMeasure\\USRP01", frequency=None, header=["XZ","YZ", "MAG", "PowerRx"], type="BW_MEAS")
    bw_file = FileCSV(name="Data/BeamWidth/USRP01", frequency=None, header=["XZ","YZ", "MAG", "PowerRx"], type="BW_MEAS")

    try:
        usrp_UT.startRxThread()
        while True:
            t.tic()
            powerRx = usrp_UT.getPower_dBm(usrp_UT.rx_samples)
            bw_data = aiming_UT.getAiming()
            bw_data.append(powerRx)
            t.toc()
            print(bw_data)
            bw_file.saveData(bw_data)
    except KeyboardInterrupt:
        print('\nCtrl + C -> Interrupted!')
        usrp_UT.stopRxThread()
        aiming_UT.serial.close()
        print("T1: ", usrp_UT.rx_thread, "T2: ", aiming_UT.aiming_thread)
    finally:
        usrp_UT.stopRxStream()

if __name__ == "__main__":
    oneShotAim()