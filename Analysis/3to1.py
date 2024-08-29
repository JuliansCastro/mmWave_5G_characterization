import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit

# Función para calcular la distancia Euclidiana para relPos
def calcular_distancia_relPos(df):
    df['Distance'] = np.sqrt(df['R_N/Lon']**2 + df['R_E/Lat']**2 + (df['R_D/Hgt'])**2)  # Convertir altitud a metros
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

# Función para procesar cada archivo CSV
def procesar_archivo(csv_file, beamwidth_func, distanceB):
    df = pd.read_csv(csv_file)

    # Filtrar datos basados en PosType 'relPos'
    relPos_df = df[df['PosType'] == 'relPos'].copy()

    # Calcular distancias para relPos
    if not relPos_df.empty:
        relPos_df = calcular_distancia_relPos(relPos_df)

        max_power_idx_relPos = relPos_df['PowerRx'].idxmax()
        max_power_relPos = relPos_df.loc[max_power_idx_relPos]

        # Ajustar valores de MAG
        relPos_df['MAG'] = adjust_MAG(relPos_df['MAG'], max_power_relPos['MAG'])

        # Filtrar datos por MAG en el rango [-10, 10]
        relPos_df = relPos_df[(relPos_df['MAG'] >= -10) & (relPos_df['MAG'] <= 10)]
        relPos_df = relPos_df[relPos_df['Distance'] > distanceB]

        # Corregir PowerRx basada en la función de ancho de haz
        relPos_df['PowerRx'] = relPos_df.apply(correct_PowerRx, axis=1, beamwidth_func=beamwidth_func)

        # Ordenar por distancia y PowerRx
        relPos_df = relPos_df.sort_values(by=['Distance', 'PowerRx'], ascending=[True, False])
        
        # Calcular la mediana de PowerRx para cada distancia
        relPos_df = relPos_df.groupby('Distance')['PowerRx'].median().reset_index()
        
    return relPos_df

# Listado de archivos CSV
archivos_csv = [
    r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024\5G_loss_MEAS_01-08-2024-12-58-35.csv'
]

#CSV = r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data/5G_loss/5G_loss_MEAS_20-08-2024-14-23-43.csv'   #Greenhouse 4
#CSV =r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_20-08-2024-13-17-20.csv'  #Greenhouse 3
#CSV = r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_08-08-2024\5G_loss_MEAS_08-08-2024-10-53-18.csv' # Greenhouse1
CSV = r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_08-08-2024\5G_loss_MEAS_08-08-2024-11-43-57.csv' # Greenhouse2
# Espacio libre las 3, 4 y 6, se seleccionó para la regreción la 3
# Greenhouse 1 el primero 
# Definir la función de ancho de haz
beamwidth_func = lambda MAG: 133800.55 * np.exp(- (MAG - 0.42)**2 / (2 * 633.4**2))  # Función de ejemplo

# Colores para diferenciar cada archivo en la gráfica
colores = ['c', 'b', 'g', 'r', 'm', 'y']

# Inicializar lista para almacenar resultados
relPos_data = []

# Procesar cada archivo y almacenar los resultados  
for i, csv_file in enumerate(archivos_csv):
    relPos_df = procesar_archivo(csv_file, beamwidth_func,20)
    relPos_data.append((relPos_df, colores[i]))
    
CSV_df = procesar_archivo(CSV,beamwidth_func,15)


# Graficar PowerRx en función de la distancia para relPos
plt.figure(figsize=(10, 6))
for i, (relPos_df, color) in enumerate(relPos_data):
    # Convertir distancia a logaritmo
    log_distance = 20 * np.log10(relPos_df['Distance']).values.reshape(-1, 1)
    
    # Crear un rango de valores logarítmicos para la predicción
    x_value = np.linspace(0.1, 40, 20000).reshape(-1, 1)
    
    # Ajustar el modelo de regresión lineal
    model = LinearRegression()
    model.fit(log_distance, relPos_df['PowerRx'])
    model.get_params()
    
    # Predecir valores de PowerRx
    y_pred = model.predict(x_value)
    P0 = float(y_pred[0])
    c = 299792458     # En m/s
    fc = 60.48e9  #en Hz
    wlenght = c/fc   # Lambda 
    A = 10**((P0+20*np.log10(4*np.pi/wlenght))/10)
    P = 10*np.log10(A)-20*np.log10(4*np.pi/wlenght)-x_value
    Pf = float(y_pred[99])
    fin = float(x_value[99])

    #plt.plot(relPos_df['Distance'], relPos_df['PowerRx'], label=f'Data {i+1}', marker='o', color=color)
    # plt.scatter(log_distance, relPos_df['PowerRx'], label=f'Espacio libre', marker='o', color=color) #LogLog
    # plt.plot(x_value, y_pred, label=f'Regresión espacio libre', color='b') #LogLog
    # plt.plot(x_value, P_1, label=f'Ecuación con pérdidas', color='g')
    # plt.plot(x_value, P, label=f'Ecuación espacio libre', color='r') #LogLog
def Power_Losses(x, alpha): #Function of signal Rx Power with losses
    return 10*np.log10(A/((4*np.pi*10**(x/20)/wlenght)**2))+10*np.log10(np.e**(-2*alpha*10**(x/20)))

# def PL_InHModel(x, a, b):
#     f_x = a+b*np.log10(x)+20.0*np.log10(fc)
#     return f_x

def PL_InHModel(x, a, b, c):
    f_x = a+b*np.log10(x)+20.0*np.log10(fc)+c*fc**0.248*x**0.588*0
    return f_x

PL_meas = 1-(CSV_df['PowerRx']-10*np.log10(A))

CSV_log = 20 * np.log10(CSV_df['Distance'])
alpha , a_var = curve_fit(Power_Losses, CSV_log, CSV_df['PowerRx'].values)
print('Alpha Greenhouse2',alpha)
x_value = np.linspace(0.1, 40, 20000)
PL =  1-10*np.log10((np.e**(-2*alpha*x_value))/(4*np.pi*x_value/wlenght)**2) # Path Loss custom model 

PL1 =  1-10*np.log10((np.e**(-2*alpha*CSV_df['Distance']))/(4*np.pi*CSV_df['Distance']/wlenght)**2)
#print("PL Model: ",PL_InHModel(x_value,37.2,20))
#a, b = curve_fit(PL_InHModel, x_value, PL)
a, b = curve_fit(PL_InHModel, CSV_df['Distance'], PL_meas, p0 = [0, 0, 0], bounds=([-np.inf, 0, 0], [np.inf,np.inf,np.inf]))
print(a)
correlation =np.corrcoef(PL_meas,PL_InHModel(CSV_df['Distance'],a[0],a[1],a[2]))[0, 1]
correlation = round(correlation, 3)

correlation1 =np.corrcoef(PL_meas,PL1)[0, 1]
correlation1 = round(correlation1, 3)
# plt.scatter(CSV_log, CSV_df['PowerRx'], label=f'Invernadero', marker='o', color='m') # LogLog
# plt.plot(x_value, Power_Losses(x_value,alpha), label=f'Ecuación invernadero', color='y') # LogLog
plt.plot(x_value, PL, label=f'Exponencial Model, R = {correlation1}', color='y')
plt.plot(CSV_df['Distance'], PL_meas, label=f'PL Measures', color='g')
plt.plot(x_value, PL_InHModel(x_value,a[0],a[1], a[2]), label=f'InH Modified, R = {correlation}', color='r') # 3GPP base model 
# plt.xlabel('20*log(Distance)')
# plt.ylabel('Power [dB]')
plt.xlabel('Distance [m]')
plt.ylabel('Path Loss [dB]')
plt.title('Path Loss vs Distance')
#plt.title('Power vs 20*log(Distance)')
plt.legend()
plt.grid(True)
plt.show()
