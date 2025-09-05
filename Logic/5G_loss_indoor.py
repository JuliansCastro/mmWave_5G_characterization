'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This script is used to measure the 5G signal loss in an indoor environment.
                The script uses a USRP B210 and manual positioning to measure the signal loss.
                The script saves the data in a CSV file.
'''


import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

from usrp import USRP
from time import sleep
from aiming import RAiming
from threading import Event
from pytictoc import TicToc
from pynput import keyboard
from filewriter import FileCSV

def oneShot():

    def keyboard_interrupt(key):
        if key == keyboard.Key.esc:
            print('Stopped...')
            measuring_flag.set()
        elif key == keyboard.Key.enter:
            print('Continuing...')
            measuring_flag.clear()

    # Serial ports
    aim_port = "COM13"

    # Baudrates
    aim_baudrate = 19200

    # USRP parameters
    frequency = 500e6
    gain_rx = 24.7
    
    
    counter = 1

    time_elapsed = 0        # Hold the total measuring elapsed time
    update_time = False     # Allows time_elapsed updating
    
    try:
        chronometer = TicToc()

        file = FileCSV(name="Data/5G_loss/5G_loss", 
                       frequency=None, 
                       header=["PosLabel", "PowerRx","Roll_XZ","Pitch_YZ", "Bearing_MAG"], 
                       type="MEAS")
        file_metadata = FileCSV(name="Data/5G_loss/Metadata/5G_loss", frequency=None, header=["time_elapsed","number_of_readings","reading_rate","time_per_reading","usrp_rx_thread","aiming_thread"], type="METADATA")
        
        usrp_UT = USRP(rx_center_freq=frequency, rx_gain=gain_rx)
        usrp_UT.startRxThread()
        aiming_UT = RAiming(serial_port=aim_port, baudrate=aim_baudrate)
        
        

        # Objects needed for keyboard measurement control
        # 'Esc' -> Stop saving readings
        # 'Enter' -> Continue saving readings
        measuring_flag = Event()
        key_listener = keyboard.Listener(on_press=keyboard_interrupt)   # Use threading
        key_listener.start()

        posLabel = input("Initial Position Label: ")

        sleep(5) # Wait for threads for stabilize

        
        chronometer.tic()
        while True:
            chronometer.tocvalue(restart=True) # Restart chronometer for more precise time measuring
            while not measuring_flag.is_set():
                powerRx = usrp_UT.getPower_dBm(usrp_UT.rx_samples)
                aiming = aiming_UT.getAiming()
                loss_data = [posLabel,powerRx,
                            aiming[0],aiming[1],aiming[2]]
                
                print("\t", counter, loss_data)
                file.saveData(loss_data)
                counter += 1
                update_time = True

            if update_time:
                time_elapsed += chronometer.tocvalue()
                print('Actual elapsed time: ', time_elapsed)
                posLabel = input("Next position label: ")
                update_time = False

    except KeyboardInterrupt:
        chronometer.toc()
        print('\nCtrl + C -> Interrupted!')
        print("\nT1: ", usrp_UT.rx_thread, "\nT2: ", aiming_UT.aiming_thread)

        usrp_UT.stopRxThread()
        aiming_UT.serial.close()
        usrp_UT.stopRxStream()
        
        key_listener.stop()


    finally:
        # time_elapsed = chronometer.tocvalue()
        reading_rate = counter/time_elapsed# chronometer.tocvalue()

        print("\n\nResults:")
        print("\tTime elapsed: ", time_elapsed)
        print("\tNumber of readings: ", counter)
        print("\tReading rate: ", reading_rate, "M/s.\t", 1000/reading_rate, "ms/M\n.")
        try:
            file_metadata.saveData([time_elapsed, counter, reading_rate, 1000/reading_rate,
                                    usrp_UT.rx_thread, aiming_UT.aiming_thread])
        
        except Exception as e:
            print(e)

        
if __name__ == "__main__":
    oneShot()