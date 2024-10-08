import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Leer el archivo CSV
file_path = 'Data\Meas_GPS\GPS_MEAS_30-07-2024-16-25-35.csv'  # Reemplaza con la ruta a tu archivo
df = pd.read_csv(file_path)
# Filtrar filas donde latitud, longitud y altitud son todas 0
absPos = df[df['pos_type']=='absPos']
relPos = df[df['pos_type']=='relPos']
# Supongamos que las columnas se llaman 'Latitud', 'Longitud' y 'Altitud'
latitudes = absPos['pos2']
longitudes = absPos['pos1']
altitudes = absPos['pos3']
disN = relPos['pos1']
disE = relPos['pos2']
disD = relPos['pos3']


# # Leer el archivo CSV
# file_path1 = 'Data\Meas_GPS\GPS_MEAS_29-07-2024-17-23-31.csv'  # Reemplaza con la ruta a tu archivo
# df1 = pd.read_csv(file_path1)
# # Filtrar filas donde latitud, longitud y altitud son todas 0
# df1 = df1[~((df1['lat'] == 0) & (df1['lon'] == 0) & (df1['height'] == 0))]
# # Supongamos que las columnas se llaman 'Latitud', 'Longitud' y 'Altitud'
# latitudes1 = df1['lat']
# longitudes1 = df1['lon']
# altitudes1 = df1['height']
# Punto inicial (0, 0, 0)
initial_point = np.array([-74.0827278, 4.6388707, 2589131])

# Calcular las distancias desde el punto inicial
distances = np.sqrt((latitudes - initial_point[0])**2 + 
                    (longitudes - initial_point[1])**2 + 
                    (altitudes - initial_point[2])**2)

# Graficar el recorrido en 3D
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# #ax.plot(latitudes, longitudes, altitudes, label='Recorrido1')
# ax.plot(disN, disE, disD, label='Recorrido2')
# ax.set_xlabel('Latitud')
# ax.set_ylabel('Longitud')
# ax.set_zlabel('Altitud')
# ax.set_title('Recorrido en 3D')
# ax.legend()

# # # Graficar la distancia a lo largo del tiempo (suponiendo que hay una columna 'Tiempo')
# # if 'Tiempo' in df.columns:
# #     tiempos = df['Tiempo']
# #     plt.figure()
# #     plt.plot(tiempos, distances, label='Distancia vs. Tiempo')
# #     plt.xlabel('Tiempo')
# #     plt.ylabel('Distancia')
# #     plt.title('Distancia desde el punto inicial a lo largo del tiempo')
# #     plt.legend()

# plt.show()
# Graficar el recorrido en 2D
plt.figure()
plt.plot(disN, disE,linewidth=3)
plt.xlabel('North Displacement [m]',fontsize=19)
plt.ylabel('East Displacement [m]',fontsize=19)
plt.title('2D Trajectory',fontsize=23)
plt.legend()
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
# Mostrar la gráfica
plt.show()
