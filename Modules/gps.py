'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of the acquisition of GPS- RTK (u-blox C94-M8P 2) data
                and format raw data from UBX protocol it to the required format
                for Rover position.
'''

import threading
import contextlib
import numpy as np
from time import sleep
from serial import Serial
from datums import DATUMS
from pytictoc import TicToc
from io import BufferedReader
from pyubx2 import (
    UBXMessage,
    UBXReader,
    UBX_MSGIDS,
    UBX_PROTOCOL,
    SET,
    GET,
    POLL,
    ERR_IGNORE,
    haversine,
)

class GPS:
    '''
    A class to interface with a GPS module for reading and processing GPS data.

    This class manages the communication with a GPS device, allowing for the retrieval of both absolute and relative position data. It supports continuous reading of GPS messages and provides methods to format the received data.

    Args:
        port (str): The serial port to which the GPS device is connected. Default is 'COM7'.
        baudrate (int): The baud rate for the serial communication. Default is 19200.
        timeout (float): The timeout for serial communication in seconds. Default is 0.1.
        type (str): The type of GPS messages to read ('abs', 'rel', or 'all'). Default is 'all'.

    Attributes:
        gps_data: Stores the most recent GPS data received.
        gps_thread: Thread for continuous GPS reading.
        continuous_reading (bool): Flag indicating if continuous reading is active.

    Methods
    -------
        readGPSMessages() -> 'UBXMessage' | None:
            Reads and parses GPS messages from the device via UBX protocol.
        sendGPSMessage() -> None:
            Sends configured GPS messages to the device.
        receiveFromGPS() -> 'UBXMessage':
            Continuously sends messages and retrieves GPS data until valid data is received.
        continuousGPSReading() -> None:
            Continuously reads GPS data while the reading flag is set.
        format_rel_GPSData() -> List: 
            Formats and returns relative GPS data as a list.
        format_abs_GPSData() -> List: 
            Formats and returns absolute GPS data as a list.
        startGPSThread() -> None:
            Starts a thread for continuous GPS reading.
        stopGPSThread() -> None:
            Stops the continuous GPS reading thread and closes the serial connection.
    '''
    
    def __init__(self, port = 'COM7', baudrate = 19200, timeout = 0.1, type="all"):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.ubxr = UBXReader(BufferedReader(self.serial), protfilter=UBX_PROTOCOL, quitonerror=ERR_IGNORE)
        self.msg_class = "NAV"
        self.msg_id = {"abs": "NAV-HPPOSLLH", "rel": "NAV-RELPOSNED"}
        #self.msg_id = {"abs": "NAV-POSLLH", "rel": "NAV-RELPOSNED"}

        # Choosing NAV type
        self.msg = []
        if type in self.msg_id:
            self.msg.append(UBXMessage(self.msg_class, self.msg_id[type], GET))
        elif type == "all":
            self.msg.extend(
                UBXMessage(self.msg_class, value, GET)
                for value in self.msg_id.values()
            )
        else:
            self.msg = None
            raise ValueError("Unrecognized acquisition type, only 'abs', 'rel' , 'all' are valid.")

        #Attribute who stores the most recent data
        self.gps_data = None

        # Attributes needed for threading
        self.gps_thread = None              # Continuous GPS reading thread
        self.continuous_reading = False     # Continuous GPS reading flag

    def readGPSMessages(self):
        """Reads and parses GPS messages from the C94-M8P-2 device.

        This function checks  if there are any incoming messages from the
        GPS device and attempts to read and parse them. If successful, it
        returns the parsed data; otherwise, it returns None.

        Returns:
            Parsed GPS data if available, otherwise None.
        """
        # global parsed_data
        parsed_data = None
        if self.serial.in_waiting:
            with contextlib.suppress(Exception):
                (raw_data, parsed_data) = self.ubxr.read()
        return parsed_data
    
    def sendGPSMessage(self):
        '''
        Sends configured GPS messages to the C94-M8P-2 device .

        This function iterates through the list of messages prepared
        for transmission and sends each one to the GPS device via the
        serial connection. It ensures that the necessary messages are 
        communicated to the device for proper operation.

        Returns:
            None
        '''
        for msgidx in self.msg:
            self.serial.write(msgidx.serialize())

    def receiveFromGPS(self):
        '''Continuously retrieves GPS data from the device.

        This function sends GPS messages to the device and 
        waits for a valid response. It continues this process
        until valid GPS data is received, which is then stored
        for further use.

        Returns:
            'UBXMessage': The retrieved GPS data once available.
        '''
        
        gps_data = None
        while gps_data is None:
            self.sendGPSMessage()
            gps_data = self.readGPSMessages()
            sleep(0.005)
        self.gps_data = gps_data
        return self.gps_data
    
    def continuousGPSReading(self):
        '''
        Continuously reads GPS data while the reading flag is active.

        This function enters a loop that repeatedly calls the method to receive
        GPS data as long  as the continuous reading flag is  set to True. It is 
        intended for use in a separate thread to allow for ongoing data collection.

        Returns:
            None
        '''
        
        while self.continuous_reading:
            self.receiveFromGPS()
    
    # Call this function each time you want to save the GPS data
    def format_GPSData(self):
        '''
        Formats and returns the relative or absolute GPS data.

        This function checks the available GPS data and formats it into a list of coordinates.
        It can return either relative position data or absolute position data based on the 
        attributes present in the GPS data.

        Returns:
            list:   A list containing the formatted GPS coordinates and their type ('relPos').
                    Here, the coordinates are in the order [North, East, Down, accN, accE, accD, 'relPos'] in meters (cm/100).
                    Here, the coordinates are in the order [lon, lat, height, hAcc, vAcc, 'absPos'] in millimeters (mm/1000).
        '''
        
        #if self.gps_data is not None:
        # print('\n', self.gps_data, '\n')
        if hasattr(self.gps_data, 'relPosN'):
            # print(self.gps_data) # Caution: Print generates an error.
            coordinates = [self.gps_data.relPosN,   # cm
                           self.gps_data.relPosE,   # cm
                           self.gps_data.relPosD,   # cm
                           self.gps_data.accN,  # mm
                           self.gps_data.accE,  # mm
                           self.gps_data.accD,  # mm
                           'relPos']
        elif hasattr(self.gps_data, 'lon'):
            # print(self.gps_data) # Caution: Print generates an error.
            coordinates = [self.gps_data.lon,
                           self.gps_data.lat,
                           self.gps_data.height,
                           self.gps_data.hMSL, # mm
                           self.gps_data.hAcc, # mm
                           self.gps_data.vAcc, # mm
                           'absPos']
        return coordinates
    
    def haversine_dist(self, lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two geographic points using the Haversine formula.
        Using default WGS84 datum.
        
        Args:
            lat1, lon1: Latitude and longitude of the first point (in degrees)
            lat2, lon2: Latitude and longitude of the second point (in degrees)
        
        Returns:
            float: Distance in meters

        http://www.movable-type.co.uk/scripts/latlong.html
        
        """
        # Refer to DATUMS.py in the /examples folder for list of common
        # international datums with semi-major axis, flattening and
        # delta_x,y,z reference values
        
        # DATUM = 'Bogota_Observatory'
        # datum_dict = DATUMS[DATUM]
        # ellipsoid, a, f, delta_x, delta_y, delta_z = datum_dict.values()
        # return haversine(lat1, lon1, lat2, lon2, radius=a) # return esferical distance in km
        
        # return esferical distance in km using default WGS84 datum
        return haversine(lat1, lon1, lat2, lon2)

    def startGPSThread(self):
        '''
        Starts a thread for continuous GPS reading.

        This function sets the continuous reading flag to True and initiates 
        a new thread that runs the continuous GPS reading process. It allows 
        for asynchronous data collection from the GPS device without blocking
        the main program flow.

        Returns:
            None
        '''
        self.continuous_reading = True
        self.gps_thread = threading.Thread(target=self.continuousGPSReading, name="GPS_THREAD", daemon=True)
        self.gps_thread.start()
    
    def stopGPSThread(self):
        '''
        Stops the continuous GPS data reading thread.

        This function sets the continuous reading flag to False, waits for the GPS reading thread
        to finish, and then  closes the serial connection to  the GPS device. It ensures that all 
        resources are properly released and that the data collection process is halted.

        Returns:
            None
        '''
        self.continuous_reading = False
        self.gps_thread.join()
        self.serial.close()
    
