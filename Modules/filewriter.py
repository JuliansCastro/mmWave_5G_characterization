from datetime import datetime as dt
import csv
import sys, os

class FileCSV():

    def __init__(self, name:str, frequency, header, type:str) -> None:

        match type:
            case "TRX_CAL":
                self.frequency = frequency
                self.filename =  name + str(self.frequency/(1e6)) + "MHz_" + dt.now().strftime('%d-%m-%Y-%H-%M-%S') 
            case "BW_MEAS":
                self.filename = name + "_" + "BW_MEAS_" + dt.now().strftime('%d-%m-%Y-%H-%M-%S')
            case _:
                raise ValueError("Invalid type of file, types available:\n-TRX_CAL\n-BW_MEAS")
                
        
        self.file_exist = False
        self.header = header

    def saveData(self, data) -> None:

        self.file_exist = os.path.isfile(self.filename)

        with open(self.filename, mode = "a" if self.file_exist else "w", newline="") as file:
            csv_writer = csv.writer(file)

            if not self.file_exist:
                csv_writer.writerow(self.header)
            csv_writer.writerow(data)


