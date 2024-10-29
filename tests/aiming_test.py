'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  {File Description}
'''
import sys
# Route needed by python interpreter to read project's custom classes
sys.path.append('../5G_CHARACTERIZATION/Modules')

import pytest
from aiming import RAiming
from unittest.mock import MagicMock, patch
from serial import SerialException

@pytest.fixture
def mock_serial():
    with patch('aiming.Serial') as MockSerial:
        yield MockSerial

@pytest.mark.parametrize("baudrate, serial_port, expected_baudrate, expected_port", [
    (19200, "COM3", 19200, "COM3"),  # default values
    (9600, "COM4", 9600, "COM4"),    # custom values
], ids=["default_values", "custom_values"])
def test_init(mock_serial, baudrate, serial_port, expected_baudrate, expected_port):
    # Act
    r_aiming = RAiming(baudrate=baudrate, serial_port=serial_port)

    # Assert
    assert r_aiming.baudrate == expected_baudrate
    assert r_aiming.serial_port == expected_port
    mock_serial.assert_called_with(port=expected_port, baudrate=expected_baudrate)

@pytest.mark.parametrize("serial_data, expected_output", [
    ("1.0,2.0,3.0\n", [1.0, 2.0, 3.0]),  # valid data
    ("1.0,2.0\n", [None, None, None]),   # incomplete data
    ("a,b,c\n", [None, None, None]),     # non-numeric data
], ids=["valid_data", "incomplete_data", "non_numeric_data"])
def test_getAiming(mock_serial, serial_data, expected_output):
    # Arrange
    mock_serial_instance = mock_serial.return_value
    mock_serial_instance.readline.return_value = serial_data.encode('utf-8')

    r_aiming = RAiming()

    # Act
    result = r_aiming.getAiming()

    # Assert
    assert result == expected_output

def test_continuousAiming(mock_serial):
    # Arrange
    r_aiming = RAiming()
    r_aiming.getAiming = MagicMock(return_value=[1.0, 2.0, 3.0])
    r_aiming.continuous_measure = True

    # Act
    r_aiming._continuousAiming()

    # Assert
    assert r_aiming.aiming_data == [1.0, 2.0, 3.0]

def test_startAimingThread(mock_serial):
    # Arrange
    r_aiming = RAiming()

    # Act
    r_aiming.startAimingThread()

    # Assert
    assert r_aiming.continuous_measure is True
    assert r_aiming.aiming_thread is not None
    assert r_aiming.aiming_thread.is_alive()

def test_stopAimingThread(mock_serial):
    # Arrange
    r_aiming = RAiming()
    r_aiming.startAimingThread()

    # Act
    r_aiming.stopAimingThread()

    # Assert
    assert r_aiming.continuous_measure is False
    mock_serial.return_value.close.assert_called_once()

@pytest.mark.parametrize("exception", [
    SerialException("Port not found"),
    ValueError("Invalid baudrate"),
], ids=["serial_exception", "value_error"])
def test_serial_exceptions(mock_serial, exception):
    # Arrange
    mock_serial.side_effect = exception

    # Act & Assert
    with pytest.raises(type(exception)):
        RAiming()
