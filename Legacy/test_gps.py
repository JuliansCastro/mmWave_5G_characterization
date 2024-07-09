import sys
sys.path.append('C:/Users/JuliansCastro/Documents/5G_characterization/Modules')

from time import sleep
from gps import GPS
from pytictoc import TicToc


gps_port = "COM8"

try:
    timer = TicToc()
    gps_rtk = GPS(port=gps_port, baudrate=19200, timeout=0.1)
    gps_rtk.startGPSThread()
    # sleep(5)
    timer.tic()
    counter = 0
    while True:        
        if gps_rtk.gps_data is not None:
            print(counter, gps_rtk.formatGPSData())
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
