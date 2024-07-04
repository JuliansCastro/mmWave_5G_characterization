import serial
import time
import pytictoc
import aiming

#https://gist.github.com/projectweekend/1fae5a8cf2a5b9282f3d

#ser = serial.Serial(port='COM3', baudrate=19200, timeout=0.1)
t = pytictoc.TicToc()
aim = aiming.RAiming(baudrate=19200,serial_port="COM3")

#print("connected to: " + ser.portstr)

#this will store the line
line = []

try:
    while True:
        time.sleep(0.001)
        print(aim.getAiming())
    # while True:
    #     #input('?')
    #     t.tic()
    #     ser.reset_input_buffer()
    #     # using ser.readline() assumes each line contains a single reading
    #     # sent using Serial.println() on the Arduino
    #     reading = ser.readline().decode('utf-8').strip().split(',')
    #     # reading is a string...do whatever you want from here
    #     print(reading)
    #     time.sleep(0.00002)
    #     t.toc()
        
except KeyboardInterrupt:
    print("ctrl + C -> Close serial comm")
    aim.serial.close()
    #ser.close()