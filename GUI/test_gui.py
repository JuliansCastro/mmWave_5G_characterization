# import pyqtgraph as pg
# import PyQt6

# win = pg.GraphicsLayoutWidget(show=True, title="Plotting")
# p = win.addPlot(title='')

# p_ellipse = PyQt6.QtWidgets.QGraphicsEllipseItem(0, 0, 10, 20)  # x, y, width, height
# p_ellipse.setPen(pg.mkPen((0, 0, 0, 100)))
# p_ellipse.setBrush(pg.mkBrush((50, 50, 200)))

# p.addItem(p_ellipse)

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout

app = QApplication([])

window = QWidget()
layout = QGridLayout()

# Agregar botones en posiciones específicas
layout.addWidget(QPushButton("Arriba izquierda"), 0, 0)
layout.addWidget(QPushButton("Arriba derecha"), 0, 1)
layout.addWidget(QPushButton("Centro"), 1, 0, 1, 2)  # Ocupa 2 columnas
layout.addWidget(QPushButton("Abajo izquierda"), 2, 0)
layout.addWidget(QPushButton("Abajo derecha"), 2, 1)

window.setLayout(layout)
window.show()
app.exec()