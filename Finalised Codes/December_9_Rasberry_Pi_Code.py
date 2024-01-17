import serial
import time
from serial.tools import list_ports
import datetime
import thingspeak
import math
import cv2


#Thing Speak Credentials
channel_id = '2271152'
write_key = 'JO2OUEE6JT9J6OIV'

# All pH Flags
pHCheck = True
pHCheckInterval = 10 * 60  # Seconds

# All EC Flags
ECCheck = True
ECCheckInterval = 10 * 60 # Seconds

# ~ #Take one image after this interval
# ~ image_interval = 20 * 60
# ~ day_interval = 24 * 60 * 60

# Light Cycle Flags
LighSwitchOnDuration = 16*(60*60)  # hours * (3600)
LightSwitchOffDuration = 2*(60*60)



# Actuators Pin Numbers
air_temperature_motor = "50"

water_chiller_motor = '40'
CO2_relay = "38"
alarm = '36'
light_switch = '34'

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
    

# ~ #Webcam Initialization
# ~ cap = cv2.VideoCapture(0)
# ~ day_counter = int(input("Enter the Day number: "))
# ~ image_counter = int(input("Enter the image number: "))

#Serial Communication , Adress Must be changed in Raspberry Pi
sensing = serial.Serial('/dev/ttyUSB0', 9600)   #/dev/ttyUSB1
actuation = serial.Serial('/dev/ttyACM0', 9600)  #dev/ttyACM1


actuation.setDTR(False)
time.sleep(1)
actuation.flushInput()
actuation.setDTR(True)

sensing.setDTR(False)
time.sleep(1)
sensing.flushInput()
sensing.setDTR(True)

#Array for storing data
received_data = []



def printSensor():
    """ This Function prints The sensor values """
    print('Time: ' ,datetime.datetime.now().strftime("%H:%M:%S"))
    #print('Count: ', cnt)
    print("CO2: ", CO2, "PPM")
    print("Air Temperature: ", round(Air_temperature, 2), " Celsius")
    print("Humidity: ", Humidity, "%")
    print("EC: ", EC, " micro-siemens/cm")
    print("pH: ", pH)
    print("Water Temperature: ", Water_temperature, " Celsius")
    print("Water Level: ", round(Water_level, 2), " cm")
    print()
    
# ~ def take_picture(image_counter, day_counter):
    # ~ ret, frame = cap.read()
    
    # ~ # Save the captured image with a serial name
    # ~ image_filename = f"Image_{image_counter}_Day_{day_counter}.jpg"
    # ~ cv2.imwrite(image_filename, frame)


#Reading counter
cnt = 0   

# # Some Initializations
Water_level = 10.5
actuation.write((light_switch + ON).encode())
print("LIGHTS ON")
LightSwitchDay = True
LightSwitchOnTime = time.time()

# ~ time.sleep(7)
# ~ take_picture(image_counter, day_counter)
# ~ image_counter += 1

# ~ image_time = time.time()
# ~ day_time = time.time()

while True:
    try:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        

        
        # Read a line of data From Actuation (Mega)
        s_bytes = actuation.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")
        lines = decoded_bytes.split(',')
        CO2 = float(lines[0])
        Air_temperature = float(lines[1])
        Humidity = float(lines[2])
        
        actuation.flushInput()
        time.sleep(0.1)
        

        
        # Read a line of data From Sensing (Nano)
        s_bytes_sensing = sensing.readline()
        decoded_bytes_sensing = s_bytes_sensing.decode("utf-8").strip("\n\r")
        print(decoded_bytes_sensing)
        lines_sensing = decoded_bytes_sensing.split(',')
        sense_length = len(lines_sensing)
        if sense_length == 3:
            EC = float(lines_sensing[0])
            pH = float(lines_sensing[1])
            Water_temperature = float(lines_sensing[2])
        if sense_length == 2:
            pH = lines_sensing[0]
            EC = lines_sensing[1]
            Water_temperature = 9999
        if sense_length == 1:
            pH = lines_sensing[0]
            EC = 99999
            Water_temperature = 99999
            
        sensing.flushInput()
        time.sleep(0.1)


        

        

        if Water_temperature > 50 or Water_temperature < 0:
            Water_temperature = 21

        # Thing Speak Code
        if sense_length == 3:
			
            send_time = str(current_time)
            data_to_send = [send_time, EC, pH, Humidity, Air_temperature, Water_temperature,
                            Water_level]  # Send EC to the Google Sheet
            channel = thingspeak.Channel(id=channel_id, api_key=write_key)
            response = channel.update(
                {'field1': EC, 'field2': pH, 'field3': Humidity, 'field4': Air_temperature, 'field5': Water_temperature,
                 'field6': Water_level, 'field7': CO2})

        # Print sensor values
        printSensor()
        cnt += 1

    except Exception as e:
        print("Error happened in code:", e)

    # Day-Night Control Unit (Grow Light Control Unit)
    if LightSwitchDay:
        if time.time() - LightSwitchOnTime >= LighSwitchOnDuration:
            actuation.write((light_switch + OFF).encode())
            print("!!! LIGHTS ARE OFF. GOOD NIGHT !!!")
            LightSwitchOffTime = time.time()
            LightSwitchDay = False

    if not LightSwitchDay:
        if time.time() - LightSwitchOffTime >= LightSwitchOffDuration:
            actuation.write((light_switch + ON).encode())
            print("!!! LIGHTS ARE ON. GOOD MORNING !!!")
            LightSwitchOnTime = time.time()
            LightSwitchDay = True

    # ~ # pH Control Unit
    # ~ if not pHCheck:
        # ~ if time.time() - previousPHCheckTime >= pHCheckInterval:
            # ~ pHCheck = True

    # ~ if pHCheck and EC > 900:
        # ~ # if too basic, add acid
        # ~ if pH > 6.5:
            # ~ actuation.write((acid_motor + ON).encode())
            # ~ print("!!! ACID PUMP IS ON !!!")
            # ~ time.sleep(0.2)
            # ~ actuation.write((acid_motor + OFF).encode())
            # ~ print("!!! ACID PUMP IS OFF !!!")
            # ~ previousPHCheckTime = time.time()
            # ~ pHCheck = False

        # ~ if pH < 5.7:
            # ~ actuation.write((base_motor + ON).encode())
            # ~ print("!!! BASE PUMP IS ON !!!")
            # ~ time.sleep(0.8)
            # ~ actuation.write((base_motor + OFF).encode())
            # ~ print("!!! BASE PUMP IS OFF !!!")
            # ~ previousPHCheckTime = time.time()
            # ~ pHCheck = False

    # ~ # EC Control Unit
    # ~ if not ECCheck:
        # ~ if time.time() - previousECCheckTime >= ECCheckInterval:
            # ~ ECCheck = True

    # ~ if ECCheck:
        # ~ # if EC is too low add both Nutrient A and B
        # ~ if EC < 900:
            # ~ actuation.write((nutrient_A_motor + ON).encode())
            # ~ actuation.write((nutrient_B_motor + ON).encode())
            # ~ print("!!! NUTRIENT A PUMP IS ON !!!")
            # ~ print("!!! NUTRIENT B PUMP IS ON !!!")
            # ~ time.sleep(1.2)
            # ~ actuation.write((nutrient_B_motor + OFF).encode())
            # ~ print("!!! NUTRIENT B PUMP IS OFF !!!")
            # ~ time.sleep(1.6)
            # ~ actuation.write((nutrient_A_motor + OFF).encode())
            # ~ print("!!! NUTRIENT A PUMP IS OFF !!!")
            # ~ previousECCheckTime = time.time()
            # ~ ECCheck = False

    # ~ # Water Cooler Control Unit
    # ~ if Water_temperature > 22:
        # ~ actuation.write((water_chiller_motor + ON).encode())
        # ~ # print("!!! WATER COOLER IS ON !!!")
    # ~ if Water_temperature <= 18:
        # ~ actuation.write((water_chiller_motor + OFF).encode())
        # ~ # print("!!! WATER COOLER IS OFF !!!")

    # ~ # Air Cooler Control Unit
    # ~ if Air_temperature > 22:
        # ~ actuation.write((air_temperature_motor + ON).encode())
        # ~ # print("!!! AIR COOLER IS ON !!!")
    # ~ if Air_temperature <= 18:
        # ~ actuation.write((air_temperature_motor + OFF).encode())
        # ~ # print("!!! AIR COOLER IS OFF !!!")

    # CO2 Control Unit
    # ~ if CO2 < 2000:
        # ~ actuation.write((CO2_relay + ON).encode())
        # ~ print("!!! CO2 Relay IS ON !!!")
    # ~ if CO2 >= 2100:
        # ~ actuation.write((CO2_relay + OFF).encode())
        # ~ print("!!! CO2 Relay IS OFF !!!")
