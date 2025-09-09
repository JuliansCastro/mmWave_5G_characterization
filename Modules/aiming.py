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
    """
    This class is in charge of the acquisition of aiming data,
    it reads the serial port assigned to the raspberry-Pi Pico
    and parse the data to the required format.
    
    This constructor sets up the baud rate and serial port for communication,
    initializes the necessary attributes for continuous measurement, and establishes
    a connection to the specified serial port.

    Args:
        baudrate (int): The baud rate for the serial communication. Defaults to 19200.
        serial_port (str): The name of the serial port to connect to. Defaults to "COM13".
    
    Methods
    -------
        getAiming() -> list:
            Returns the values of acceleration 'XZ', 'YZ' and magnetometer 'MAG'.
        
        _continuousAiming() -> None:
            Do continuously acquires aiming data while the measurement flag is set to true.
        
        startAimingThread() -> None:
            Starts a separate thread for continuous aiming data acquisition.
        
        stopAimingThread() -> None:
            Stops the continuous aiming data acquisition thread and cleans up resources.
    """ 
       
    def __init__(self, baudrate = 19200, serial_port = "COM13"):
        self.baudrate = baudrate
        self.serial_port = serial_port
        self.continuous_measure = False
        self.aiming_thread = None
        self.aiming_data = []
        self.serial = Serial(port = self.serial_port, baudrate = self.baudrate)


    def getAiming(self):
        """
        Get the values ​​of acceleration 'bearing', 'pitch' and magnetometer 'roll'

        Returns:
            accel_mag_values (list): ['bearing', 'pitch','roll']
        """        
        accel_mag_values = []
        #if self.serial.in_waiting > 0:
        self.serial.reset_input_buffer()
        # Read a line from the serial port
        str_line = self.serial.readline().decode('utf-8').strip().split(',')
        #print(str_line)
        
        # aiming return "{bearing},{pitch},{roll},{cal_stat},{temp}"
        return (
            [float(value) for value in str_line]
            if len(str_line) == 5
            else [None, None, None]
        )

    # WARNING: Private function used in threading. May be blocking.
    def _continuousAiming(self):
        """
        Continuously acquires aiming data while the measurement flag is set to true.
        This method runs in a loop, calling the `getAiming` method to update the aiming data as long as continuous measurement is enabled. It is intended to be used in a separate thread to allow for real-time data acquisition without blocking other operations.

        Raises:
            Exception: May raise exceptions from the `getAiming` method if data acquisition fails.
        """

        while self.continuous_measure:        
            self.aiming_data = self.getAiming()
    
    def startAimingThread(self):
        """
        Starts a separate thread for continuous aiming data acquisition.

        This method enables continuous measurement by setting the appropriate flag
        and initiates a new thread that runs the `_continuousAiming` method.
        The thread is marked as a daemon, allowing it to run in the background 
        and terminate when the main program exits.

        Raises:
            RuntimeError: If the thread cannot be started due to system limitations 
            or other issues.
        """

        self.continuous_measure = True
        self.aiming_thread = threading.Thread(target=self._continuousAiming, name="AIMING_THREAD", daemon=True)
        self.aiming_thread.start()

    def stopAimingThread(self):
        """
        Stops the continuous aiming data acquisition thread and cleans up resources.

        This method disables continuous measurement by setting the appropriate flag
        to false, waits for the aiming thread to finish its execution, and closes 
        the serial connection. It ensures that all resources are properly released 
        before the program continues or terminates.

        Raises:
            RuntimeError: If the thread cannot be joined or if there are issues closing
            the serial connection.
        """

        self.continuous_measure = False
        self.aiming_thread.join()
        self.serial.close()
    