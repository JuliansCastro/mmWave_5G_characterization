import uhd
import time
import csv
import numpy as np
import scipy.io as sio
import instrument
import usrp
import sys
from tkinter import *
from tkinter import ttk
from datetime import datetime 
from filewriter import FileCSV

freq = 500e6
duration = 300                        #in seconds
t = np.linspace(0,1/freq, 2000)
tx_signal = np.ones([1,1000000]) # np.cos(2*np.pi*freq*t)


usrp_UT = usrp.USRP(tx_center_freq=freq, tx_gain=70)

usrp_UT.setTransmitter()
usrp_UT.sendSignal(signal=tx_signal, tx_duration=duration)

