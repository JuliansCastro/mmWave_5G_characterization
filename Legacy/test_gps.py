'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: test GPS data reading without saving it.
'''


# Route needed by python interpreter to read project's custom classes
# Add the path to the 'Modules' directory to the PYTHONPATH
import os
import sys
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'Modules')))

#from gps import GPS
from gps import GPS
from time import sleep
from pytictoc import TicToc


gps_port = "COM4"

try:
    timer = TicToc()
    gps_rtk = GPS(port=gps_port, baudrate=19200, timeout=0.1, type='rel')
    
    gps_rtk.startGPSThread()
    
    sleep(5)
    timer.tic()
    counter = 0
    while True:
        print(counter, gps_rtk.format_rel_GPSData())
        #print(counter, gps_rtk.format_abs_GPSData())
        counter += 1
        #timer.toc()
        if timer.tocvalue() >= 60.0:
            break
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
