import thingspeak
import random
from flask import Flask, render_template, request
import time
import threading

app = Flask(__name__)

# Replace 'your_ddns_hostname' with your Dynu DDNS hostname
hostname = '0.0.0.0'
port = 5000  # Use the port you configured in your code

# Provide your ThingSpeak API Write Key and Channel ID
write_key = 'A64SDPA5T2NT2M40'
channel_id = '2331508'

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
Water_Level_min = 2
Water_Level_max = 10
CO2_min = 200
CO2_max = 5000


# Function to generate a random value within the specified range
def generate_random_value(min_val, max_val):
    return random.uniform(min_val, max_val)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_variables', methods=['POST'])
def update_variables():
    selected_option = request.form.get('dropdown')
    if selected_option == 'Lettuce':
        # Update the 14 variables based on option 1
        pH_min = 5.6
        pH_max = 6.0
        EC_min = 1100
        EC_max = 1700
        A_Temp_min = 24
        A_Temp_max = 19
        W_Temp_min = 24
        W_Temp_max = 26
        Humidity_min = 50
        Humidity_max = 70
        Water_Level_min = 2
        Water_Level_max = 10
        CO2_min = 2000
        CO2_max = 5000
    elif selected_option == 'option2':
        # Update the 14 variables based on option 2
        pH_min = "new_value_pH_min_option2"
        pH_max = "new_value_pH_max_option2"
        EC_min = "new_value_EC_min_option2"
        EC_max = "new_value_EC_max_option2"
        A_Temp_min = "new_value_A_Temp_min_option2"
        A_Temp_max = "new_value_A_Temp_max_option2"
        W_Temp_min = "new_value_W_Temp_min_option2"
        W_Temp_max = "new_value_W_Temp_max_option2"
        Humidity_min = "new_value_Humidity_min_option2"
        Humidity_max = "new_value_Humidity_max_option2"
        Water_Level_min = "new_value_Water_Level_min_option2"
        Water_Level_max = "new_value_Water_Level_max_option2"
        CO2_min = "new_value_CO2_min_option2"
        CO2_max = "new_value_CO2_max_option2"
    elif selected_option == 'option3':
        # Update the 14 variables based on option 3
        pH_min = "new_value_pH_min_option3"
        pH_max = "new_value_pH_max_option3"
        EC_min = "new_value_EC_min_option3"
        EC_max = "new_value_EC_max_option3"
        A_Temp_min = "new_value_A_Temp_min_option3"
        A_Temp_max = "new_value_A_Temp_max_option3"
        W_Temp_min = "new_value_W_Temp_min_option3"
        W_Temp_max = "new_value_W_Temp_max_option3"
        Humidity_min = "new_value_Humidity_min_option3"
        Humidity_max = "new_value_Humidity_max_option3"
        Water_Level_min = "new_value_Water_Level_min_option3"
        Water_Level_max = "new_value_Water_Level_max_option3"
        CO2_min = "new_value_CO2_min_option3"
        CO2_max = "new_value_CO2_max_option3"
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host=hostname, port=port)
    app.run(debug=True)


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

    channel = thingspeak.Channel(id=channel_id, api_key=write_key)
    response = channel.update({'field1': EC, 'field2': pH, 'field3': Humidity, 'field4': A_Temp, 'field5': W_Temp, 'field6': Water_Level, 'field7': CO2})
        

