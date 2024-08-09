import pandas as pd
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2
import numpy as np
'''
# Function to calculate the distance between two points (lat, lon, alt)
def calculate_distance(lat1, lon1, alt1, lat2, lon2, alt2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Haversine formula for horizontal distance
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    horizontal_distance = R * c

    # Calculate the vertical distance
    vertical_distance = alt2 - alt1

    # Total distance considering the altitude difference
    total_distance = sqrt(horizontal_distance**2 + vertical_distance**2)
    return total_distance

# Fixed position (lat, lon, alt)
fixed_position = (lat1, lon1, alt1) = (lat_value, lon_value, alt_value)  # Replace with actual values 
'''

# Function to calculate the distance between two points using Dis_N and Dis_E
def calculate_distance(dis_n1, dis_e1, dis_n2, dis_e2):
    # Horizontal distance using Dis_N and Dis_E
    horizontal_distance = sqrt((dis_n2 - dis_n1)**2 + (dis_e2 - dis_e1)**2)
    return horizontal_distance

# Function to calculate the circular difference
def circular_difference(a, b):
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)

# Fixed position (Dis_N, Dis_E)
fixed_position = (dis_n1, dis_e1) = (0, 0)  # Replace with actual values

# Read the CSV file
df = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_01-08-2024-13-10-13.csv')

df1 = df[df['PosType']=='relPos']

# Filter rows where BW is greater than or equal to a specific value
BW = 10  # Change this value as needed
# Get the first value of the 'YZ' column
first_value1 = df1.loc[df1['PowerRx'].idxmax()]
first_value = first_value1['MAG']
df_max = df1.loc[df1.groupby('R_N/Lon')['PowerRx'].idxmax()]
# Filter the DataFrame according to the circular condition
filtered_df = df_max[df_max['MAG'].apply(lambda x: circular_difference(x, first_value) <= BW)]

# Calculate the distance for each row
distance = filtered_df.apply(lambda row: calculate_distance(dis_n1, dis_e1, row['R_N/Lon'], row['R_E/Lat']), axis=1)
'''
# Calculate correlation coefficient
correlation_coef = np.corrcoef(filtered_df['Dist_N'], filtered_df['Dist_E'])[0, 1]

plt.scatter(filtered_df['Dist_N'], filtered_df['Dist_E'], label='Datos Dispersos', color='red')

# Add linear regression line
plt.plot(np.unique(filtered_df['Dist_N']), np.poly1d(np.polyfit(filtered_df['Dist_N'], filtered_df['Dist_E'], 1))(np.unique(filtered_df['Dist_N'])),
         color='blue', label=f'Correlación: {correlation_coef:.2f}')
'''
coeffs = np.polyfit(distance, filtered_df['PowerRx'], 4)
poly = np.poly1d(coeffs)
fitted_curve = poly(distance)
print(poly)

first_valuePower = filtered_df['PowerRx'].iloc[0]
Losses = first_valuePower-filtered_df['PowerRx']



plt.plot(distance, Losses, 'o-')
# plt.plot(distance, fitted_curve, label=f'Polinomio ajustado (grado 2): y = {coeffs[0]:.2f}x^2 + {coeffs[1]:.2f}x + {coeffs[2]:.2f}', color='red')
plt.ylabel('Power')
plt.xlabel('Distance')
plt.title('Power vs Distance')
plt.grid(True)
plt.show()
'''

from scipy.optimize import curve_fit

# Filtrar valores no válidos para el ajuste logarítmico
valid_indices = distance > 0
distance_valid = distance[valid_indices]
power_rx_valid = Losses[valid_indices]

# Función polinómica de grado 2
def polynomial_func(x, a, b, c, d, e, f):
    return a * x**2 + b * x + c + d * x**3 + e * x**4 + f * x**5 

# Función exponencial
def exponential_func(x, a, b):
    return a * np.exp(b * x)

# Función logarítmica
def logarithmic_func(x, a, b):
    return a * np.log(x) + b + a * x**2 + b * x

# Ajustar las curvas
popt_poly, pcov_poly = curve_fit(polynomial_func, distance, Losses)
popt_exp, pcov_exp = curve_fit(exponential_func, distance, Losses)

# Proveer parámetros iniciales para el ajuste logarítmico
initial_params = [1, 1]  # Ajustar estos valores según sea necesario

try:
    popt_log, pcov_log = curve_fit(logarithmic_func, distance_valid, power_rx_valid, p0=initial_params, maxfev=5000)
    log_fit_success = True
except RuntimeError:
    log_fit_success = False
    print("Logarithmic fit did not converge")

# Imprimir las ecuaciones en la consola
poly_eq = f"{popt_poly[0]:.5f} * x^2 + {popt_poly[1]:.5f} * x + {popt_poly[2]:.5f}"
exp_eq = f"{popt_exp[0]:.5f} * exp({popt_exp[1]:.5f} * x)"
if log_fit_success:
    log_eq = f"{popt_log[0]:.5f} * log(x) + {popt_log[1]:.5f}"
else:
    log_eq = "Logarithmic fit did not converge"

print("Polynomial Fit Equation: ", poly_eq)
print("Exponential Fit Equation: ", exp_eq)
print("Logarithmic Fit Equation: ", log_eq)

# Graficar los datos y las curvas ajustadas
plt.scatter(distance, Losses, label='Data')
plt.plot(distance, polynomial_func(distance, *popt_poly), 'r-', label='Polynomial Fit')
plt.plot(distance, exponential_func(distance, *popt_exp), 'g-', label='Exponential Fit')

if log_fit_success:
    plt.plot(distance, logarithmic_func(distance, *popt_log), 'b-', label='Logarithmic Fit')

plt.xlabel('Distance')
plt.ylabel('PowerRx')
plt.legend()
plt.show()
'''
'''
from scipy.optimize import curve_fit

# Filtrar valores no válidos para el ajuste logarítmico
valid_indices = distance > 0
distance_valid = distance[valid_indices]
power_rx_valid = filtered_df['PowerRx'][valid_indices]

# Definir funciones para ajustar

# Función polinómica de grado 2
def polynomial_func(x, a, b, c):
    return a * x**2 + b * x + c

# Función exponencial
def exponential_func(x, a, b):
    return a * np.exp(b * x)

# Función logarítmica
def logarithmic_func(x, a, b):
    return a * np.log(x) + b

# Ajustar las curvas
popt_poly, pcov_poly = curve_fit(polynomial_func, distance, filtered_df['PowerRx'])
popt_exp, pcov_exp = curve_fit(exponential_func, distance, filtered_df['PowerRx'])

# Proveer parámetros iniciales para el ajuste logarítmico
initial_params = [1, 1]  # Ajustar estos valores según sea necesario

try:
    popt_log, pcov_log = curve_fit(logarithmic_func, distance_valid, power_rx_valid, p0=initial_params, maxfev=5000)
    log_fit_success = True
except RuntimeError:
    log_fit_success = False
    print("Logarithmic fit did not converge")

# Imprimir las ecuaciones en la consola
poly_eq = f"{popt_poly[0]:.5f} * x^2 + {popt_poly[1]:.5f} * x + {popt_poly[2]:.5f}"
exp_eq = f"{popt_exp[0]:.5f} * exp({popt_exp[1]:.5f} * x)"
if log_fit_success:
    log_eq = f"{popt_log[0]:.5f} * log(x) + {popt_log[1]:.5f}"
else:
    log_eq = "Logarithmic fit did not converge"

print("Polynomial Fit Equation: ", poly_eq)
print("Exponential Fit Equation: ", exp_eq)
print("Logarithmic Fit Equation: ", log_eq)

# Graficar los datos y las curvas ajustadas
plt.scatter(distance, filtered_df['PowerRx'], label='Data')
plt.plot(distance, polynomial_func(distance, *popt_poly), 'r-', label='Polynomial Fit')
plt.plot(distance, exponential_func(distance, *popt_exp), 'g-', label='Exponential Fit')

if log_fit_success:
    plt.plot(distance, logarithmic_func(distance, *popt_log), 'b-', label='Logarithmic Fit')

plt.xlabel('Distance')
plt.ylabel('PowerRx')
plt.legend()
plt.show()
'''