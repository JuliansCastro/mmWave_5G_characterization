import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Función para calcular la distancia Euclidiana para relPos
def calcular_distancia_relPos(df):
    df['Distance'] = np.sqrt(df['R_N/Lon']**2 + df['R_E/Lat']**2 + (df['R_D/Hgt']/1000)**2)  # Convertir altitud a metros
    return df

# Función para calcular la distancia 3D para absPos
def calcular_distancia_absPos(df, ref_lat, ref_lon, ref_alt):
    # Convertir latitud y longitud a radianes
    df['Lat_rad'] = np.radians(df['R_E/Lat'])
    df['Lon_rad'] = np.radians(df['R_N/Lon'])
    ref_lat_rad = np.radians(ref_lat)
    ref_lon_rad = np.radians(ref_lon)

    # Calcular distancia usando la fórmula de Haversine y la diferencia de altitud
    R = 6371  # Radio de la Tierra en kilómetros
    delta_lat = df['Lat_rad'] - ref_lat_rad
    delta_lon = df['Lon_rad'] - ref_lon_rad
    a = np.sin(delta_lat / 2)**2 + np.cos(ref_lat_rad) * np.cos(df['Lat_rad']) * np.sin(delta_lon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    horizontal_distance = R * c * 1000  # Convertir a metros

    # Diferencia de altitud (convertir altitud de milímetros a metros)
    delta_alt = (df['R_D/Hgt'] / 1000) - ref_alt

    # Calcular la distancia total 3D
    df['Distance'] = np.sqrt(horizontal_distance**2 + delta_alt**2)
    return df

# Función para ajustar los valores de MAG para que estén dentro de -180 a 180 grados
def adjust_MAG(MAG, reference_MAG):
    adjusted_MAG = MAG - reference_MAG
    adjusted_MAG[adjusted_MAG > 180] -= 360
    adjusted_MAG[adjusted_MAG < -180] += 360
    return adjusted_MAG

# Función para corregir los valores de PowerRx basada en una ecuación proporcionada
def correct_PowerRx(row, beamwidth_func):
    correction = beamwidth_func(0) - beamwidth_func(row['MAG'])
    return row['PowerRx'] + correction

# Función para procesar un archivo CSV
def procesar_archivo(path, ref_lat, ref_lon, ref_alt):
    df = pd.read_csv(path)
    relPos_df = df[df['PosType'] == 'relPos'].copy()
    absPos_df = df[df['PosType'] == 'absPos'].copy()

    # Calcular distancias
    relPos_df = calcular_distancia_relPos(relPos_df)
    absPos_df = calcular_distancia_absPos(absPos_df, ref_lat, ref_lon, ref_alt)

    # Definir la función de ancho de haz (Ejemplo: modelo lineal de ancho de haz)
    beamwidth_func = lambda MAG: 27.11 * np.exp(- (MAG  - 0.51)**2 / (2 * 7.02**2))  # Función de ejemplo

    # Procesar datos de relPos
    if not relPos_df.empty:
        max_power_idx_relPos = relPos_df['PowerRx'].idxmax()
        max_power_relPos = relPos_df.loc[max_power_idx_relPos]
        relPos_df['MAG'] = adjust_MAG(relPos_df['MAG'], max_power_relPos['MAG'])
        relPos_df['PowerRx'] = relPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
    
    # Procesar datos de absPos
    if not absPos_df.empty:
        max_power_idx_absPos = absPos_df['PowerRx'].idxmax()
        max_power_absPos = absPos_df.loc[max_power_idx_absPos]
        absPos_df['MAG'] = adjust_MAG(absPos_df['MAG'], max_power_absPos['MAG'])
        absPos_df['PowerRx'] = absPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
    
    return relPos_df, absPos_df

# Parámetros de referencia
ref_lat = 4.63955790  # Latitud de referencia en grados
ref_lon = -74.08166900  # Longitud de referencia en grados
ref_alt = 2593.178  # Altitud de referencia en metros

# Rutas de los archivos CSV
file_paths = [
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024-12-46-06.csv',
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024-12-58-35.csv',
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024-13-10-13.csv'
]

# Inicializar dataframes vacíos
combined_relPos_df = pd.DataFrame()
combined_absPos_df = pd.DataFrame()

for path in file_paths:
    relPos_df, absPos_df = procesar_archivo(path, ref_lat, ref_lon, ref_alt)
    if not relPos_df.empty:
        relPos_df['Source'] = path  # Añadir una columna para identificar el archivo
        combined_relPos_df = pd.concat([combined_relPos_df, relPos_df], ignore_index=True)
    if not absPos_df.empty:
        absPos_df['Source'] = path  # Añadir una columna para identificar el archivo
        combined_absPos_df = pd.concat([combined_absPos_df, absPos_df], ignore_index=True)

# Graficar PowerRx en función de la distancia

# Gráfica para relPos
plt.figure(figsize=(12, 6))
for label, df_group in combined_relPos_df.groupby('Source'):
    plt.plot(df_group['Distance'], df_group['PowerRx'], label=f'{label}', marker='o')
plt.xlabel('Distancia')
plt.ylabel('PowerRx')
plt.title('PowerRx vs Distancia (relPos) - Combinado')
plt.legend()
plt.grid(True)
plt.show()

# Gráfica para absPos
plt.figure(figsize=(12, 6))
for label, df_group in combined_absPos_df.groupby('Source'):
    plt.plot(df_group['Distance'], df_group['PowerRx'], label=f'{label}', marker='o')
plt.xlabel('Distancia')
plt.ylabel('PowerRx')
plt.title('PowerRx vs Distancia (absPos) - Combinado')
plt.legend()
plt.grid(True)
plt.show()
