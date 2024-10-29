'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of the acquisition of GPS data
                and format raw data from UBX protocol it to the required format.
'''



import contextlib
import threading
from time import sleep
from serial import Serial
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
from pytictoc import TicToc

class GPS:
    
    def __init__(self, port = 'COM7', baudrate = 19200, timeout = 0.1, type="all"):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.ubxr = UBXReader(BufferedReader(self.serial), protfilter=UBX_PROTOCOL)
        self.msg_class = "NAV"
        self.msg_id = {"abs": "NAV-POSLLH", "rel": "NAV-RELPOSNED"}
        # self.msg_id_1 = "NAV-RELPOSNED"     # relative coordinates 
        # self.msg_id_2 = "NAV-POSLLH"        # abs coordinates

        # Choosing NAV type
        self.msg = []
        if type in self.msg_id:
            self.msg.append(UBXMessage(self.msg_class, self.msg_id[type], GET, SET))
        elif type == "all":
            for value in self.msg_id.values():
                self.msg.append(UBXMessage(self.msg_class, value, GET, SET))
        else:
            self.msg = None
            raise ValueError("Unrecognized acquisition type, only 'abs', 'rel' , 'all' are valid.")

        # self.msg_2 = UBXMessage(self.msg_class, self.msg_id_2, GET, SET)
        # self.msg_1 = UBXMessage(self.msg_class, self.msg_id_1, GET, SET)

        #Attribute who stores the most recent data
        self.gps_data = None

        # Attributes needed for threading
        self.gps_thread = None                  # Continuous GPS reading thread
        self.continuous_reading = False     # Continuous GPS reading flag

    def readGPSMessages(self):
        # global parsed_data
        parsed_data = None
        if self.serial.in_waiting:
            with contextlib.suppress(Exception):
                (raw_data, parsed_data) = self.ubxr.read()
        return parsed_data
    
    def sendGPSMessage(self):
        for msgidx in self.msg:
            self.serial.write(msgidx.serialize())
        # self.serial.write(self.msg_1.serialize())
        # self.serial.write(self.msg_2.serialize())

    def receiveFromGPS(self):
        gps_data = None
        while gps_data is None:
            self.sendGPSMessage()
            gps_data = self.readGPSMessages()
            sleep(0.005)
        self.gps_data = gps_data
        return self.gps_data
    
    def continuousGPSReading(self):
        while self.continuous_reading:
            self.receiveFromGPS()
    
    # Call this function each time you want to save the GPS data
    def format_rel_GPSData(self):
        #if self.gps_data is not None:
        #print('\n', self.gps_data, self.gps_data.relPosN, '\n')
        if hasattr(self.gps_data, 'relPosN'):
            distance_N = (self.gps_data.relPosN)/100
            distance_E = (self.gps_data.relPosE)/100
            distance_D = (self.gps_data.relPosD)/100
            coordinates = [distance_N, distance_E, distance_D, 'relPos']
        if hasattr(self.gps_data, 'lon'):
            coordinates = [self.gps_data.lon, self.gps_data.lat, self.gps_data.height, 'absPos']
        
        #coordinates = np.append(relative_coordinates, abs_coordinates)
        return coordinates
    
    # DEPRECATED FUNCTION : format_abs_GPSData since 31/07/2024
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
    
