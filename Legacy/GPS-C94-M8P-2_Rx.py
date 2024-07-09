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
from pytictoc import TicToc

t = TicToc()

##########################################################################################

############### Modulos GPS ###############

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


############### Modulos GPS ###############

port = "COM5"  # COM7 is Rx module
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


 #################################################################
 ######################## Ciclo de lectura #######################

try:
    print("\nInicia lectura\n")
    dataGPS = receiveFromGPS(serial, serial_lock, msg, ubr)
    
    count_errors = 0
    count_loop = 0

    while True:
        #input("?")
        # Lectura y muestra del GPS
        t.tic()
        dataGPS = receiveFromGPS(serial, serial_lock, msg, ubr)
        #print(dataGPS,'\n')

        # P(114-doc-REceiver description)
        # North, East and Down distante to relative position
        # 'NAV-RELPOSNED' mode. Results in cm and relposHP in mm
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
    print("\nCtrl + C -> Termina lectura\n")

finally:
    print('eventos fuera tiempo: ', count_errors)
    print('total eventos: ', count_loop)
    print('Tasa', count_errors/count_loop)


'''
eventos fuera tiempo:  30
total eventos:  1321
Tasa 0.022710068130204392
'''



'''
eventos fuera tiempo:  39
total eventos:  18050
Tasa 0.0021606648199445984
'''