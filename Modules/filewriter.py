'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of the save data in a CSV file. 
'''


from datetime import datetime as dt
import csv
import os

class FileCSV():
    '''
    A class for creating and managing CSV files for data storage.

    This class initializes a CSV file with a specific naming convention
    based on the provided type and frequency. It provides functionality 
    to save data  to the CSV file, ensuring  that the header is written 
    only when the file is created.

    Args:
        name (str): The base name for the CSV file.
        frequency: The frequency value used in the filename for certain types.
        header: The header row to be written to the CSV file.
        type (str): The type of file being created, which determines the filename format.

    Raises:
        ValueError: If an invalid file type is provided.
    '''
    def __init__(self, name:str, frequency, header, type:str) -> None:
        self.DATETIME = dt.now().strftime('%d-%m-%Y-%H-%M-%S')
        match type:
            case "TRX_CAL":
                self.frequency = frequency
                self.filename = (
                    name
                    + str(self.frequency / (1e6))
                    + "MHz_"
                    + self.DATETIME
                    + ".csv"
                )
            case "MEAS":
                self.filename = f"{name}_MEAS_{self.DATETIME}.csv"
            case "METADATA":
                self.filename = f"{name}_METADATA_{self.DATETIME}.csv"
            case _:
                raise ValueError(
                    "Invalid type of file, types available:\n-TRX_CAL\n-BW_MEAS\n-METADATA"
                )

        self.file_exist = False
        self.header = header

    def saveData(self, data) -> None:
        '''
        Saves data to a CSV file, creating the file if it does not exist.

        This function checks if the specified file already exists and opens
        it in append mode if it does, or in write mode if it does not. It writes
        the header row if the file is newly created and appends the provided data as a new row.

        Args:
            data (list): The data to be saved as a new row in the CSV file.

        Returns:
            None
        '''
        self.file_exist = os.path.isfile(self.filename)

        with open(self.filename, mode = "a" if self.file_exist else "w", newline="") as file:
            csv_writer = csv.writer(file)

            if not self.file_exist:
                csv_writer.writerow(self.header)
            csv_writer.writerow(data)


