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
import numpy as np
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'Modules')))

#from gps import GPS
from gps import GPS
from time import sleep
from pytictoc import TicToc


gps_port = "COM4"

try:
    timer = TicToc()
    gps_rtk = GPS(port=gps_port, baudrate=19200, timeout=0.1, type='all')
    
    gps_rtk.startGPSThread()
    
    sleep(5)
    timer.tic()
    

    start_position_abs = [-74.08198720, 4.639767, 2585.419]  # [lon, lat, alt]
    start_position_rel = [0,0,0]
    counter = 0
    
    while True:
        gps_data = gps_rtk.format_GPSData()
        if gps_data[5] == 'absPos':
            distance = gps_rtk.haversine_dist(start_position_abs[0], start_position_abs[1], gps_data[0], gps_data[1]) / 1000
        else:
            distance = (np.sqrt((gps_data[0] - start_position_rel[0])**2 + (gps_data[1] - start_position_rel[1])**2)) / 100 # Relative position is get in cm

        # if timer.tocvalue() < 8.0:
        #     start_position = distance
        #     print(f"Start position: {start_position:0.3f} cm")
        # else:
        #     print(f"Meassure: {counter}, Distance: {distance-start_position:0.3f} cm") 
        #     counter += 1
        #     #timer.toc()
        #     # if timer.tocvalue() >= 60.0:
        #     #     break
        #timer.toc()
        print(f"Meassure: {counter}, GPS Data: {gps_data}, Distance to start: {distance:0.3f} cm")
        counter += 1
        
except KeyboardInterrupt:
    print("\nCtrl + c -> Stop reading position!!!")
    print("End of the program")

finally:
    print("\nResults: ")
    print("Time elapsed: ", timer.tocvalue())
    print("Number of readings: ", counter)
    print("Reading rate: ", counter/timer.tocvalue(), "M/s.\t", 1000*timer.tocvalue()/counter, "ms/M.")
    gps_rtk.stopGPSThread()
