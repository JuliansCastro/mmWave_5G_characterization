import threading
from serial import Serial

class RAiming:

    def __init__(self, baudrate = 19200, serial_port = "COM3"):
        self.baudrate = baudrate
        self.serial_port = serial_port
        self.continuous_measure = False
        self.aiming_thread = None
        self.aiming_data = []
        self.serial = Serial(port = self.serial_port, baudrate = self.baudrate)


    def getAiming(self):
        accel_mag_values = []
        #if self.serial.in_waiting > 0:
        self.serial.reset_input_buffer()
        # Read a line from the serial port
        str_line = self.serial.readline().decode('utf-8').strip().split(',')

        # Verify that the line has three values
        if len(str_line) == 3:
            # Casting each value individually
            accel_mag_values = [float(value) for value in str_line]

        else:
            #print(f"Línea con formato incorrecto: {line}")
            accel_mag_values =[None, None, None]

        
        return accel_mag_values

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
    