# __init__.py - MVC package initialization

"""
5G Measurement System GUI - MVC Architecture

This package implements the graphical user interface for the 5G measurement system 
using the Model-View-Controller (MVC) architectural pattern.

Components:
- models: Data structures and application state management
- views: User interface widgets and visual components  
- controllers: Business logic and event handling

Usage:
    from GUI import MainController
    
    controller = MainController()
    main_window = controller.get_main_window()
    main_window.show()
"""

from .models import AppState, ConnectionConfig, SensorData, MeasurementData
from .views import (
    SerialPortSelectorView, BearingCompassView, AttitudeIndicatorView,
    RealTimePlotView, MainWindowView
)
from .controllers import (
    ConnectionController, DataController, SerialPortController,
    RealTimePlotController, MainController
)

__all__ = [
    # Models
    'AppState', 'ConnectionConfig', 'SensorData', 'MeasurementData',
    
    # Views  
    'SerialPortSelectorView', 'BearingCompassView', 'AttitudeIndicatorView',
    'RealTimePlotView', 'MainWindowView',
    
    # Controllers
    'ConnectionController', 'DataController', 'SerialPortController', 
    'RealTimePlotController', 'MainController'
]

__version__ = "1.0.0"
__author__ = "5G Characterization Team"