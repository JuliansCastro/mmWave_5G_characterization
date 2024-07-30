import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Read the CSV file
CSV = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\BeamWidth\USRP01_BW_MEAS_19-07-2024-17-32-56.csv')
#CSV = CSV[CSV['PowerRx'] > -45]

# Check if the necessary columns exist
if 'MAG' not in CSV.columns or 'PowerRx' not in CSV.columns:
    raise ValueError('CSV file does not contain the necessary columns: MAG, PowerRx')

# Extract columns into lists
AngleAci = np.array(CSV['MAG'])
Power = np.array(CSV['PowerRx'])

# Adjust angles
AngleAci_adjusted = np.where(AngleAci > 180, AngleAci - 360, AngleAci)

# Check if Power array is empty
if len(Power) == 0:
    raise ValueError('Power array is empty')

# Find the maximum value for the angle adjustment
max_value = CSV.loc[CSV['PowerRx'].idxmax()]
Center = AngleAci_adjusted - max_value['MAG']

# Filter out NaN and Inf values
valid_indices = np.isfinite(Center) & np.isfinite(Power)
Center = Center[valid_indices]
Power = Power[valid_indices] 

# Define the Gaussian function
def gaussian(x, A, mu, sigma, const):
    return A * np.exp(- (x - mu)**2 / (2 * sigma**2)) + const

# Adjust initial parameters
initial_guess = [max(Power), 0, 1, min(Power)]  # [A, mu, sigma, const]
try:
    popt, pcov = curve_fit(gaussian, Center, Power, p0=initial_guess, maxfev=10000)
except RuntimeError as e:
    print(f"Error: {e}")
    # Optionally: Try different initial guesses or data scaling
    raise

# Extract the parameters
A, mu, sigma, const = popt

# Generate x values for the Gaussian fit line
x_fit = np.linspace(min(Center), max(Center), 1000)
y_fit = gaussian(x_fit, *popt)

# Plot the data and the Gaussian fit
plt.plot(Center, Power, 'b.', label='Data')
plt.plot(x_fit, y_fit, 'r-', label=f'Gaussian Fit: A={A:.2f}, μ={mu:.2f}, σ={sigma:.2f}, c={const:.2f}')
plt.title('Azimuthal')
plt.xlabel('Angle (°)')
plt.ylabel('Power')
plt.legend()
plt.show()

