import uhd
import csv
import numpy as np
import scipy.io as sio
import instrument
from tkinter import *
from tkinter import ttk
from datetime import datetime 

#import configureFreqCalibRx as con_f_cal_Rx

#-----------------------------------------------------------------------------------------
# USRP configuration for 'B200', 'B210'
master_clock_rate = 20e6                            # Hz
sample_rate = 2e6                                   # sps
decimation_factor = master_clock_rate/sample_rate   
center_freq = 500e6 + 0.0000e6                      # Nominal RF receive center frequency
gain = 0                                         # dB
channel_mapping = 0                                 # USRP channel
num_samps = 2**12                                   # number of samples received per frame 2^12 = 4096
buffer_length = 2**10                               # must be less than number samples and power of 2 (1024)
num_frames = 100                                    # At least 2 frames
Z0 = 50                                             # USRP port impedance (assumed 50 Ohms)
powerdBm = []                                       

# SDRu Receiver System object

def main():
    #-------------------------------------------------------------------------------------
    # USRP initialization
    
    usrp = uhd.usrp.MultiUSRP()

    # Baseband and RF configuration
    usrp.set_master_clock_rate(master_clock_rate)
    usrp.set_rx_rate(sample_rate, channel_mapping)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), channel_mapping)
    usrp.set_rx_gain(gain, channel_mapping)

    # Set up the stream and receive buffer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = [channel_mapping]
    metadata = uhd.types.RXMetadata()
    streamer = usrp.get_rx_stream(st_args)
    recv_buffer = np.zeros((1, buffer_length), dtype=np.complex64)

    # Start Stream
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    loop_index = 0
    while loop_index < num_frames:
        # print('Frames: ', loop_index)
        # Receive Samples
        rx_samples = np.zeros(num_samps, dtype=np.complex64)
        for i in range(num_samps//buffer_length):
            streamer.recv(recv_buffer, metadata)
            rx_samples[i*buffer_length:(i+1)*buffer_length] = recv_buffer[0]  #Save every pow of 2 samples
        
        if loop_index == 0:
            rx_data = rx_samples
        else:
            rx_data = np.column_stack((rx_data,rx_samples))

        loop_index += 1

    # Stop Stream
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    streamer.issue_stream_cmd(stream_cmd)

    for i in range(num_frames):

        # Compute each frame's received power
        power_i = 10*np.log10(1e3*np.sum(np.square(np.abs(rx_data[:,i])))/(2*Z0*num_samps))
        # Save power measure
        powerdBm.append(power_i)

    # print('Received power [dBm]: ', powerdBm)
    av_power = np.sum(powerdBm)/num_frames
    print('Average power: ', av_power)





if __name__=="__main__":

    main()



    