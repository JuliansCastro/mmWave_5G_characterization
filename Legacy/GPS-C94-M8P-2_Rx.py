'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description: {File Description}
'''



import contextlib
from time import sleep
from serial import Serial
from threading import Lock
from pytictoc import TicToc
from io import BufferedReader
from pyubx2 import ( 
    UBXMessage ,
    UBXReader ,
    UBX_MSGIDS,
    UBX_PROTOCOL,
    SET,
    GET,
    POLL
)


t = TicToc()


############### Modules GPS ###############

def read_messages( stream , lock , ubxreader):
    global parsed_data
    if stream.in_waiting:
        with contextlib.suppress(Exception):
            lock.acquire()
            (raw_data , parsed_data) = ubxreader.read()
            lock.release()
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


############### Modules GPS ###############

port = "COM4"  # COM7 is Rx module
baudrate = 19200
timeout = 0.1

serial = Serial(port, baudrate, timeout=timeout)
ubr = UBXReader(
    BufferedReader(serial),
    protfilter=UBX_PROTOCOL
    )

serial_lock = Lock()
msg_class = "NAV"
msg_id = "NAV-RELPOSNED"

msg = UBXMessage(
    msg_class,
    msg_id,
    GET
)
send_message(serial, serial_lock, msg)
sleep(1)


 ######################## Reading cycle #######################

try:
    print("\nStart reading\n")
    dataGPS = receiveFromGPS(serial, serial_lock, msg, ubr)
    
    count_errors = 0
    count_loop = 0

    while True:
        #input("?")
        # GPS reading and display
        t.tic()
        dataGPS = receiveFromGPS(serial, serial_lock, msg, ubr)
        #print(dataGPS,'\n')

        # P(114-doc-REceiver description)
        # North, East and Down distance to relative position
        # 'NAV-RELPOSNED' mode. Results in cm and relpos HP in mm
        disN = (dataGPS.relPosN #+ dataGPS.relPosHPN * 1e-2 
        )/100
        disE = (dataGPS.relPosE #+ dataGPS.relPosHPE * 1e-2
        )/100
        disD = (dataGPS.relPosD #+ dataGPS.relPosHPD * 1e-2
        )/100
        
        GPS = [disN, disE, disD]
        print("Dis N, E, D: ", GPS)
        elapsed_time = t.tocvalue()
        print(elapsed_time)

        count_loop += 1
        if elapsed_time >= 0.017:
            count_errors += 1

        sleep(0.01666666669)

    serial.close()


except KeyboardInterrupt:
    print("\nCtrl + C -> Finish reading\n")

finally:
    print('Events out of time: ', count_errors)
    print('Total events: ', count_loop)
    print('Rate: ', count_errors/count_loop)
