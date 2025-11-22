'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: Script to measure power in dBm using USRP step by step.
'''


import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

import usrp

rx_samples = []
freq = 500e6
gain = 20

usrpUT = usrp.USRP(rx_center_freq=freq, rx_gain=gain)

try:
    usrpUT.startRxThread()
    while True:
        print("Power dBm: ", usrpUT.getPower_dBm(usrpUT.rx_samples))
        print(usrpUT.rx_thread) 
        cont = input("Continue? ")
        if cont == "n":
            usrpUT.stopRxThread()
        
except KeyboardInterrupt:
    print('\n\nCtrl + C -> Interrupted!')
    usrpUT.stopRxStream()
finally:
    usrpUT.stopRxStream()

''' 30 samples frames and 10 discarded frames   ---> 66 ms elapsed time per measure
    Continuous measure                          ---> 1.02 ms elapsed time per meausre'''
