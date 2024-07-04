import usrp
import numpy as np
import time
from pytictoc import TicToc
import threading
import instrument

rx_samples = []
freq = 500e6
gain = 22

usrpUT = usrp.USRP(rx_center_freq=freq, rx_gain=gain)
# # t = TicToc()
# rx_thread = threading.Thread(target=usrpUT._continuousRxSampling, daemon=True)

# num_frames = 20
# discard_frames = 10

# usrpUT.setReceiver()
# #usrpUT.setRecieveBuffer()
# usrpUT.startRxStream()


try:
    usrpUT.startRxThread()
    while True:
        print("Power dBm: ", usrpUT.getPower_dBm(usrpUT.rx_samples))
        print(usrpUT.rx_thread) 
        cont = input("Continue? ")
        if cont == "n":
            usrpUT.stopRxThread()
        # t.tic()
        # usrpUT.startRxStream()
        # samples = usrpUT.getSamples()
        # powerRx = usrpUT.getPower_dBm(samples)
        # print("Actual measure: ", powerRx)
        # usrpUT.stopRxStream()
        # t.toc()
        #time.sleep(0.01)
        # powerRx = 0
        # for i in range(num_frames):
        #     usrpUT.startRxStream()
        #     samples = usrpUT.getSamples()
        #     usrpUT.stopRxStream()
        #     if i >= discard_frames:                             # Discard outdated frames
        #         powerRx += usrpUT.getPower_dBm(samples)         # |Average over 
        # powerRx = powerRx/(num_frames-discard_frames)           # |updated frames
        # t.toc()
        # print("Actual measure: ", powerRx)
except KeyboardInterrupt:
    print('\nCtrl + C -> Interrupted!')
    usrpUT.stopRxStream()
finally:
    usrpUT.stopRxStream()

''' 30 samples frames and 10 discarded frames   ---> 66 ms elapsed time per measure
    Continuous measure                          ---> 1.02 ms elapsed time per meausre'''
