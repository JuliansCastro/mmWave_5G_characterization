import uhd
import time
import csv
import numpy as np
import scipy.io as sio
import instrument
import usrp
from tkinter import *
from tkinter import ttk
from datetime import datetime 
import filewriter

if __name__=="__main__":

    # Creation of calibration file
    rx_name = "Measures\\RxCalibration\\USRP01" 
    rx_header = ["Each row has the same USRP gain, is a vector of measured power\n First row is the gen power range"]
    #rx_header = ["Gen Power", "Rx Power", "Rx Gain"]
    freq = 500e6

    cal_file = filewriter.FileCSV(rx_name,freq,rx_header)

    # Using default configuration
    usrpUT = usrp.USRP(rx_center_freq=freq)
    generator = instrument.RSGenerator("172.177.75.22",frequency=freq,power=-60)
    generator.on
    time.sleep(0.25)

    # Sweep settings
    gain_steps = 20     # Number of points of gain sweep
    gain_beg = 20       # Beginning of gain sweep
    gain_end = 30       # End of gain sweep
    power_steps = 20    # Number of points of power sweep
    power_beg = -40     # Beginning of power sweep
    power_end = -20     # End of power sweep
    gain_range = np.round(np.linspace(gain_beg,gain_end,gain_steps),1)
    power_range = np.round(np.linspace(power_beg, power_end, power_steps),1)
    discard_frames = 10
    num_frames = 30

    usrpUT.setReceiver()

    # for p in range(power_steps):

    #     # Generator power setter
    #     generator.power = power_range[p]
    #     time.sleep(0.2)

    #     for i in range(gain_steps):

    #         powerRx = 0
    #         usrpUT.updateRxGain(gain_range[i])
    #         time.sleep(0.25)
    #         # Create buffer and open stream only when a measure is needed
    #         # usrpUT.setReceiver()
    #         # usrpUT.setRecieveBuffer()
    #         for i in range(num_frames):
    #             usrpUT.startRxStream()
    #             samples = usrpUT.getSamples()
    #             usrpUT.stopRxStream()
    #             if i >= discard_frames:                             # Discard outdated frames
    #                 powerRx += usrpUT.getPower_dBm(samples)         # |Average over 
    #         powerRx = powerRx/(num_frames-discard_frames)           # |updated frames
    #         # usrpUT.startRxStream()
    #         # samples = usrpUT.getSamples()
    #         # powerRx = usrpUT.getPower_dBm(samples)
    #         # usrpUT.stopRxStream()
    #         # Must close the stream after the measure was performed to avoid buffer overflow
    #         cal_data = [generator.power,powerRx,usrpUT.rx_gain]
    #         print("Gen power: ", cal_data[0], "Rx power: ", cal_data[1], "Rx Gain: ", cal_data[2])
    #         # Save calibration data as CSV
    #         cal_file.saveData(cal_data)
    #         time.sleep(0.1)

    # generator.off

    gen_values = ["USRP Gain / Gen Power"]

    for p in range(power_steps):
        gen_values.append(power_range[p])

    cal_file.saveData(gen_values)

    for g in range(gain_steps):

        usrpUT.updateRxGain(gain_range[g])
        time.sleep(0.1)
        measured_power = []   # Measured power vector per USRP gain

        for p in range(power_steps):

            generator.power = power_range[p]
            time.sleep(1)
            powerRx = 0
            for i in range(num_frames):
                usrpUT.startRxStream()
                samples = usrpUT.getSamples()
                usrpUT.stopRxStream()
                if i >= discard_frames:                             # Discard outdated frames
                    powerRx += usrpUT.getPower_dBm(samples)         # |Average over 
            powerRx = powerRx/(num_frames-discard_frames)           # |updated frames
            time.sleep(0.2)
            print(powerRx)

            measured_power.append(powerRx)
        
        cal_data = [usrpUT.rx_gain] + measured_power
        print(len(cal_data))
        cal_file.saveData(cal_data)

    generator.off