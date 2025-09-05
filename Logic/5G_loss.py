'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  Capture power in dBm from USRP, GPS data in absolute ({long},{lat},{height}[deg,mm]) and relative 
                position({PosNorth},{PosEast},{PosDown}[cm]), aiming ({angle_xz},{angle_yz},{heading}[deg]),
                to measure 5G signal loss in a specific area. Capacity to continue measurement.
'''

# Route needed by python interpreter to read project's custom classes
# Add the path to the 'Modules' directory to the PYTHONPATH
import os
import sys
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'Modules')))

from gps import GPS
from usrp import USRP
from time import sleep
from datetime import datetime
from aiming import RAiming
from pytictoc import TicToc
from filewriter import FileCSV

def interrupt(chronometer, usrp_UT, aiming_UT, gps_rtk):
    chronometer.toc()
    print('\nCtrl + C -> Interrupted!')
    print("\nT1: ", usrp_UT.rx_thread, "\nT2: ", aiming_UT.aiming_thread, "\nT3: ", gps_rtk.gps_thread)

    usrp_UT.stopRxThread()
    aiming_UT.serial.close()
    #aiming_UT.stopAimingThread()
    usrp_UT.stopRxStream()
    gps_rtk.stopGPSThread()
    
    
def oneShot():
    # Baudrates
    aim_baudrate = 19200
    gps_baudrate = 19200

    # USRP parameters
    frequency = 500e6
    gain_rx = 24.7


    counter = 1

    try:
        # Serial ports
        aim_port = "COM8"
        gps_port = "COM9"

        chronometer = TicToc()

        file = FileCSV(name="Data/5G_loss/5G_loss",
                       frequency=None, 
                       header=["Timestamp",
                               "R_N/Lon", "R_E/Lat", "R_D/Hgt",
                               "accN/hMSL", "accE/hAcc", "accD/vAcc",
                               "PosType", "PowerRx",
                               "Bearing", "Roll_XZ", "Pitch_YZ", "cal_stat_aim", "Temp"],
                       type="MEAS")
        file_metadata = FileCSV(name="Data/5G_loss/Metadata/5G_loss", frequency=None, header=["time_elapsed","number_of_readings",
                                                                                              "reading_rate","time_per_reading",
                                                                                              "usrp_rx_thread","aiming_thread",
                                                                                              "gps_thread"], type="METADATA")

        usrp_UT = USRP(rx_center_freq=frequency, rx_gain=gain_rx)
        usrp_UT.startRxThread()
        aiming_UT = RAiming(serial_port=aim_port, baudrate=aim_baudrate)
        #aiming_UT.startAimingThread()
        gps_rtk = GPS(port=gps_port, baudrate=gps_baudrate, timeout=0.1, type="all")
        gps_rtk.startGPSThread()

        sleep(5) # Wait for GPS to stabilize in the thread


        chronometer.tic()
        while True:
            powerRx = usrp_UT.getPower_dBm(usrp_UT.rx_samples)
            gps_data = gps_rtk.format_GPSData()
            aiming = aiming_UT.getAiming()
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            loss_data = [date_time, gps_data[0], gps_data[1], gps_data[2], gps_data[3], gps_data[4], gps_data[5], gps_data[6],
                         powerRx,
                         aiming[0], aiming[1], aiming[2], aiming[3], aiming[4]
                         ]

            print("\t", counter, loss_data)
            file.saveData(loss_data)
            counter += 1

    except KeyboardInterrupt:
        interrupt(chronometer, usrp_UT, aiming_UT, gps_rtk)
    finally:
        time_elapsed = chronometer.tocvalue()
        reading_rate = counter/chronometer.tocvalue()

        print("\n\nResults:")
        print("\tTime elapsed: ", time_elapsed)
        print("\tNumber of readings: ", counter)
        print("\tReading rate: ", reading_rate, "M/s.\t", 1000/reading_rate, "ms/M\n.")
        try:
            file_metadata.saveData([time_elapsed, counter, reading_rate, 1000/reading_rate,
                                    usrp_UT.rx_thread, aiming_UT.aiming_thread, gps_rtk.gps_thread])

        except Exception as e:
            print(e)


 
if __name__ == "__main__":
    oneShot()