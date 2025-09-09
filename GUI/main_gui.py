# main_app.py

from PyQt6.QtCore import QTimer, qInstallMessageHandler, QtMsgType
from PyQt6.QtWidgets import (
    QMainWindow,  QTabWidget, QApplication,
    QWidget, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QMessageBox, QGridLayout,
    QLineEdit, QHBoxLayout
)

import serial.tools.list_ports
import pyqtgraph as pg
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Modules'))
from aiming import RAiming


def qt_message_handler(mode, context, message):
    """Filtrar mensajes de Qt para suprimir advertencias innecesarias"""
    # Suprimir mensajes específicos de setGeometry de Windows
    if "QWindowsWindow::setGeometry" in message:
        return
    if "Unable to set geometry" in message:
        return
    if "MINMAXINFO" in message:
        return
    
    # Permitir otros mensajes importantes
    if mode == QtMsgType.QtCriticalMsg or mode == QtMsgType.QtFatalMsg:
        print(f"Qt {mode}: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        # Solo mostrar advertencias que no sean de geometría
        if not any(keyword in message for keyword in ["setGeometry", "geometry", "MINMAXINFO"]):
            print(f"Qt Warning: {message}")


class SerialPortSelectorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # Title
        title = QLabel("Selector de Puertos COM")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout().addWidget(title)

        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto COM:"))
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)

        port_widget = QWidget()
        port_widget.setLayout(port_layout)
        self.layout().addWidget(port_widget)

        # Baudrate selection
        baudrate_layout = QHBoxLayout()
        baudrate_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_input = QLineEdit("19200")  # Default baudrate
        self.baudrate_input.setPlaceholderText("Ex: 9600, 19200, 115200")
        baudrate_layout.addWidget(self.baudrate_input)

        baudrate_widget = QWidget()
        baudrate_widget.setLayout(baudrate_layout)
        self.layout().addWidget(baudrate_widget)

        # Status
        self.status_label = QLabel("Estado: No conectado")
        self.layout().addWidget(self.status_label)

        # Initialize
        self.selected_port = None
        self.refresh_ports()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

        if ports:
            self.status_label.setText(f"Encontrados {len(ports)} puertos")
        else:
            self.status_label.setText("No se encontraron puertos COM")

    def get_selected_port(self):
        """Retorna información del puerto seleccionado"""
        if self.port_combo.currentText():
            device = self.port_combo.currentText().split(' - ')[0]
            try:
                baudrate = int(self.baudrate_input.text())
            except ValueError:
                baudrate = 9600  # Default fallback

            return {
                'device': device,
                'baudrate': baudrate
            }
        return None


class bearingCompassWidget(QWidget):
    def __init__(self, title="Bearing"):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.label = QLabel(title)
        self.layout().addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setXRange(-110, 110)
        self.plot.setYRange(-110, 110)
        self.layout().addWidget(self.plot)

        # Dibujar círculo de referencia
        from PyQt6.QtWidgets import QGraphicsEllipseItem
        circle_item = QGraphicsEllipseItem(-100, -100, 200, 200)
        circle_item.setPen(pg.mkPen('#eff5fa', width=2))
        self.plot.addItem(circle_item)

        # Marcadores cardinales (color claro para alta visibilidad)
        self.text_items = {}
        for angle, label in zip([90, 0, 270, 180], ['N', 'E', 'S', 'W']):
            x = 90 * np.cos(np.radians(angle))
            y = 90 * np.sin(np.radians(angle))
            text = pg.TextItem(label, anchor=(0.5, 0.5), color='#eff5fa')
            text.setPos(x, y)
            self.plot.addItem(text)
            self.text_items[label] = text

        # Aguja de dirección tipo brújula (azul medio brillante para máxima visibilidad)
        self.arrow = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=2), 
                                   brush=pg.mkBrush('#5374ac'))
        self.plot.addItem(self.arrow)

        # Cruz central que rota con la aguja (10 unidades de ancho)
        self.center_cross_h = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=2))
        self.center_cross_v = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=2))
        self.plot.addItem(self.center_cross_h)
        self.plot.addItem(self.center_cross_v)

        # Texto del ángulo - posicionado en la parte superior (azul claro para contraste)
        self.angle_text = pg.TextItem("Bearing: 0.0°", anchor=(0.5, 0.5), color='#8bafd0')
        self.angle_text.setPos(0, 110)
        self.plot.addItem(self.angle_text)

    def update_bearing(self, angle_deg: float):
        # Convertir ángulo para que 0° sea Norte (ajuste de coordenadas)
        angle_rad = np.radians(90 - angle_deg)
        
        # Crear forma de rombo/triangular para la aguja de la brújula
        # Punto de la punta (hacia la dirección)
        tip_length = 70
        tip_x = tip_length * np.cos(angle_rad)
        tip_y = tip_length * np.sin(angle_rad)
        
        # Puntos laterales del rombo (perpendiculares a la dirección)
        side_length = 15
        side_angle_1 = angle_rad + np.pi/2
        side_angle_2 = angle_rad - np.pi/2
        
        side1_x = side_length * np.cos(side_angle_1)
        side1_y = side_length * np.sin(side_angle_1)
        side2_x = side_length * np.cos(side_angle_2)
        side2_y = side_length * np.sin(side_angle_2)
        
        # Punto trasero (cola del rombo)
        tail_length = 20
        tail_x = -tail_length * np.cos(angle_rad)
        tail_y = -tail_length * np.sin(angle_rad)
        
        # Crear el polígono del rombo: punta -> lado1 -> cola -> lado2 -> punta
        x_points = [tip_x, side1_x, tail_x, side2_x, tip_x]
        y_points = [tip_y, side1_y, tail_y, side2_y, tip_y]
        
        self.arrow.setData(x_points, y_points)
        
        # Actualizar cruz central que rota con la aguja (10 unidades de ancho)
        cross_half_width = 5  # 10 unidades total / 2
        
        # Línea horizontal de la cruz (rotada)
        cross_h_x1 = -cross_half_width * np.cos(angle_rad + np.pi/2)
        cross_h_y1 = -cross_half_width * np.sin(angle_rad + np.pi/2)
        cross_h_x2 = cross_half_width * np.cos(angle_rad + np.pi/2)
        cross_h_y2 = cross_half_width * np.sin(angle_rad + np.pi/2)
        
        # Línea vertical de la cruz (rotada)
        cross_v_x1 = -cross_half_width * np.cos(angle_rad)
        cross_v_y1 = -cross_half_width * np.sin(angle_rad)
        cross_v_x2 = cross_half_width * np.cos(angle_rad)
        cross_v_y2 = cross_half_width * np.sin(angle_rad)
        
        self.center_cross_h.setData([cross_h_x1, cross_h_x2], [cross_h_y1, cross_h_y2])
        self.center_cross_v.setData([cross_v_x1, cross_v_x2], [cross_v_y1, cross_v_y2])
        
        self.angle_text.setText(f"Bearing: {angle_deg:.1f}°")


class AttitudeIndicatorWidget(QWidget):
    def __init__(self, title="Attitude Indicator"):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.label = QLabel(title)
        self.layout().addWidget(self.label)

        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.setXRange(-100, 100)
        self.plot.setYRange(-100, 100)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.layout().addWidget(self.plot)

        # Variables para ángulos actuales
        self.current_pitch = 0.0
        self.current_roll = 0.0

        # Crear horizonte artificial (colores optimizados con nueva paleta)
        from PyQt6.QtWidgets import QGraphicsRectItem
        from PyQt6.QtGui import QBrush, QColor
        
        # Rectángulos simples para cielo y tierra
        self.sky_rect = QGraphicsRectItem(-100, -100, 200, 100)
        self.sky_rect.setBrush(QBrush(QColor(20, 28, 51)))  # #141c33
        self.sky_rect.setPen(pg.mkPen(None))
        self.plot.addItem(self.sky_rect)
        
        self.ground_rect = QGraphicsRectItem(-100, 0, 200, 100)
        self.ground_rect.setBrush(QBrush(QColor(47, 69, 111)))  # #2f456f
        self.ground_rect.setPen(pg.mkPen(None))
        self.plot.addItem(self.ground_rect)

        # Línea de horizonte principal (azul claro brillante para alto contraste)
        self.horizon_line = pg.PlotDataItem(pen=pg.mkPen('#8bafd0', width=4))
        self.plot.addItem(self.horizon_line)

        # Líneas de pitch cada 10 grados (color claro para máximo contraste)
        self.pitch_lines = []
        self.pitch_texts = []
        for angle in range(-30, 35, 10):
            if angle == 0:
                continue  # Ya tenemos la línea principal de horizonte
                
            # Líneas más largas para ángulos principales
            if abs(angle) % 20 == 0:
                line_width = 50
                pen_width = 2
            else:
                line_width = 30
                pen_width = 1
            
            line = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=pen_width))
            self.plot.addItem(line)
            self.pitch_lines.append((line, angle, line_width))
            
            # Etiquetas de ángulo (azul claro brillante para alta visibilidad)
            if angle != 0:
                text_left = pg.TextItem(f"{angle}°", anchor=(1, 0.5), color='#8bafd0')
                text_right = pg.TextItem(f"{angle}°", anchor=(0, 0.5), color='#8bafd0')
                self.plot.addItem(text_left)
                self.plot.addItem(text_right)
                self.pitch_texts.append((text_left, text_right, angle))

        # Símbolo del avión (azul medio brillante para máxima visibilidad)
        self.aircraft_wings = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=4))
        self.aircraft_center = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=3))
        self.plot.addItem(self.aircraft_wings)
        self.plot.addItem(self.aircraft_center)
        
        # Dibujar símbolo del avión
        self.aircraft_wings.setData([-40, -15, -15, 15, 15, 40], [0, 0, -3, -3, 0, 0])
        self.aircraft_center.setData([0, 0], [-8, 8])

        # Indicador de roll (arco superior) - color claro para máximo contraste
        self.roll_scale = []
        for angle in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            angle_rad = np.radians(angle)
            x = 85 * np.sin(angle_rad)
            y = 85 * np.cos(angle_rad)
            
            # Marcas más largas para ángulos principales
            if angle % 30 == 0:
                mark_length = 10
                pen_width = 2
            else:
                mark_length = 5
                pen_width = 1
                
            # Línea de marca
            x2 = (85 - mark_length) * np.sin(angle_rad)
            y2 = (85 - mark_length) * np.cos(angle_rad)
            
            mark = pg.PlotDataItem(pen=pg.mkPen('#eff5fa', width=pen_width))
            mark.setData([x2, x], [y2, y])
            self.plot.addItem(mark)
            
            # Etiquetas para ángulos principales (azul claro brillante)
            if angle % 30 == 0 and angle != 0:
                text = pg.TextItem(f"{abs(angle)}°", anchor=(0.5, 0.5), color='#8bafd0')
                text_x = (85 + 15) * np.sin(angle_rad)
                text_y = (85 + 15) * np.cos(angle_rad)
                text.setPos(text_x, text_y)
                self.plot.addItem(text)

        # Triángulo indicador de roll (azul medio brillante)
        self.roll_triangle = pg.PlotDataItem(pen=pg.mkPen('#5374ac', width=2), 
                                           brush=pg.mkBrush('#5374ac'))
        self.plot.addItem(self.roll_triangle)

        # Textos para mostrar valores numéricos (azul claro para alto contraste)
        self.pitch_text = pg.TextItem("Pitch: 0.0°", anchor=(0, 1), color='#8bafd0')
        self.pitch_text.setPos(-95, 95)
        self.plot.addItem(self.pitch_text)
        
        self.roll_text = pg.TextItem("Roll: 0.0°", anchor=(1, 1), color='#8bafd0')
        self.roll_text.setPos(95, 95)
        self.plot.addItem(self.roll_text)

        # Inicializar posiciones
        self.update_attitude(0, 0)

    def update_attitude(self, pitch_deg: float, roll_deg: float):
        self.current_pitch = pitch_deg
        self.current_roll = roll_deg
        
        # Convertir roll a radianes
        roll_rad = np.radians(roll_deg)
        
        # Actualizar horizonte principal
        horizon_y = -pitch_deg * 2  # Escalar pitch
        horizon_points = self._rotate_line(-100, 100, horizon_y, horizon_y, roll_rad)
        self.horizon_line.setData(horizon_points[0], horizon_points[1])
        
        # Actualizar líneas de pitch
        for line, angle, width in self.pitch_lines:
            line_y = (angle - pitch_deg) * 2
            points = self._rotate_line(-width/2, width/2, line_y, line_y, roll_rad)
            line.setData(points[0], points[1])
        
        # Actualizar textos de pitch
        for text_left, text_right, angle in self.pitch_texts:
            text_y = (angle - pitch_deg) * 2
            # Calcular posiciones rotadas para los textos
            left_pos = self._rotate_point(-40, text_y, roll_rad)
            right_pos = self._rotate_point(40, text_y, roll_rad)
            text_left.setPos(left_pos[0], left_pos[1])
            text_right.setPos(right_pos[0], right_pos[1])
        
        # Actualizar triángulo indicador de roll
        triangle_angle = np.radians(-roll_deg)  # Negativo para que gire en la dirección correcta
        triangle_x = 75 * np.sin(triangle_angle)
        triangle_y = 75 * np.cos(triangle_angle)
        
        # Crear triángulo apuntando hacia el centro
        tri_size = 5
        triangle_points = [
            [triangle_x, triangle_x - tri_size * np.cos(triangle_angle + np.pi/2), 
             triangle_x - tri_size * np.cos(triangle_angle - np.pi/2)],
            [triangle_y, triangle_y - tri_size * np.sin(triangle_angle + np.pi/2), 
             triangle_y - tri_size * np.sin(triangle_angle - np.pi/2)]
        ]
        self.roll_triangle.setData(triangle_points[0], triangle_points[1])
        
        # Actualizar textos numéricos
        self.pitch_text.setText(f"Pitch: {pitch_deg:.1f}°")
        self.roll_text.setText(f"Roll: {roll_deg:.1f}°")

    def _rotate_point(self, x, y, angle):
        """Rotar un punto alrededor del origen"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
    
    def _rotate_line(self, x1, x2, y1, y2, angle):
        """Rotar una línea alrededor del origen"""
        point1 = self._rotate_point(x1, y1, angle)
        point2 = self._rotate_point(x2, y2, angle)
        return ([point1[0], point2[0]], [point1[1], point2[1]])

    def update_pitch(self, pitch_deg: float):
        self.update_attitude(pitch_deg, self.current_roll)
    
    def update_roll(self, roll_deg: float):
        self.update_attitude(self.current_pitch, roll_deg)


class RealTimePlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QGridLayout())

        # Título
        self.layout().addWidget(QLabel("Visualización en Tiempo Real"))

        # Control buttons
        self.controls_layout = QHBoxLayout()
        self.connect_button = QPushButton("Conectar Sensor")
        self.connect_button.clicked.connect(self.connect_aiming_sensor)
        self.disconnect_button = QPushButton("Desconectar")
        self.disconnect_button.clicked.connect(self.disconnect_aiming_sensor)
        self.disconnect_button.setEnabled(False)

        self.controls_layout.addWidget(self.connect_button)
        self.controls_layout.addWidget(self.disconnect_button)

        controls_widget = QWidget()
        controls_widget.setLayout(self.controls_layout)
        self.layout().addWidget(controls_widget, 0, 0, 1, 3)

        # Status label
        self.connection_status = QLabel("Estado: Desconectado")
        self.layout().addWidget(self.connection_status, 1, 0, 1, 3)

        # Gráfica 1D: Potencia vs Distancia
        self.plot1d = pg.PlotWidget(title="Potencia vs Distancia")
        self.plot1d.setLabel('left', 'Potencia', units='dBm')
        self.plot1d.setLabel('bottom', 'Distancia', units='m')
        self.curve1d = self.plot1d.plot(pen='#8bafd0')
        self.layout().addWidget(self.plot1d, 2, 0, 1, 2)

        # Gráfica 2D: Posición actual vs referencia
        self.plot2d = pg.PlotWidget(title="Posición en el Plano XY")
        self.plot2d.setLabel('left', 'Y', units='m')
        self.plot2d.setLabel('bottom', 'X', units='m')
        self.plot2d.setAspectLocked(True)
        self.ref_point = self.plot2d.plot(
            [0], [0], pen=None, symbol='x', symbolBrush='#5374ac', symbolSize=12)
        self.trace_curve = self.plot2d.plot(pen=pg.mkPen('#8bafd0', width=2))
        self.current_point = self.plot2d.plot(
            [0], [0], pen=None, symbol='o', symbolBrush='#2f456f', symbolSize=10)
        self.layout().addWidget(self.plot2d, 2, 2)

        # Brújula bearing
        self.bearing_widget = bearingCompassWidget("Bearing")
        self.layout().addWidget(self.bearing_widget, 4, 0)

        # Indicador de Actitud (Pitch + Roll combinados)
        self.attitude_widget = AttitudeIndicatorWidget("Attitude Indicator")
        self.layout().addWidget(QLabel("Aiming System"), 3, 0, 1, 3)
        self.layout().addWidget(self.attitude_widget, 4, 1, 1, 2)  # Ocupa 2 columnas

        # Buffers
        self.distance_data = []
        self.power_data = []
        self.x_trace = []
        self.y_trace = []

        # Variables para sensor real
        self.aiming_sensor = None
        self.data_timer = None
        self.parent_app = None

    def set_parent_app(self, parent_app):
        self.parent_app = parent_app

    def connect_aiming_sensor(self):
        if self.parent_app and self.parent_app.port_selector_widget.get_selected_port():
            try:
                port_info = self.parent_app.port_selector_widget.get_selected_port()
                self.aiming_sensor = RAiming(
                    serial_port=port_info['device'],
                    baudrate=port_info['baudrate']
                )

                # Start data timer
                self.data_timer = QTimer()
                self.data_timer.timeout.connect(self.update_real_data)
                self.data_timer.start(100)  # Update every 100ms

                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.connection_status.setText(
                    f"Estado: Conectado a {port_info['device']}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Error de Conexión", f"No se pudo conectar al sensor:\n{str(e)}")
        else:
            QMessageBox.warning(
                self, "Error", "Primero seleccione un puerto COM en la pestaña 'Puertos COM'")

    def disconnect_aiming_sensor(self):
        if self.data_timer:
            self.data_timer.stop()
            self.data_timer = None

        if self.aiming_sensor:
            try:
                self.aiming_sensor.serial.close()
            except:
                pass
            self.aiming_sensor = None

        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.connection_status.setText("Estado: Desconectado")

    def update_real_data(self):
        if self.aiming_sensor:
            try:
                # Get real aiming data: [bearing, pitch_yz, roll_xz, cal_stat_aim, temp]
                # {bearing},{pitch},{roll}
                aiming_data = self.aiming_sensor.getAiming()

                if aiming_data and len(aiming_data) >= 3:
                    bearing = aiming_data[0]    # bearing/yaw
                    pitch = aiming_data[1]      # Pitch (pitch_yz)
                    roll = aiming_data[2]       # Roll (roll_xz)

                    # Update orientation displays with real data
                    self.update_bearing(bearing)
                    self.update_pitch(pitch)
                    self.update_roll(roll)

                    # Simulate power and position until you connect real USRP/GPS
                    self.simulate_power_position()

            except Exception as e:
                print(f"Error reading sensor data: {e}")

    def simulate_power_position(self):
        """Keep simulating power and position until you connect real USRP and GPS"""
        import time
        current_time = time.time()

        # Simulate power vs distance
        distance = (current_time % 60) * 0.5  # Reset every minute
        power = -30 + 5 * np.sin(distance / 5)
        self.update_1d(distance, power)

        # Simulate position XY
        x = np.cos(current_time / 10) * 5
        y = np.sin(current_time / 10) * 5
        self.update_2d(x, y, x_ref=0, y_ref=0)

    def update_1d(self, distance: float, power: float):
        self.distance_data.append(distance)
        self.power_data.append(power)
        # Keep only last 1000 points
        if len(self.distance_data) > 1000:
            self.distance_data = self.distance_data[-1000:]
            self.power_data = self.power_data[-1000:]
        self.curve1d.setData(self.distance_data, self.power_data)

    def update_2d(self, x: float, y: float, x_ref: float = 0.0, y_ref: float = 0.0):
        self.x_trace.append(x)
        self.y_trace.append(y)
        # Keep only last 1000 points
        if len(self.x_trace) > 1000:
            self.x_trace = self.x_trace[-1000:]
            self.y_trace = self.y_trace[-1000:]
        self.trace_curve.setData(self.x_trace, self.y_trace)
        self.current_point.setData([x], [y])
        self.ref_point.setData([x_ref], [y_ref])

    def update_bearing(self, angle_deg: float):
        self.bearing_widget.update_bearing(angle_deg)

    def update_pitch(self, angle_deg: float):
        self.attitude_widget.update_pitch(angle_deg)

    def update_roll(self, angle_deg: float):
        self.attitude_widget.update_roll(angle_deg)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Mediciones 5G - Análisis Integrado")
        
        # Configurar ventana con tamaño inicial normal
        # self.setGeometry(100, 100, 1400, 900)
        self.setGeometry(50, 50, 700, 500)

        # Widget central con pestañas
        self.central_widget = QTabWidget()
        self.central_widget.currentChanged.connect(self.on_tab_changed)  # Conectar evento de cambio de pestaña
        self.setCentralWidget(self.central_widget)

        # Pestaña 1: Selector de puertos COM
        self.port_selector_widget = SerialPortSelectorGUI()
        self.central_widget.addTab(self.port_selector_widget, "Puertos COM")

        # Pestaña 2: Visualización en Tiempo Real
        self.realtime_widget = RealTimePlotWidget()
        self.realtime_widget.set_parent_app(self)  # Set parent reference
        self.central_widget.addTab(self.realtime_widget, "Tiempo Real")

    def on_tab_changed(self, index):
        """Manejar el cambio de pestañas para ajustar el tamaño de la ventana"""
        if index == 0:  # Pestaña "Puertos COM"
            if self.isMaximized():  # Solo cambiar si está maximizada
                self.showNormal()  # Volver al tamaño normal
                # Usar QTimer para dar tiempo a que la ventana se normalice antes de cambiar geometría
                QTimer.singleShot(
                    50, lambda: self.setGeometry(50, 50, 700, 500))
        elif index == 1:  # Pestaña "Tiempo Real"
            if not self.isMaximized():  # Solo maximizar si no está ya maximizada
                self.showMaximized()  # Maximizar ventana


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instalar el filtro de mensajes de Qt para suprimir advertencias innecesarias
    qInstallMessageHandler(qt_message_handler)
    
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())
