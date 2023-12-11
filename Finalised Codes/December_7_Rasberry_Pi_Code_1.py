import serial
import time
from serial.tools import list_ports
import datetime
import thingspeak
import math

#Thing Speak Credentials
channel_id = '2271152'
write_key = 'JO2OUEE6JT9J6OIV'

# All pH Flags
pHCheck = True
pHCheckInterval = 120.0  # Seconds

# All EC Flags
ECCheck = True
ECCheckInterval = 120.0

# Light Cycle Flags
LighSwitchOnDuration = 18*(60*60)  # hours * (3600)
LightSwitchOffDuration = 2*(60*60)

# Actuators Pin Numbers
air_temperature_motor = "50"

forty = '40'
CO2_relay = "38"
light_switch = '36'
water_chiller_motor = '34'

base_motor = '48'
acid_motor = '46'
nutrient_B_motor = '44'
nutrient_A_motor = '42'

# On Off Conditions
ON = ",0"
OFF = ",1"

#See the available ports to use in Serial Communication address
ports = list_ports.comports()
for port in ports:
    print("Port: ")
    print(port)
    print()

#Serial Communication , Adress Must be changed in Raspberry Pi
sensing = serial.Serial("COM14", 9600)   #/dev/ttyUSB1
actuation = serial.Serial('COM5', 9600)  #dev/ttyACM1

actuation.setDTR(False)
time.sleep(1)
actuation.flushInput()
actuation.setDTR(True)

sensing.setDTR(False)
time.sleep(1)
sensing.flushInput()
sensing.setDTR(True)

received_data = []

# # Some Initializations
# actuation.write((light_switch + ON).encode())
# print("LIGHTS ON")
# LightSwitchDay = True
# LightSwitchOnTime = time.time()

def printSensor():
    """ This Function prints The sensor values """
    print("CO2: ", CO2, "PPM")
    print("Air Temperature: ", round(Air_temperature, 2), " Celsius")
    print("Humidity: ", Humidity, "%")
    print("EC: ", EC, " micro-siemens/cm")
    print("pH: ", pH)
    print("Water Temperature: ", Water_temperature, " Celsius")
    print("Water Level: ", round(Water_level, 2), " cm")
    print()

while (1):
    try:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        # Read a line of data From Actuation (Mega)
        s_bytes = actuation.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")
        lines = decoded_bytes.split(',')
        CO2 = float(lines[0])
        Air_temperature = float(lines[1])
        Humidity = float(lines[2])

        # Read a line of data From Sensing (Nano)
        s_bytes_sensing = sensing.readline()
        decoded_bytes_sensing = s_bytes_sensing.decode("utf-8").strip("\n\r")
        lines_sensing = decoded_bytes_sensing.split(',')
        EC = float(lines_sensing[0])
        pH = float(lines_sensing[1])
        Water_temperature = float(lines_sensing[2])
        Water_level = float(lines_sensing[3])

        if (Water_temperature >50 or Water_temperature <0):
            Water_temperature = 21

        #Thing Speak Code
        send_time = str(current_time)
        data_to_send = [send_time, EC, pH, Humidity, Air_temperature, Water_temperature,
                        Water_level]  # Send EC to the Google Sheet
        channel = thingspeak.Channel(id=channel_id, api_key=write_key)
        response = channel.update(
            {'field1': EC, 'field2': pH, 'field3': Humidity, 'field4': Air_temperature, 'field5': Water_temperature,
             'field6': Water_level, 'field7': CO2, })

        printSensor()


    except:
        print("")




    # # pH Control Unit
    # if pHCheck == False:
    #     if (time.time() - previousPHCheckTime >= pHCheckInterval):
    #         pHCheck = True
    #
    # if pHCheck == True:
    #     # if too base, add acid
    #     if pH > 6.5:
    #         actuation.write((acid_motor + ON).encode())
    #         print("!!! ACID PUMP IS ON !!!")
    #         time.sleep(1.5)
    #         actuation.write((acid_motor + OFF).encode())
    #         print("!!! ACID PUMP IS OFF !!!")
    #         previousPHCheckTime = time.time()
    #         pHCheck = False
    #
    #     if pH < 5.8:
    #         actuation.write((base_motor + ON).encode())
    #         print("!!! BASE PUMP IS ON !!!")
    #         time.sleep(1)
    #         actuation.write((base_motor + OFF).encode())
    #         print("!!! BASE PUMP IS OFF !!!")
    #         previousPHCheckTime = time.time()
    #         pHCheck = False
    #
    #
    # # EC Control Unit
    # if ECCheck == False:
    #     if (time.time() - previousECCheckTime >= ECCheckInterval):
    #         ECCheck = True
    #
    # if ECCheck == True:
    #     # if EC is too low add both Nutrient A and B
    #     if EC < 1000:
    #         actuation.write((nutrient_a_motor + ON).encode())
    #         actuation.write((nutrient_b_motor + ON).encode())
    #         print("!!! NUTRIENT A PUMP IS ON !!!")
    #         print("!!! NUTRIENT B PUMP IS ON !!!")
    #         time.sleep(1)
    #         actuation.write((nutrient_b_motor + OFF).encode())
    #         print("!!! NUTRIENT B PUMP IS OFF !!!")
    #         time.sleep(3)
    #         actuation.write((nutrient_a_motor + OFF).encode())
    #         print("!!! NUTRIENT A PUMP IS OFF !!!")
    #         previousECCheckTime = time.time()
    #         ECCheck = False
    #
    # # Day-Night Control Unit (Grow Light Control Unit)
    # if LightSwitchDay == False:
    #     if (time.time() - LightSwitchOffTime >= LightSwitchOffDuration):
    #         actuation.write((light_switch + ON).encode())
    #         # print("!!! LIGHTS ARE ON. GOOD MORNING !!!")
    #         LightSwitchOnTime = time.time()
    #         LightSwitchDay = True
    #
    # if LightSwitchDay == True:
    #     if (time.time() - LightSwitchOnTime >= LighSwitchOnDuration):
    #         actuation.write((light_switch + OFF).encode())
    #         # print("!!! LIGHTS ARE OFF. GOOD NIGHT !!!")
    #         LightSwitchOffTime = time.time()
    #         LightSwitchDay = False
    #
    # # Water Cooler Control Unit
    # if Water_temperature > 22:
    #     actuation.write((water_temperature_motor + ON).encode())
    #     # print("!!! WATER COOLER IS ON !!!")
    # if Water_temperature <= 18:
    #     actuation.write((water_temperature_motor + OFF).encode())
    #     # print("!!! WATER COOLER IS OFF !!!")
    #
    # # Air Cooler Control Unit
    # if Air_temperature > 24:
    #     actuation.write((air_temperature_motor + ON).encode())
    #     # print("!!! AIR COOLER IS ON !!!")
    # if Air_temperature <= 18:
    #     actuation.write((air_temperature_motor + OFF).encode())
    #     # print("!!! AIR COOLER IS OFF !!!")
    #
    # # CO2 Control Unit
    # if CO2 < 1200:
    #     actuation.write((CO2_relay + ON).encode())
    #     print("!!! CO2 Relay IS ON !!!")
    # if CO2 >= 1200:
    #     actuation.write((CO2_relay + OFF).encode())
    #     print("!!! CO2 Relay IS OFF !!!")
