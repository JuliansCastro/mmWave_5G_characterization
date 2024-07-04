import uhd
import csv
import numpy as np
import scipy.io as sio
from tkinter import *
from tkinter import ttk
from datetime import datetime 
from time import sleep
from io import BufferedReader
from threading import Lock
from serial import Serial
from pyubx2 import ( 
    UBXMessage ,
    UBXReader ,
    UBX_MSGIDS,
    UBX_PROTOCOL,
    SET,
    GET,
    POLL
)


# USRP
#-----------------------------------------------------------------------------------------
# USRP configuration for 'B200', 'B210'
master_clock_rate = 20e6                            # Hz
sample_rate = 2e6                                   # sps
decimation_factor = master_clock_rate/sample_rate   
center_freq = 500e6 + 0.0000e6                      # Nominal RF receive center frequency
gain = 0                                            # dB
channel_mapping = 0
num_samps = 2**12                                   # number of samples received per frame 2^12 = 4096,  ^23
buffer_length = 2**10                               # must be less than number samples and power of 2


#-----------------------------------------------------------------------------------------
# GPS Modules configuration

# Serial comm configuration
port_accel = "COM13"  # COM13 is accel sensor module
port_GPS = "COM7"  # COM7 is Rx module
baudrate = 19200
timeout = 0.1
serial_lock = Lock()

# GPs navigation mode
msg_class = "NAV"
msg_id = "NAV-RELPOSNED"


def read_messages( stream , lock , ubxreader) :
    global parsed_data
    if stream.in_waiting:
        try:
            lock.acquire()
            (raw_data , parsed_data) = ubxreader.read()
            lock.release()
            if parsed_data:
                pass
        except Exception as err:
            pass
    return parsed_data

def send_message(stream, lock, message):
    lock.acquire()
    stream.write(message.serialize())
    lock.release()

def receiveFromGPS(stream, lock, message, ubxreader):
    dataFromGPS = None
    while dataFromGPS is None:
        send_message(stream, serial_lock, message)
        dataFromGPS = read_messages ( stream , lock , ubxreader )
        sleep(0.001)
    return dataFromGPS


def read_accel_mag(serial):
    accel_mag_values = []
    serial_lock.acquire()
    if serial.in_waiting > 0:
        serial.reset_input_buffer()
        # Read a line from the serial port
        str_line = serial.readline().decode('utf-8').strip().split(',')

        # Verify that the line has three values
        if len(str_line) == 3:
            # Casting each value individually
            accel_mag_values = [float(value) for value in str_line]

        else:
            #print(f"Línea con formato incorrecto: {line}")
            accel_mag_values =[None, None, None]
    serial_lock.release()
    
    return accel_mag_values


def main():
    try:
        #-------------------------------------------------------------------------------------
        # serial comm initialization
        serial_accel = Serial(port_accel, baudrate)
        # serial_GPS = Serial(port_GPS, baudrate, timeout=timeout)
        # ubr = UBXReader(
        #     BufferedReader(serial_GPS),
        #     protfilter=UBX_PROTOCOL
        #     )
        
        # msg = UBXMessage(
        #     msg_class,
        #     msg_id,
        #     GET
        # )
        # send_message(serial_GPS, serial_lock, msg)
        sleep(1)

        
        
        #aiming = np.zeros(3)
        idx = 0
        while idx < 100:
            # dataGPS = receiveFromGPS(serial_GPS, serial_lock, msg, ubr)
            # position = [dataGPS.relPosN/100, dataGPS.relPosE/100, dataGPS.relPosD/100]
            aiming = np.array((read_accel_mag(serial_accel))) # 1. Angle XZ, 2. Angle Yz, 3. Heading
            idx += 1
            sleep(0.1) # check and activate if any data is not captured

        # print(aiming,'\n')


        '''
        while True:
            # Lectura y muestra del GPS
            dataGPS = receiveFromGPS(serial_GPS, serial_lock, msg, ubr)
            #print(dataGPS,'\n')
            disN = (dataGPS.relPosN #+ dataGPS.relPosHPN * 1e-2 
            )/1000
            disE = (dataGPS.relPosE #+ dataGPS.relPosHPE * 1e-2
            )/1000
            disD = (dataGPS.relPosD #+ dataGPS.relPosHPD * 1e-2
            )/1000
            GPS = [disN, disE, disD]
            print("Dis N, E, D: ", GPS)
            sleep(1)
        
        '''

        
        # SDRu Receiver System object
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

        #-------------------------------------------------------------------------------------
        # Data Capture
        print("\nInicia lectura\n")

        loop_index = 0
        while loop_index < 1000:
            
            # Receive Samples
            rx_samples = np.zeros(num_samps, dtype=np.complex64)
            reading_accel = read_accel_mag(serial_accel)
            # print('position; ', position)
            for i in range(num_samps//buffer_length):
                streamer.recv(recv_buffer, metadata)
                rx_samples[i*buffer_length:(i+1)*buffer_length] = recv_buffer[0]  #Save every pow of 2 samples
            
            if loop_index == 0:
                rx_data = rx_samples
                # dataGPS = receiveFromGPS(serial_GPS, serial_lock, msg, ubr)
                # position = np.array(([dataGPS.relPosN/100, dataGPS.relPosE/100, dataGPS.relPosD/100]))  # relpos in cm -> m
                # print('relp N, E, D: ', dataGPS, position)
                aiming = np.array((read_accel_mag(serial_accel)))
            else:
                rx_data = np.column_stack((rx_data,rx_samples))
                # dataGPS = receiveFromGPS(serial_GPS, serial_lock, msg, ubr)
                # position = np.column_stack((position, [dataGPS.relPosN/100, dataGPS.relPosE/100, dataGPS.relPosD/100]))  # relpos in cm -> m
                # print('relp N, E, D: ', dataGPS, position)
                reading_accel = read_accel_mag(serial_accel)
                aiming = np.column_stack((aiming, reading_accel))

            loop_index += 1
            print('Frames: {}, Aiming: {}'.format(loop_index, reading_accel))
            sleep(0.31)

    

    except KeyboardInterrupt:
        print("\nCtrl + C -> Termina lectura\n")
        
    finally:
        # Stop Stream
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        streamer.issue_stream_cmd(stream_cmd)

        # Stop comm serial
        #serial_GPS.close()
        serial_accel.close()
        #-------------------------------------------------------------------------------------
        # Data writer
        filename = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
        #data = {'rx_data': rx_data, 'position': position, 'aiming': aiming}         # for save in Matlab file use a dict
        data = {'rx_data': rx_data, 'aiming': aiming}
        sio.savemat(f'./5gLoss_py/data/{filename}_usrp_accel.mat', data)
        print(f'\nSave data: {filename}_usrp_accel.mat\n')

        # Show data in terminal
        print('r_type: ', type(rx_samples))
        print('N. muestras: ', len(rx_samples))
        print(data)
        #EOS

    

if __name__ == '__main__':
    main()



# def gui():
#     '''
#     #-------------------------------------------------------------------------------------
#     # GUI control
#     root = Tk()
#     root.title('Pathloss measurement Control')
#     frm = ttk.Frame(root, padding=100)
#     frm.grid()

#     # Buttons
#     label_loop = ttk.Label(frm, text="Control loop").grid(column=0, row=0)
#     run_button = ttk.Button(frm, text="Start", command=start(False))
#     run_button.grid(column=1, row=0)
#     ttk.Label(frm, text="").grid(column=0, row=2)
#     ttk.Label(frm, text="Cerrar  ").grid(column=0, row=3)
#     ttk.Button(frm, text="Quit", command=lambda:[stop, root.destroy]).grid(column=1, row=3)
#     root.mainloop()
#     '''
#     pass