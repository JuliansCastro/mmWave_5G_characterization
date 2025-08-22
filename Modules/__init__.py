"""
5G Characterization Modules Package

Custom modules for 5G mmWave characterization project.
"""

# Import specific modules
from . import gps
from . import usrp
from . import aiming
from . import filewriter

# Import all main classes/functions from each module
from .gps import GPS
from .usrp import USRP
from .datums import DATUMS
from .aiming import RAiming
from .filewriter import FileCSV
from .instrument import Instrument

# Define what gets imported with "from Modules import *"
__all__ = [
    'GPS',
    'USRP',
    'RAiming',
    'FileCSV',
    'DATUMS',
    'Instrument'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Julián Andrés Castro Pardo, Diana Sofía López, Carlos Julián Furnieles Chipagra'
