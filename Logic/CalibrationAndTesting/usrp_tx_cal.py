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

def continueMeasure():
    continue_measure = input("Would you like to continue measuring? (Y/n)\n").lower()

    if continue_measure == "n":
        print("Closing system...")
        sys.exit()
    elif continue_measure == "y":
        pass
    else:
        continueMeasure()


if __name__ == "__main__":


    SA_SETTINGS = {
                # Start and stop frequencies of the horizontal axis of the diagram area, for more information 
                # about its settings refer to page 107 (109) of the user manual
                "START": 400e6,
                "STOP": 600e6, 

                "STEP": 200e3, # Frequency step size, for more information about its settings refer to page 105 (107) of the user manual
                "SPAN": 200e6, # Frequency range around the center frequency that a spectrum analyzer displays on the screen,
                # for more information about its settings refer to page 107 (109) of the user manual

                "RANGE": 80, # Determines the scaling or resolution of the vertical axis. For more information about its settings refer
                # to page 110 (112) of the user manual
                "RLEVEL": 5, # The reference level sets the input signal gain up to the display stage. If the reference level is
                # low, the gain is high. For more information about its settings refer to page 109 (111) of the user manual
                "ATTENUATION": 15, # RF attenuation adjusts the input range inside the analyzer. It is coupled directly to the
                # reference level. For more information about its settings refer to page 111 (113) of the user manual

                "RBW": 100e3, # The resolution bandwidth in a spectrum analyzer determines the frequency resolution
                # for frequency domain measurements and therefore determines how well it can separate adjacent frequencies.
                # For more information about its settings refer to page 112 (114) of the user manual

                #doesn't seem to be used
                "VBW": 30e3 # The video bandwidth (VBW) basically smoothes the trace by reducing the noise and therefore 
                # making power levels easier to see. For more information about its settings refer to page 115 (117) of the user manual
                }

    # Creation of the file
    tx_name = "Measures\\TxCalibration\\USRP05"
    tx_header = ["Tx Power", "Tx Gain"]
    freq = 500e6

    cal_file = FileCSV(tx_name, freq, tx_header) 

    # FSH8 Espectrum analyzer object
    espectrum_analyzer = instrument.RSSpectrumAnalyzer("172.177.75.23",SA_SETTINGS)
    # Ensure FSH8 is set in espectrum analyzer mode
    espectrum_analyzer.set_inst_mode()
    # Configure instrument 
    espectrum_analyzer.set_instrument()
    # Verify configuration
    espectrum_analyzer.print_configuration()

    # User must be sure about settings
    continueMeasure()

    # Create usrp object (usrp Under Test)
    # Default settings are being used
    usrpUT = usrp.USRP(center_freq=freq)

    # Pasos para la ganancia
    steps = 10
    gain_range = np.round(np.linspace(0, 80, steps),1)






