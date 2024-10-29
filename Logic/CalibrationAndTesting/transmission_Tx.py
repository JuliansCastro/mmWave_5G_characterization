'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: Basic script to transmit a signal using USRP.
'''


import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

import sys
import usrp
import numpy as np
from tkinter import *


freq = 500e6
duration = 1200                        #in seconds
t = np.linspace(0,1/freq, 2000)
tx_signal = np.ones([1,1000000]) # np.cos(2*np.pi*freq*t)

try:
    usrp_UT = usrp.USRP(tx_center_freq=freq, tx_gain=70)
    usrp_UT.setTransmitter()
    usrp_UT.sendSignal(signal=tx_signal, tx_duration=duration)
    
except KeyboardInterrupt:
    # Send EOB to terminate TX
    usrp_UT.tx_metadata.end_of_burst = True
    usrp_UT.tx_streamer.send(np.zeros((1,1), dtype=np.complex64), usrp_UT.tx_metadata)
    usrp_UT.tx_streamer = None
    
finally:
    print("\n\nTransmission finished.")




