import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Read the CSV file
CSV = pd.read_csv(r'C:\Users\carlo\Documents\GitHub\5G_characterization\Data\BeamWidth\USRP01_BW_MEAS_05-07-2024-15-59-13.csv')


# Extract columns into lists
AngleXZ = np.array(CSV['XZ'])
AngleYZ = np.array(CSV['YZ'])
Power = np.array(CSV['PowerRx'])

# Angel range [-180 180]

AngleXZ_adjusted = np.where(AngleXZ > 180, AngleXZ - 360, AngleXZ)
AngleYZ_adjusted = np.where(AngleYZ > 180, AngleYZ - 360, AngleYZ)

# Convert lists to numpy arrays
AngleXZ_adjusted = np.array(AngleXZ_adjusted)
AngleYZ_adjusted = np.array(AngleYZ_adjusted)
Power = np.array(Power)

# Initialize lists to store unique angles and corresponding max powers
unique_angleXZ = []
max_powerXZ = []

# Iterate over unique values in AngleXZ
for angle in np.unique(AngleXZ_adjusted):
    unique_angleXZ.append(angle)
    max_powerXZ.append(np.max(Power[AngleXZ_adjusted == angle]))

# Initialize lists to store unique angles and corresponding max powers
unique_angleYZ = []
max_powerYZ = []

# Iterate over unique values in AngleXZ
for angle in np.unique(AngleYZ_adjusted):
    unique_angleYZ.append(angle)
    max_powerYZ.append(np.max(Power[AngleYZ_adjusted == angle]))

'''
# Plotting
plt.plot(unique_angleXZ, max_powerXZ)
plt.plot(unique_angleYZ, max_powerYZ)
plt.xlabel('Angle XZ')
plt.ylabel('Max Power')
plt.title('Max Power vs. Angle XZ')
plt.grid(True)
plt.show()'''

'''
plt.figure(1)
plt.plot(unique_angleXZ, max_powerXZ)
plt.figure(2)
plt.plot(unique_angleYZ, max_powerYZ)
'''


fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('Ancho de haz')
ax1.plot(unique_angleXZ, max_powerXZ)
ax1.set_ylabel('Elevación')

ax2.plot(unique_angleYZ, max_powerYZ)
ax2.set_xlabel('Ángulo')
ax2.set_ylabel('Acimutal')

plt.show()
