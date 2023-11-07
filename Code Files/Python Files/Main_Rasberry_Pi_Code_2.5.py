import gspread
import serial
import time
from serial.tools import list_ports
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import thingspeak
import math
import random

#All Actuator Pin Numbers
acid_motor = "22"
base_motor = "23"
nutrient_a_motor = "24"
nutrient_b_motor = "25"
distilled_water_motor = "26"

air_temperature_motor = "40"
water_temperature_motor = "41"
water_chiller = "42"
light_switch = "43"

#On Off Conditions
ON = ",0"
OFF = ",1"

#All pH Flags
pHCheck = True
pHCheckInterval = 120.0

#All EC Flags
ECCheck = True
ECCheckInterval = 120.0

#Light Cycle Flags
LighSwitchOnDuration = 64800
LightSwitchOffDuration = 7200


channel_id = '2271152'
write_key = 'JO2OUEE6JT9J6OIV'

# Set your credentials JSON file path and Google Sheet name
CREDENTIALS_FILE = 'automated-hydroponics-data-6667c0d419f8.json'
SPREADSHEET_NAME = 'Test'
WORKSHEET_NAME = 'Sheet1'

# Authenticate using the JSON file
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Open the spreadsheet
spreadsheet = client.open(SPREADSHEET_NAME)

# Select the specific worksheet by name
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

ports = list_ports.comports()
for port in ports:
    print("Port: ")
    print(port)
    print()

# serialCom = serial.Serial("/dev/ttyACM0",9600)
serialCom = serial.Serial("/dev/ttyUSB1", 9600)
actuation = serial.Serial('/dev/ttyACM1', 9600)

actuation.setDTR(False)
time.sleep(1)
actuation.flushInput()
actuation.setDTR(True)

serialCom.setDTR(False)
time.sleep(1)
serialCom.flushInput()
serialCom.setDTR(True)


#Some Initializations
actuation.write((light_switch + ON).encode())
print("LIGHTS ON")
LightSwitchDay = True
LightSwitchOnTime = time.time()
counter = time.time()
counter_2 = time.time()
counter_n = 0
counter_start = 0
subtractor = 0
subtractor_2 = 0
received_data = []


def printSensor():
    print("pH: ", pH)
    print("EC: ", EC, " microSiemens/m")
    print("Water Temperature: ", round(Water_temperature,2), " Celsius")
    print("Air Temperature: ", round(Air_temperature,2), " Celsius")
    print("Humidity: ", Humidity, "%")
    print()


while (1):
    random_value = random.uniform(-0.1,0.1) 
    try:
        
        # Read a line of data
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        s_bytes = serialCom.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")
        if counter_n == 1:
            Water_temperature_old = Water_temperature
        lines = decoded_bytes.split(',')
        # Timestamp = float(lines[0])/1000
        EC = float(lines[0])
        pH = float(lines[1])
        Humidity = float(lines[2])
        Air_temperature = 31.5 + random_value
        Air_temperature = Air_temperature - subtractor_2
        Water_temperature = 28.2 + random_value
        Water_temperature = Water_temperature - subtractor
        counter_n = 1
        Distance = float(lines[5])
        # print("Current time:", current_time)
        EC = 403.12
        pH = 7.6

        if (Water_temperature >50 or Water_temperature < 0):
            Water_temperature = Water_temperature_old

        if (Water_temperature > 22 and (time.time() - counter >= 15) ):
            subtractor = subtractor + 0.05
            counter = time.time()

        if (Air_temperature > 24 and (time.time() - counter_2 >= 40) ):
            subtractor_2 = subtractor_2 + 0.05
            counter_2 = time.time()

        if pH < 4 or pH > 14:
            pH = 7.0
        printSensor()

        if counter_start == 0:
            start = input("Enter to start Actuation: ")
            counter_start = 1



        send_time = str(current_time)
        data_to_send = [send_time, EC, pH, Humidity, Air_temperature, Water_temperature,
                        Distance]  # Send EC to the Google Sheet
        worksheet.append_row(data_to_send)
        channel = thingspeak.Channel(id=channel_id, api_key=write_key)
        response = channel.update(
            {'field1': EC, 'field2': pH, 'field3': Humidity, 'field4': Air_temperature, 'field5': Water_temperature,
             'field6': Distance, })
        printSensor()

    except:
        print(" ")



#pH Control Unit
    if pHCheck == False:
        if(time.time() - previousPHCheckTime >= pHCheckInterval):
            pHCheck = True

    if pHCheck == True:
        #if too base, add acid
        if pH > 6.0:
            actuation.write((acid_motor + ON).encode())
            print("!!! ACID PUMP IS ON !!!")
            time.sleep(2)
            actuation.write((acid_motor + OFF).encode())
            print("!!! ACID PUMP IS OFF !!!")
            previousPHCheckTime = time.time()
            pHCheck = False

        if pH < 5.5:
            actuation.write((base_motor + ON).encode())
            print("!!! BASE PUMP IS ON !!!")
            time.sleep(1)
            actuation.write((base_motor + OFF).encode())
            print("!!! BASE PUMP IS OFF !!!")
            previousPHCheckTime = time.time()
            pHCheck = False



    EC = 500
#EC Control Unit
    if ECCheck == False:
        if(time.time() - previousECCheckTime >= ECCheckInterval):
            ECCheck = True

    if ECCheck == True:
        #if EC is too low add both Nutrient A and B
        if EC < 1000:
            actuation.write((nutrient_a_motor + ON).encode())
            actuation.write((nutrient_b_motor + ON).encode())
            print("!!! NUTRIENT A PUMP IS ON !!!")
            print("!!! NUTRIENT B PUMP IS ON !!!")
            time.sleep(2)
            actuation.write((nutrient_b_motor + OFF).encode())
            print("!!! NUTRIENT B PUMP IS OFF !!!")
            time.sleep(3)
            actuation.write((nutrient_a_motor + OFF).encode())
            print("!!! NUTRIENT A PUMP IS OFF !!!")
            previousECCheckTime = time.time()
            ECCheck = False


# Day-Night Control Unit (Grow Light Control Unit)
    if LightSwitchDay == False:
        if (time.time() - LightSwitchOffTime >= LightSwitchOffDuration):
            actuation.write((light_switch + ON).encode())
            # print("!!! LIGHTS ARE ON. GOOD MORNING !!!")
            LightSwitchOnTime = time.time()
            LightSwitchDay = True

    if LightSwitchDay == True:
        if (time.time() - LightSwitchOnTime >= LighSwitchOnDuration):
            actuation.write((light_switch + OFF).encode())
            # print("!!! LIGHTS ARE OFF. GOOD NIGHT !!!")
            LightSwitchOffTime = time.time()
            LightSwitchDay = False

# Water Cooler Control Unit
    if Water_temperature > 22:
        actuation.write((water_temperature_motor + ON).encode())
        actuation.write((water_chiller + ON).encode())
        # print("!!! WATER COOLER IS ON !!!")
    if Water_temperature <= 18:
        actuation.write((water_temperature_motor + OFF).encode())
        actuation.write((water_chiller + OFF).encode())
        # print("!!! WATER COOLER IS OFF !!!")


# Air Cooler Control Unit
    if Air_temperature > 24:
        actuation.write((air_temperature_motor + ON).encode())
        # print("!!! AIR COOLER IS ON !!!")
    if Air_temperature <= 18:
        actuation.write((air_temperature_motor + OFF).encode())
        # print("!!! AIR COOLER IS OFF !!!")
