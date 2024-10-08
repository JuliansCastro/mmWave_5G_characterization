import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Leer el archivo CSV
CSV = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\BeamWidth\USRP01_BW_MEAS_19-07-2024-17-32-56.csv')

# Verificar si las columnas necesarias existen
if 'MAG' not in CSV.columns or 'PowerRx' not in CSV.columns:
    raise ValueError('El archivo CSV no contiene las columnas necesarias: MAG, PowerRx')

# Extraer las columnas en listas
AngleAci = np.array(CSV['MAG'])
Power = np.array(CSV['PowerRx'])

# Ajustar los ángulos
AngleAci_adjusted = np.where(AngleAci > 180, AngleAci - 360, AngleAci)

# Verificar si el array de Potencia está vacío
if len(Power) == 0:
    raise ValueError('El array de Potencia está vacío')

# Encontrar el valor máximo para el ajuste del ángulo
max_value = CSV.loc[CSV['PowerRx'].idxmax()]
Center = AngleAci_adjusted - max_value['MAG']

# Filtrar valores NaN e Inf
valid_indices = np.isfinite(Center) & np.isfinite(Power)
Center = Center[valid_indices]
Power = Power[valid_indices]

# Filtrar los valores de Center entre -10 y 10
filter_mask = (Center >= -10) & (Center <= 10)
Center_filtered = Center[filter_mask]
Power_filtered = Power[filter_mask]

# Verificar si los arrays filtrados están vacíos
if len(Center_filtered) == 0 or len(Power_filtered) == 0:
    raise ValueError('Los arrays filtrados están vacíos después de aplicar el límite.')

# Definir la función gaussiana
def gaussian(x, A, mu, sigma, const):
    return A * np.exp(- (x - mu)**2 / (2 * sigma**2)) + const

# Ajustar los parámetros iniciales
initial_guess = [max(Power_filtered), 0, 1, min(Power_filtered)]  # [A, mu, sigma, const]

# Ajustar la curva solo con los datos filtrados
try:
    popt, pcov = curve_fit(gaussian, Center_filtered, Power_filtered, p0=initial_guess, maxfev=10000)
except RuntimeError as e:
    print(f"Error: {e}")
    raise

# Extraer los parámetros ajustados
A, mu, sigma, const = popt

# Generar los valores x para la línea ajustada
x_fit = np.linspace(min(Center_filtered), max(Center_filtered), 1000)
y_fit = gaussian(x_fit, *popt)
plt.xlim(-10, 10)
# Graficar los datos filtrados y el ajuste gaussiano
plt.scatter(Center_filtered, Power_filtered, color='c', label='Measured Data',s=10)
plt.plot(x_fit, y_fit, color='#FF1A1A', label=f'Gaussian Curve Fitting: A={A:.2f}, μ={mu:.2f}, σ={sigma:.2f}, c={const:.2f}', linewidth=3)
plt.title('Beam Width',fontsize=23)
plt.xlabel('Angle (°)',fontsize=19)
plt.ylabel('Power [dB]',fontsize=19)
plt.legend(fontsize=18)  # Ajusta el tamaño de la fuente de las etiquetas de la gráfica
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.legend()
plt.show()
