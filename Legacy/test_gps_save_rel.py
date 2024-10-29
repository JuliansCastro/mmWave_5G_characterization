'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: test and save GPS data of relative position in a CSV file.
'''


import sys
sys.path.append('../5G_CHARACTERIZATION/Modules')

from gps import GPS
from time import sleep
from pytictoc import TicToc
from filewriter import FileCSV


try:
    gps_port = "COM14"
    
    gps_file = FileCSV(name="Data/Meas_GPS/GPS", frequency=None, header=["pos1","pos2", "pos3", "pos_type"], type="MEAS")

    timer = TicToc()
    gps_rtk = GPS(port=gps_port, baudrate=19200, timeout=0.1)
    gps_rtk.startGPSThread()
    sleep(5)
    timer.tic()
    counter = 0
    while True:
        gps_data = gps_rtk.format_rel_GPSData()
        gps_file.saveData(gps_data)
        print(counter, gps_data)
        counter += 1
        #timer.toc()
        #if timer.tocvalue() >= 60.0:
        #    break
    #timer.toc()
        
except KeyboardInterrupt:
    print("\nCtrl + c -> Stop reading position!!!")
    print("End of the program")

finally:
    print("\nResults: ")
    print("Time elapsed: ", timer.tocvalue())
    print("Number of readings: ", counter)
    print("Reading rate: ", counter/timer.tocvalue(), "M/s.\t", 1000*timer.tocvalue()/counter, "ms/M.")
    gps_rtk.stopGPSThread()
