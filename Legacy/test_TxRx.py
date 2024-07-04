import uhd
import numpy as np


usrp = uhd.usrp.MultiUSRP()

num_samps = 10000 # number of samples received
center_freq = 500e6 # Hz
sample_rate = 1e6 # Hz
gain = 89 # [dB] start low then work your way up 80db{-8dBm(mini)}  60.5dB{0dBm doble}
duration = 15 # seconds

# Transmition
#samples = 0.1*np.random.randn(num_samps) + 0.1j*np.random.randn(num_samps) # create random signal

#Creando un array de mil valores con numpy, de t=0 a t=0.5
t = np.linspace(0,1/center_freq,2000)
#Generando una funcion seno, con amplitud unitaria
samples = 0.1*np.sin(2*np.pi*center_freq*t)


usrp.send_waveform(samples, duration, center_freq, sample_rate, [0], gain)



# # Reception
# usrp.set_rx_rate(sample_rate, 0)
# usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), 0)
# usrp.set_rx_gain(gain, 0)

# # Set up the stream and receive buffer
# st_args = uhd.usrp.StreamArgs("fc32", "sc16")
# st_args.channels = [0]
# metadata = uhd.types.RXMetadata()
# streamer = usrp.get_rx_stream(st_args)
# recv_buffer = np.zeros((1, 1000), dtype=np.complex64)

# # Start Stream
# stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
# stream_cmd.stream_now = True
# streamer.issue_stream_cmd(stream_cmd)

# # Receive Samples
# samples = np.zeros(num_samps, dtype=np.complex64)
# for i in range(num_samps//1000):
#     streamer.recv(recv_buffer, metadata)
#     samples[i*1000:(i+1)*1000] = recv_buffer[0]

# # Stop Stream
# stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
# streamer.issue_stream_cmd(stream_cmd)

# print(len(samples))
# print(samples[0:10])


# '''
# [ 2.1362951e-04+3.0518502e-05j -9.1555507e-05+0.0000000e+00j
#  -1.8311101e-04+3.0518502e-05j  3.0518502e-05+1.5259252e-04j
#   9.1555507e-05-1.5259252e-04j -6.1037004e-05-6.1037004e-05j
#   6.1037004e-05+0.0000000e+00j  3.0518502e-05+3.0518502e-05j
#   9.1555507e-05+2.1362951e-04j  1.2207401e-04-9.1555507e-05j]

#   [ 0.0000000e+00-1.5259252e-04j  1.5259252e-04+6.1037004e-05j
#   3.0518504e-04+3.0518502e-05j -3.0518502e-05+1.2207401e-04j
#  -6.1037004e-05+1.2207401e-04j -9.1555507e-05+1.2207401e-04j
#  -3.0518504e-04-6.1037004e-05j  1.8311101e-04+9.1555507e-05j
#   3.0518502e-05-1.2207401e-04j -1.5259252e-04+3.0518502e-05j]

# '''