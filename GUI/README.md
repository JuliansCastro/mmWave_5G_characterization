# GUI Module - MVC Architecture

This folder contains the graphical user interface implementation for the project using the **MVC (Model-View-Controller)** architectural pattern.

## Project Structure

```
GUI/
├── __init__.py              # MVC package initialization
├── main_gui.py             # Main entry point (MVC)
├── models.py               # Data models and application state
├── views.py                # User interface components
├── controllers.py          # Business logic and event handling
└── README.md              # This file
```

## MVC Architecture

### **Model** (`models.py`)
Manages application state and data:
- `AppState`: Global application state with PyQt6 signals
- `ConnectionConfig`: COM connection configuration
- `SensorData`: Structure for sensor data
- `MeasurementData`: Structure for measurement data with automatic buffering

### **View** (`views.py`) 
Visual components without business logic:
- `SerialPortSelectorView`: COM port selection interface
- `BearingCompassView`: Compass widget for bearing
- `AttitudeIndicatorView`: Attitude indicator (pitch/roll)
- `RealTimePlotView`: Real-time visualization interface
- `MainWindowView`: Main window with tabs

### **Controller** (`controllers.py`)
Business logic and coordination:
- `ConnectionController`: Sensor connection management
- `DataController`: Real-time data acquisition
- `SerialPortController`: Port selection control
- `RealTimePlotController`: Real-time plot control
- `MainController`: Main application coordinator

## Usage

### Run the Application
```bash
# Using the configured Python environment
C:/ProgramData/radioconda/python.exe main_gui.py
```

### Use MVC Components in Code
```python
# Import main components
from controllers import MainController

# Create main controller
controller = MainController()

# Get and show main window
main_window = controller.get_main_window()
main_window.show()
```

### Import Individual Components
```python
# Models
from models import AppState, SensorData, MeasurementData

# Views
from views import SerialPortSelectorView, RealTimePlotView

# Controllers
from controllers import MainController, DataController
```

## Benefits of MVC Architecture

### **Separation of Concerns**
- **Model**: Only handles data and state
- **View**: Only handles visual presentation
- **Controller**: Only handles business logic

### **Maintainability**
- Code organized into coherent modules
- Easy to locate and modify functionality
- Lower coupling between components

### **Reusability**
- Reusable view widgets
- Independent data models
- Modular controllers

### **Testing**
- Models testable without PyQt6
- Views testable independently
- Controllers testable separately

## Component Communication

Communication is performed through **PyQt6 signals**:

```python
# The model emits signals when state changes
app_state.sensor_data_updated.emit(sensor_data)

# Views connect to these signals
app_state.sensor_data_updated.connect(view.update_sensor_displays)

# Controllers coordinate communication
controller._connect_signals()
```

## Compatibility

- ✅ **Full compatibility** with existing modules in `/Modules`
- ✅ **No modifications** required in existing code
- ✅ **Identical functionality** to the original implementation
- ✅ **Same user interface** and behavior

## Data Structure

### Data Flow
```
Sensor Hardware → DataController → AppState → View Updates
     ↑                ↓              ↓           ↓
     └── ConnectionController ← User Actions ← Views
```

### Centralized State
All data is stored in `AppState`:
- Connection configuration
- Real-time sensor data
- Measurement data with automatic buffering
- User interface state

## Future Development

This architecture facilitates:
- **Adding new sensors**: Extend `DataController`
- **New visualizations**: Create new classes in `views.py`
- **New functionality**: Add specific controllers
- **Different interfaces**: Reuse models and controllers

## Dependencies

- PyQt6: Graphical interface and signal system
- pyqtgraph: Graphics and visualizations
- serial: COM port communication
- numpy: Mathematical calculations
- Project modules in `/Modules` (unchanged)

