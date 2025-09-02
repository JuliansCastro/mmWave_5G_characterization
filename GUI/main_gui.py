# main_app.py

import sys
import PyQt6
import numpy as np
import pyqtgraph as pg
import serial.tools.list_ports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,  QTabWidget, QApplication, 
    QWidget, QVBoxLayout, QPushButton, 
    QComboBox, QLabel, QMessageBox, QGridLayout
)

# gui_selector.py
# serial_scanner.py
# from serial_scanner import SerialPortScanner
# from real_time_plot import RealTimePlotWidget
#from gui_selector import SerialPortSelectorGUI
# real_time_plot.py

class SerialPortScanner:
    def __init__(self):
        self.available_ports = []

    def scan_ports(self):
        self.available_ports = []
        for port in serial.tools.list_ports.comports():
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'manufacturer': port.manufacturer,
                'location': port.location
            }
            self.available_ports.append(port_info)

    def filter_by_vid_pid(self, target_vid: int, target_pid: int):
        return [p for p in self.available_ports if p['vid'] == target_vid and p['pid'] == target_pid]

    def get_ports(self):
        return self.available_ports
    


class SerialPortSelectorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selector de Puerto COM")
        self.setMinimumWidth(400)
        self.scanner = SerialPortScanner()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Seleccione un puerto COM:")
        self.layout.addWidget(self.label)

        self.combo_box = QComboBox()
        self.layout.addWidget(self.combo_box)

        self.refresh_button = QPushButton("Actualizar lista")
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.layout.addWidget(self.refresh_button)

        self.select_button = QPushButton("Seleccionar puerto")
        self.select_button.clicked.connect(self.select_port)
        self.layout.addWidget(self.select_button)

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.refresh_ports()

    def refresh_ports(self):
        self.combo_box.clear()
        self.scanner.scan_ports()
        ports = self.scanner.get_ports()
        for p in ports:
            # print(p)
            label = f"{p['device']} - {p['description']} (VID:{p['vid']} PID:{p['pid']})"
            self.combo_box.addItem(label, p)

    def select_port(self):
        index = self.combo_box.currentIndex()
        if index >= 0:
            port_info = self.combo_box.itemData(index)
            msg = f"Puerto seleccionado:\n{port_info['device']}\nVID: {port_info['vid']}\nPID: {port_info['pid']}"
            QMessageBox.information(self, "Puerto COM", msg)
            self.status_label.setText(f"Puerto activo: {port_info['device']}")
        else:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún puerto.")

class YawCompassWidget(QWidget):
    def __init__(self, title="Yaw"):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.label = QLabel(title)
        self.layout().addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.layout().addWidget(self.plot)

        # Dibujar círculo de referencia
        circle = PyQt6.QtWidgets.QGraphicsEllipseItem(-100, -100, 200, 200)
        circle.setPen(pg.mkPen('w', width=2))
        self.plot.addItem(circle)

        # Marcadores cardinales
        self.text_items = {}
        for angle, label in zip([0, 90, 180, 270], ['N', 'E', 'S', 'W']):
            x = 90 * np.cos(np.radians(angle))
            y = 90 * np.sin(np.radians(angle))
            text = pg.TextItem(label, anchor=(0.5, 0.5), color='w')
            text.setPos(x, y)
            self.plot.addItem(text)
            self.text_items[label] = text

        # Aguja de dirección
        self.arrow = pg.PlotDataItem(pen=pg.mkPen('r', width=3))
        self.plot.addItem(self.arrow)

    def update_yaw(self, angle_deg: float):
        # Normalizar ángulo
        angle_rad = np.radians(angle_deg)
        x = [0, 80 * np.cos(angle_rad)]
        y = [0, 80 * np.sin(angle_rad)]
        self.arrow.setData(x, y)


class InclinometerWidget(QWidget):
    def __init__(self, title="Inclinómetro"):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.label = QLabel(title)
        self.layout().addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.setRange(xRange=[-100, 100], yRange=[-100, 100])
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.layout().addWidget(self.plot)

        # Barra inclinada
        self.bar = pg.PlotDataItem(pen=pg.mkPen('orange', width=6))
        self.plot.addItem(self.bar)

        # Texto del ángulo
        self.angle_text = pg.TextItem("", anchor=(0.5, 0.5), color='w')
        self.angle_text.setPos(0, 70)
        self.plot.addItem(self.angle_text)

    def update_angle(self, angle_deg: float):
        # Calcular inclinación de la barra
        angle_rad = np.radians(angle_deg)
        x = [-80 * np.cos(angle_rad), 80 * np.cos(angle_rad)]
        y = [-80 * np.sin(angle_rad), 80 * np.sin(angle_rad)]
        self.bar.setData(x, y)
        self.angle_text.setText(f"{angle_deg:.1f}°")


class RealTimePlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QGridLayout())

        # Título
        self.layout().addWidget(QLabel("Visualización en Tiempo Real"))

        # Gráfica 1D: Potencia vs Distancia
        self.plot1d = pg.PlotWidget(title="Potencia vs Distancia")
        self.plot1d.setLabel('left', 'Potencia', units='dBm')
        self.plot1d.setLabel('bottom', 'Distancia', units='m')
        self.curve1d = self.plot1d.plot(pen='y')
        self.layout().addWidget(self.plot1d, 0, 0, 1, 2)

        # Gráfica 2D: Posición actual vs referencia
        self.plot2d = pg.PlotWidget(title="Posición en el Plano XY")
        self.plot2d.setLabel('left', 'Y', units='m')
        self.plot2d.setLabel('bottom', 'X', units='m')
        self.plot2d.setAspectLocked(True)
        self.ref_point = self.plot2d.plot([0], [0], pen=None, symbol='x', symbolBrush='r', symbolSize=12)
        self.trace_curve = self.plot2d.plot(pen=pg.mkPen('c', width=2))
        self.current_point = self.plot2d.plot([0], [0], pen=None, symbol='o', symbolBrush='g', symbolSize=10)
        self.layout().addWidget(self.plot2d, 0, 2)

        # Brújula Yaw
        self.yaw_widget = YawCompassWidget()
        #self.layout().addWidget(QLabel("Orientación Yaw"), 2, 0)
        self.layout().addWidget(self.yaw_widget, 2, 0)

        # Inclinómetros
        self.pitch_widget = InclinometerWidget("Pitch")
        self.roll_widget = InclinometerWidget("Roll")
        self.layout().addWidget(QLabel("Inclinómetros"), 1, 0, 1, 3)
        self.layout().addWidget(self.pitch_widget, 2, 1)
        self.layout().addWidget(self.roll_widget, 2, 2)

        # Buffers
        self.distance_data = []
        self.power_data = []
        self.x_trace = []
        self.y_trace = []

    def update_1d(self, distance: float, power: float):
        self.distance_data.append(distance)
        self.power_data.append(power)
        self.curve1d.setData(self.distance_data, self.power_data)

    def update_2d(self, x: float, y: float, x_ref: float = 0.0, y_ref: float = 0.0):
        self.x_trace.append(x)
        self.y_trace.append(y)
        self.trace_curve.setData(self.x_trace, self.y_trace)
        self.current_point.setData([x], [y])
        self.ref_point.setData([x_ref], [y_ref])

    def update_yaw(self, angle_deg: float):
        self.yaw_widget.update_yaw(angle_deg)

    def update_pitch(self, angle_deg: float):
        self.pitch_widget.update_angle(angle_deg)

    def update_roll(self, angle_deg: float):
        self.roll_widget.update_angle(angle_deg)

# class MainApp(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Sistema de Adquisición y Control")
#         self.setMinimumSize(800, 600)

#         # Crear widget principal con pestañas
#         self.tabs = QTabWidget()
#         self.setCentralWidget(self.tabs)

#         # Tab de selección de puerto
#         self.port_selector_tab = QWidget()
#         self.port_selector_layout = QVBoxLayout()
#         self.port_selector_tab.setLayout(self.port_selector_layout)

#         # Insertar el selector de puerto como widget
#         self.port_selector_widget = SerialPortSelectorGUI()
#         self.port_selector_layout.addWidget(self.port_selector_widget)

#         # Agregar pestaña
#         self.tabs.addTab(self.port_selector_tab, "Puertos COM")

#         # Puedes agregar más tabs aquí (visualización, adquisición, configuración...)



class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Adquisición y Control")
        self.setMinimumSize(800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Selector de puerto
        self.port_selector_tab = QWidget()
        self.port_selector_layout = QVBoxLayout()
        self.port_selector_tab.setLayout(self.port_selector_layout)
        self.port_selector_widget = SerialPortSelectorGUI()
        self.port_selector_layout.addWidget(self.port_selector_widget)
        self.tabs.addTab(self.port_selector_tab, "Puertos COM")

        # Tab 2: Visualización en tiempo real
        self.plot_tab = RealTimePlotWidget()
        self.tabs.addTab(self.plot_tab, "Visualización")

        # Simulación de datos (puedes reemplazar esto con datos reales)
        self.simulate_data()

    def simulate_data(self):
        from PyQt6.QtCore import QTimer
        import random
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_fake_data)
        self.timer.start(50)  # cada 50 ms

        self.distance = 0

    def generate_fake_data(self):
        # Simulación de potencia vs distancia
        self.distance += 0.5
        power = -30 + 5 * np.sin(self.distance / 5)
        self.plot_tab.update_1d(self.distance, power)

        # Simulación de posición XY
        x = np.cos(self.distance / 10) * 5
        y = np.sin(self.distance / 10) * 5
        self.plot_tab.update_2d(x, y, x_ref=0, y_ref=0)

        # Simulación de Yaw
        yaw_angle = (self.distance * 10) % 360
        self.plot_tab.update_yaw(yaw_angle)

        # Simulación de Pitch y Roll
        pitch = 10 * np.sin(self.distance / 5)
        roll = 15 * np.cos(self.distance / 7)
        self.plot_tab.update_pitch(pitch)
        self.plot_tab.update_roll(roll)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = SerialPortSelectorGUI()
#     window.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     scanner = SerialPortScanner()
#     scanner.scan_ports()
#     print(scanner.get_ports())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())