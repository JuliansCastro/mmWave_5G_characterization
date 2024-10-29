'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of the acquisition of aiming data, 
                it reads the serial port assigned to the Raspberry Pi Pico 
                and parse the data to the required format.
'''


import threading
from serial import Serial

class RAiming:
    """This class is in charge of the acquisition of aiming data,
    it reads the serial port assigned to the raspberry-Pi Pico
    and parse the data to the required format.
    """    
    def __init__(self, baudrate = 19200, serial_port = "COM3"):
        self.baudrate = baudrate
        self.serial_port = serial_port
        self.continuous_measure = False
        self.aiming_thread = None
        self.aiming_data = []
        self.serial = Serial(port = self.serial_port, baudrate = self.baudrate)


    def getAiming(self):
        """Get the values ​​of acceleration 'XZ', 'YZ' and magnetometer 'MAG'

        Returns:
            accel_mag_values {type:'list'}: ['XZ', 'YZ','MAG']
        """        
        accel_mag_values = []
        #if self.serial.in_waiting > 0:
        self.serial.reset_input_buffer()
        # Read a line from the serial port
        str_line = self.serial.readline().decode('utf-8').strip().split(',')

        return (
            [float(value) for value in str_line]
            if len(str_line) == 3
            else [None, None, None]
        )

    # WARNING: Private function used in threading. May be blocking.
    def _continuousAiming(self):
        while self.continuous_measure:        
            self.aiming_data = self.getAiming()
    
    def startAimingThread(self):
        self.continuous_measure = True
        self.aiming_thread = threading.Thread(target=self._continuousAiming, name="AIMING_THREAD", daemon=True)
        self.aiming_thread.start()

    def stopAimingThread(self):
        self.continuous_measure = False
        self.aiming_thread.join()
        self.serial.close()
    