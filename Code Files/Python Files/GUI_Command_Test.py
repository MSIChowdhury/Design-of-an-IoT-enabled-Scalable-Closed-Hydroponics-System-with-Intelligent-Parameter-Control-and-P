import requests

# Replace 'YOUR_API_KEY' with your ThingSpeak API key
api_key = 'A64SDPA5T2NT2M40'
base_url = f'https://api.thingspeak.com/update?api_key={api_key}'


import random

# Define the range for each variable
pH_min = 0
pH_max = 14
EC_min = 10
EC_max = 3000
A_Temp_min = 15
A_Temp_max = 50
W_Temp_min = 15
W_Temp_max = 50
Humidity_min = 30
Humidity_max = 100
Water_Level_min = 0
Water_Level_max = 10
CO2_min = 200
CO2_max = 5000


# Function to generate a random value within the specified range
def generate_random_value(min_val, max_val):
    return random.uniform(min_val, max_val)



while True:
    
    # Generate random values for the 7 variables
    pH = generate_random_value(pH_min, pH_max)
    EC = generate_random_value(EC_min, EC_max)
    A_Temp = generate_random_value(A_Temp_min, A_Temp_max)
    W_Temp = generate_random_value(W_Temp_min, W_Temp_max)
    Humidity = generate_random_value(Humidity_min, Humidity_max)
    Water_Level = generate_random_value(Water_Level_min, Water_Level_max)
    CO2 = generate_random_value(CO2_min, CO2_max)


    # Replace these with actual sensor readings for each of your 7 fields
    sensor1_value = pH  # Read from your first sensor
    sensor2_value = EC  # Read from your second sensor
    sensor3_value = A_Temp  # Read from your third sensor
    sensor4_value = W_Temp  # Read from your fourth sensor
    sensor5_value = Humidity  # Read from your fifth sensor
    sensor6_value = Water_Level # Read from your sixth sensor
    sensor7_value = CO2  # Read from your seventh sensor

    sensor_data = {
        'field1': sensor1_value,
        'field2': sensor2_value,
        'field3': sensor3_value,
        'field4': sensor4_value,
        'field5': sensor5_value,
        'field6': sensor6_value,
        'field7': sensor7_value,
    }

    response = requests.get(base_url, params=sensor_data)

    if response.status_code == 200:
        print(f"Variable 1: {pH}, Variable 2: {EC}, Variable 3: {A_Temp}, Variable 4: {W_Temp}, Variable 5: {Humidity}, Variable 6: {Water_Level}, Variable 7: {CO2}")
    else:
        print('Failed to send data to ThingSpeak')

