import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Función para calcular la distancia Euclidiana para relPos
def calcular_distancia_relPos(df):
    df['Distance'] = np.sqrt(df['R_N/Lon']**2 + df['R_E/Lat']**2 + (df['R_D/Hgt']/1000)**2)  # Convertir altitud a metros
    return df

# Función para calcular la distancia 3D para absPos
def calcular_distancia_absPos(df, ref_lat, ref_lon, ref_alt):
    df['Lat_rad'] = np.radians(df['R_E/Lat'])
    df['Lon_rad'] = np.radians(df['R_N/Lon'])
    ref_lat_rad = np.radians(ref_lat)
    ref_lon_rad = np.radians(ref_lon)

    R = 6371  # Radio de la Tierra en kilómetros
    delta_lat = df['Lat_rad'] - ref_lat_rad
    delta_lon = df['Lon_rad'] - ref_lon_rad
    a = np.sin(delta_lat / 2)**2 + np.cos(ref_lat_rad) * np.cos(df['Lat_rad']) * np.sin(delta_lon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    horizontal_distance_km = R * c  # Distancia horizontal en kilómetros

    horizontal_distance_m = horizontal_distance_km * 1000

    delta_alt = (df['R_D/Hgt']) - ref_alt
    df['Distance'] = np.sqrt(horizontal_distance_m**2 + (delta_alt / 1000)**2)
    return df

# Función para ajustar los valores de MAG
def adjust_MAG(MAG, reference_MAG):
    adjusted_MAG = MAG - reference_MAG
    adjusted_MAG[adjusted_MAG > 180] -= 360
    adjusted_MAG[adjusted_MAG < -180] += 360
    return adjusted_MAG

# Función para corregir los valores de PowerRx basada en una ecuación proporcionada
def correct_PowerRx(row, beamwidth_func):
    correction = beamwidth_func(0) - beamwidth_func(row['MAG'])
    return row['PowerRx'] + correction

# Lista de archivos CSV que se quieren analizar
archivos_csv = [
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_08-08-2024-10-47-50.csv',
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_08-08-2024-10-53-18.csv',
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_08-08-2024-10-57-59.csv'
]

# Punto de referencia (latitud, longitud, altitud en metros)
ref_lat = 4.63600930
ref_lon = -74.08904440
ref_alt = 2579220

# Definir la función de ancho de haz (Ejemplo: modelo lineal de ancho de haz)
beamwidth_func = lambda MAG: 27.11 * np.exp(- (MAG  - 0.51)**2 / (2 * 7.02**2))

# Procesar cada archivo CSV y graficar los resultados
for archivo in archivos_csv:
    df = pd.read_csv(archivo)

    # Dividir el dataframe por PosType
    relPos_df = df[df['PosType'] == 'relPos'].copy()
    absPos_df = df[df['PosType'] == 'absPos'].copy()

    # Calcular distancias para relPos y absPos
    if not relPos_df.empty:
        relPos_df = calcular_distancia_relPos(relPos_df)

        max_power_idx_relPos = relPos_df['PowerRx'].idxmax()
        max_power_relPos = relPos_df.loc[max_power_idx_relPos]

        relPos_df['MAG'] = adjust_MAG(relPos_df['MAG'], max_power_relPos['MAG'])
        relPos_df = relPos_df[(relPos_df['MAG'] >= -10) & (relPos_df['MAG'] <= 10)]
        relPos_df['PowerRx'] = relPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
        relPos_df = relPos_df.sort_values(by=['Distance', 'PowerRx'], ascending=[True, False])
        relPos_df = relPos_df.groupby('Distance')['PowerRx'].median().reset_index()

    if not absPos_df.empty:
        absPos_df = calcular_distancia_absPos(absPos_df, ref_lat, ref_lon, ref_alt)

        max_power_idx_absPos = absPos_df['PowerRx'].idxmax()
        max_power_absPos = absPos_df.loc[max_power_idx_absPos]

        absPos_df['MAG'] = adjust_MAG(absPos_df['MAG'], max_power_absPos['MAG'])
        absPos_df = absPos_df[(absPos_df['MAG'] >= -10) & (absPos_df['MAG'] <= 10)]
        absPos_df['PowerRx'] = absPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)
        absPos_df = absPos_df.sort_values(by=['Distance', 'PowerRx'], ascending=[True, False])
        absPos_df = absPos_df.groupby('Distance')['PowerRx'].median().reset_index()

    # Graficar PowerRx vs Distancia
    plt.figure(figsize=(10, 6))
    
    if not relPos_df.empty:
        plt.plot(relPos_df['Distance'], relPos_df['PowerRx'], label=f'relPos - {archivo}', marker='o')
    
    if not absPos_df.empty:
        plt.plot(absPos_df['Distance'], absPos_df['PowerRx'], label=f'absPos - {archivo}', marker='o')

    plt.ylim((-50, -10))
    plt.xlabel('Distancia')
    plt.ylabel('PowerRx')
    plt.title(f'PowerRx vs Distancia ({archivo})')
    plt.legend()
    plt.grid(True)
    plt.show()
