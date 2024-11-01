# Using Raspberry Pi Pico with sensor LSM303

- Download package [Adafruit](https://circuitpython.org/libraries) CircuitPython
- Install Firmware Circuitpython ([Adafruit](https://circuitpython.org/libraries))

# RPi pico serial comm out

File: *code.py*

```python

import time
from math import atan2, degrees
import board
import digitalio
import adafruit_lsm303_accel
import adafruit_lsm303dlh_mag
import busio

# Initialize Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Initialize I2C
sda_pin = board.GP0
scl_pin = board.GP1
i2c = busio.I2C(scl_pin, sda_pin)

# Initialize the accelerometer
sensor = adafruit_lsm303_accel.LSM303_Accel(i2c)
mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c)

# Initialize UART
tx_pin_uart = board.GP4
rx_pin_uart = board.GP5
uart = busio.UART(tx=tx_pin_uart, rx=rx_pin_uart, baudrate=19200)

def vector_2_degrees(x, y):
    angle = degrees(atan2(y, x))
    if angle < 0:
        angle += 360
    return angle

def get_inclination(_sensor):
    x, y, z = _sensor.acceleration
    return vector_2_degrees(x, z), vector_2_degrees(y, z)

def get_heading(mag):
    magnet_x, magnet_y, _= mag.magnetic
    return vector_2_degrees(magnet_x , magnet_y)


led.value = True # LED on while transmitting
while True:
    # Get inclination angles
    angle_xz, angle_yz = get_inclination(sensor)
    heading = get_heading(mag)

    # Format the message
    # message = "[{}, {}, {}]\r\n".format(angle_xz, angle_yz, heading)
    message = f'{angle_xz},{angle_yz},{heading}'
    print(message)
    # Send the message via UART
    uart.write(message.encode('utf-8'))


```
