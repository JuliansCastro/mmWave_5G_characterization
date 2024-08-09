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

# Cargar el archivo CSV
df = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024-12-46-06.csv')

# Dividir el dataframe basado en PosType
relPos_df = df[df['PosType'] == 'relPos'].copy()
absPos_df = df[df['PosType'] == 'absPos'].copy()

# Punto específico de referencia (latitud, longitud, altitud en metros)
ref_lat = 4.63955790  # Latitud de referencia en grados
ref_lon = -74.08166900  # Longitud de referencia en grados
ref_alt = 2593.178  # Altitud de referencia en metros

# Calcular distancias para relPos y absPos
relPos_df = calcular_distancia_relPos(relPos_df)
absPos_df = calcular_distancia_absPos(absPos_df, ref_lat, ref_lon, ref_alt)

# Procesar datos de relPos
if not relPos_df.empty:
    max_power_idx_relPos = relPos_df['PowerRx'].idxmax()
    max_power_relPos = relPos_df.loc[max_power_idx_relPos]
    
    # Ajustar valores de MAG
    relPos_df['MAG'] = adjust_MAG(relPos_df['MAG'], max_power_relPos['MAG'])
    print(relPos_df)
    
    # Definir la función de ancho de haz (Ejemplo: modelo lineal de ancho de haz)
    beamwidth_func = lambda MAG: 27.11 * np.exp(- (MAG  - 0.51)**2 / (2 * 7.02**2)) # Función de ejemplo
    
    # Corregir PowerRx basada en la función de ancho de haz
    relPos_df['PowerRx'] = relPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
    
    print(relPos_df)
    
    # Ordenar por distancia y PowerRx
    relPos_df = relPos_df.sort_values(by=['Distance', 'PowerRx'], ascending=[True, False])
    
    # Calcular la mediana de PowerRx para cada distancia
    relPos_df = relPos_df.groupby('Distance')['PowerRx'].median().reset_index()


# Procesar datos de absPos
if not absPos_df.empty:
    max_power_idx_absPos = absPos_df['PowerRx'].idxmax()
    max_power_absPos = absPos_df.loc[max_power_idx_absPos]
    
    # Ajustar valores de MAG
    absPos_df['MAG'] = adjust_MAG(absPos_df['MAG'], max_power_absPos['MAG'])
    
    # Corregir PowerRx basada en la función de ancho de haz
    absPos_df['PowerRx'] = absPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
    
    # Ordenar por distancia y PowerRx
    absPos_df = absPos_df.sort_values(by=['Distance', 'PowerRx'], ascending=[True, False])
    
    # Calcular la mediana de PowerRx para cada distancia
    absPos_df = absPos_df.groupby('Distance')['PowerRx'].median().reset_index()

# Graficar PowerRx en función de la distancia

# Gráfica para relPos
plt.figure(figsize=(10, 6))
plt.plot(relPos_df['Distance'], relPos_df['PowerRx'], label='relPos', marker='o')
plt.xlabel('Distancia')
plt.ylabel('PowerRx')
plt.title('PowerRx vs Distancia (relPos)')
plt.legend()
plt.grid(True)
plt.show()

# Gráfica para absPos
plt.figure(figsize=(10, 6))
plt.plot(absPos_df['Distance'], absPos_df['PowerRx'], label='absPos', marker='o')
plt.xlabel('Distancia')
plt.ylabel('PowerRx')
plt.title('PowerRx vs Distancia (absPos)')
plt.legend()
plt.grid(True)
plt.show()
