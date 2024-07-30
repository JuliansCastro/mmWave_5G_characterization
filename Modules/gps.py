import threading
from time import sleep
from io import BufferedReader
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

class GPS:
    
    def __init__(self, port = 'COM7', baudrate = 19200, timeout = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.ubxr = UBXReader(BufferedReader(self.serial), protfilter=UBX_PROTOCOL)
        self.msg_class = "NAV"
        self.msg_id_1 = "NAV-RELPOSNED"     # realtive coordinates 
        self.msg_id_2 = "NAV-POSLLH"        # abs coordinates 
        self.msg = UBXMessage(self.msg_class, self.msg_id_2, GET, SET)

        self.gps_data = None

        # Attributes needed for threading
        self.gps_thread = None                  # Continuous GPS reading thread
        self.continuous_reading = False     # Continuous GPS reading flag

    def readGPSMessages(self):
        # global parsed_data
        parsed_data = None
        if self.serial.in_waiting:
            try:
                (raw_data, parsed_data) = self.ubxr.read()
            except Exception as err:
                pass
        return parsed_data
    
    def sendGPSMessage(self):
        self.serial.write(self.msg.serialize())

    def recieveFromGPS(self):
        gps_data = None
        while gps_data is None:
            self.sendGPSMessage()
            gps_data = self.readGPSMessages()
            sleep(0.005)
        self.gps_data = gps_data
        return self.gps_data
    
    def continuousGPSReading(self):
        while self.continuous_reading:
            self.recieveFromGPS()
    
    # Call this function each time you want to save the GPS data
    def formatGPSData(self):
        #if self.gps_data is not None:
        distance_N = (self.gps_data.relPosN)/100
        distance_E = (self.gps_data.relPosE)/100
        distance_D = (self.gps_data.relPosD)/100
        relative_coordinates = [distance_N, distance_E, distance_D]
        return relative_coordinates
    
    def format_abs_GPSData(self):
        try:
            #print(self.gps_data)
            abs_coordinates = [self.gps_data.lon, self.gps_data.lat, self.gps_data.height]
        except AttributeError:
            abs_coordinates = [0,0,0]
        return abs_coordinates
        
    
    def startGPSThread(self):
        self.continuous_reading = True
        self.gps_thread = threading.Thread(target=self.continuousGPSReading, name="GPS_THREAD", daemon=True)
        self.gps_thread.start()
    
    def stopGPSThread(self):
        self.continuous_reading = False
        self.gps_thread.join()
        self.serial.close()
    
