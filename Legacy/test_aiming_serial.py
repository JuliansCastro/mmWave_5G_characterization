'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: test aiming data reading without saving it. Data is printed on console. 
               Data is read from a serial port, from Raspberry Pi Pico.
'''

# Route needed by python interpreter to read project's custom classes
# Add the path to the 'Modules' directory to the PYTHONPATH
import os
import sys
import numpy as np
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'Modules')))

import time
import pytictoc
import aiming


#this will store the time
t = pytictoc.TicToc()

#this will store the aiming
aim = aiming.RAiming(baudrate=19200,serial_port="COM8")

#this will store the line
line = []

try:
    while True:
        time.sleep(0.001)
        print(aim.getAiming())


except KeyboardInterrupt:
    print("\nctrl + C -> Close serial comm\n")
    print(f"Close connection on port: {aim.serial.portstr}\n")
    aim.serial.close()