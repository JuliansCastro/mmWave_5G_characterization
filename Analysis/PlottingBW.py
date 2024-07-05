import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# aGregar una etapa de filtrado Kalman
# Read the CSV file
CSV = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\BeamWidth\USRP01_BW_MEAS_05-07-2024-15-59-13')

# Check if the necessary columns exist
if 'XZ' not in CSV.columns or 'YZ' not in CSV.columns or 'PowerRx' not in CSV.columns:
    raise ValueError('CSV file does not contain the necessary columns: XZ, YZ, PowerRx')

# Extract columns into lists
AngleXZ = np.array(CSV['XZ'])
AngleYZ = np.array(CSV['YZ'])
Power = np.array(CSV['PowerRx'])

# Angel range [-180 180]
AngleXZ_adjusted = np.where(AngleXZ > 180, AngleXZ - 360, AngleXZ)
AngleYZ_adjusted = np.where(AngleYZ > 180, AngleYZ - 360, AngleYZ)

# Check if adjusted angles are empty
if len(AngleXZ_adjusted) == 0 or len(AngleYZ_adjusted) == 0:
    raise ValueError('Adjusted angle arrays are empty')

# Check if Power array is empty
if len(Power) == 0:
    raise ValueError('Power array is empty')

# Initialize lists to store unique angles and corresponding max powers
unique_angleXZ = []
max_powerXZ = []

# Iterate over unique values in AngleXZ
for angle in np.unique(AngleXZ_adjusted):
    powers_at_angle = Power[AngleXZ_adjusted == angle]
    if len(powers_at_angle) == 0:
        print(f'No power values found for angle XZ: {angle}')
        continue
    unique_angleXZ.append(angle)
    max_powerXZ.append(np.max(powers_at_angle))

# Initialize lists to store unique angles and corresponding max powers
unique_angleYZ = []
max_powerYZ = []

# Iterate over unique values in AngleYZ
for angle in np.unique(AngleYZ_adjusted):
    powers_at_angle = Power[AngleYZ_adjusted == angle]
    if len(powers_at_angle) == 0:
        print(f'No power values found for angle YZ: {angle}')
        continue
    unique_angleYZ.append(angle)
    max_powerYZ.append(np.max(powers_at_angle))

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('Ancho de haz')
ax1.plot(unique_angleXZ, max_powerXZ)
ax1.set_ylabel('Elevación')

ax2.plot(unique_angleYZ, max_powerYZ)
ax2.set_xlabel('Ángulo')
ax2.set_ylabel('Acimutal')

plt.show()
