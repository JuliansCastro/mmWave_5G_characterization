import matplotlib.pyplot as plt
import csv

# Step 1: Read the CSV file into columna1 and matrix
file_name = r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\RX_CAL\USRP01_500.0MHz_15-06-2024-22-00-18.csv'
matrix = []
columna1 = []
fila = []

with open(file_name, mode='r') as file:
    reader = csv.reader(file)
    
    # Iterar sobre cada fila en el archivo CSV
    for idx, row in enumerate(reader):
        if idx == 0:
            # Omitir la primera fila para agregar solo a columna1
            continue
        if idx == 1:  # Si es la segunda fila (índice 1 en base 0)
            fila = row  # Guardar la segunda fila en la lista fila
            #break       # Terminar el bucle después de leer la segunda fila
        
        # Agregar desde la segunda columna hasta el final a la matriz
        matrix.append([float(val) for val in row[1:]])  # Convertir valores a float
        
        # Agregar el primer elemento de cada fila a columna1
        columna1.append(row[0])

# Step 2: Remove the first row from matrix (if exists)
if matrix:
    matrix.pop(0)  # Eliminar la primera fila de la matriz
    
if columna1:
    columna1.pop(0)  # Eliminar el primer elemento de columna1
    
if fila: 
    fila.pop(0)
    
colores = ['#FF6666', '#66FF66', '#6666FF', '#FFCC66', '#66CCFF', '#CC66FF', '#FF66CC', '#66FF99', '#99FF66']

#colores = ['#808080', '#808080', '#808080', '#808080', '#66CCFF', '#808080', '#808080', '#808080', '#808080']
for idx, data_row in enumerate(matrix):
    
    if len(fila) != len(data_row):
        print(f"Error: Los tamaños de fila y data_row no coinciden para la fila ")
        print(len(data_row))
        continue
    color = colores[idx % len(colores)]
    if idx == 4:  # Para los primeros 4, el marcador será pequeño
        markersize = 7
    else:  # Para los otros, el marcador será más grande
        markersize = 4
    
    # Crear una nueva figura para cada fila de matrix
    plt.plot(fila, data_row, marker='o', color=color, markersize=markersize, label=f'{columna1[idx]}dB')


# Añadir título y etiquetas

plt.title('USRP - RX Calibration',fontsize=23)
plt.xlabel('Generator Power (dBm)',fontsize=19)
plt.ylabel('Measured Power (dBm)',fontsize=19)
#plt.xlim(-40, -20)  # Reemplaza min_x y max_x con los valores deseados
plt.ylim(-45,-15)
#plt.xlim(-40, -20)  # Reemplaza min_x y max_x con los valores deseados
plt.grid(True)
plt.legend(fontsize=13, loc="upper left")  # Ajusta el tamaño de la fuente de las etiquetas de la gráfica
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)


# Mostrar la gráfica
plt.show()
