import pandas as pd
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2
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
df = pd.read_csv(r'C:\Users\sofia\OneDrive\Documentos\GitHub\5G_characterization\Data\5G_loss\5G_loss_MEAS_10-07-2024\5G_loss_MEAS_10-07-2024-16-24-27.csv')

# Filter rows where BW is greater than or equal to a specific value
BW = 10  # Change this value as needed
# Get the first value of the 'YZ' column
first_value = df['YZ'].iloc[0]
# Filter the DataFrame according to the circular condition
filtered_df = df[df['YZ'].apply(lambda x: circular_difference(x, first_value) <= BW)]

# Calculate the distance for each row
distance = filtered_df.apply(lambda row: calculate_distance(dis_n1, dis_e1, row['Dist_N'], row['Dist_E']), axis=1)

# Plot Distance as a function of Power
#plt.plot(filtered_df['PowerRX'], filtered_df['distance'], 'o-')
plt.plot(distance, filtered_df['PowerRx'], 'o-')
plt.ylabel('Power')
plt.xlabel('Distance')
plt.title('Distance as a function of Time')
plt.grid(True)
plt.show()
