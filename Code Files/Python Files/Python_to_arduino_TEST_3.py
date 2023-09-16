import serial
import time
from serial.tools import list_ports

ports = list_ports.comports()
for port in ports:
    print(port)

#All Actuator Pin Numbers
acid_motor = "22"
base_motor = "23"
nutrient_a_motor = "24"
nutrient_b_motor = "25"
distilled_water_motor = "26"

air_temperature_motor = "13"
water_temperature_motor = "41"
light_switch = "42"

#On Off Conditions
ON = ",0"
OFF = ",1"

#All pH Flags
pHCheck = True
pHAcidOnFlag = False
pHBaseOnFlag = False
pHPumpDuration = 2.0
pHCheckInterval = 2.0

#All EC Flags
ECCheck = True
ECAOnFlag = False
ECBOnFlag = False
ECAPumpDuration = 4.0
ECBPumpDuration = 2.0
ECCheckInterval = 5.0

#Light Cycle Flags
LighSwitchOnDuration = 60 #64800
LightSwitchOffDuration = 60 #7200


#Serial Communication classes
actuation = serial.Serial('COM5', 9600)
serialCom = serial.Serial("COM9",9600)

actuation.setDTR(False)
time.sleep(1)
actuation.flushInput()
actuation.setDTR(True)

serialCom.setDTR(False)
time.sleep(1)
serialCom.flushInput()
serialCom.setDTR(True)

pH = 4
time.sleep(1)

#Some Initializations
actuation.write((light_switch + ON).encode())
LightSwitchDay = True
LightSwitchOnTime = time.time()
received_data = []

while(1):

#Reading Sensor Values
    try:
        #Read a line of data
        s_bytes = serialCom.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")

        lines = decoded_bytes.split(',')

        EC = float(lines[0])
        pH = float(lines[1])
        Humidity = float(lines[2])
        Air_temperature = float(lines[3])
        Water_temperature = float(lines[4])
        Distance = float(lines[5])

        print(EC/2)

    except:
        print("ERROR! There was an error in the code!")

# #pH Control Unit
#     if pHCheck == False:
#         if(time.time() - previousPHCheckTime >= pHCheckInterval):
#             pHCheck = True
#
#     if pHCheck == True:
#         #if too base, add acid
#         if pH > 6.5:
#             if pHAcidOnFlag == False:
#                 pHAcidOnTime = time.time()
#                 actuation.write((acid_motor + ON).encode())
#                 print("!!! ACID PUMP IS ON !!!")
#                 pHAcidOnFlag = True
#
#         if pHAcidOnFlag == True :
#             if(time.time() - pHAcidOnTime >= pHPumpDuration):
#                 actuation.write((acid_motor + OFF).encode())
#                 print("!!! ACID PUMP IS OFF !!!")
#                 previousPHCheckTime = time.time()
#                 pHCheck = False
#                 pHAcidOnFlag = False
#
#         #if too acidic, add base
#         if pH < 5.5:
#             if pHBaseOnFlag == False:
#                 pHBaseOnTime = time.time()
#                 actuation.write((base_motor + ON).encode())
#                 print("!!! BASE PUMP IS ON !!!")
#                 pHBaseOnFlag = True
#
#         if pHBaseOnFlag == True:
#             if (time.time() - pHBaseOnTime >= pHPumpDuration):
#                 actuation.write((base_motor + OFF).encode())
#                 print("!!! BASE PUMP IS OFF !!!")
#                 previousPHCheckTime = time.time()
#                 pHCheck = False
#                 pHBaseOnFlag = False


#     EC = 500
# #EC Control Unit
#     if ECCheck == False:
#         if(time.time() - previousECCheckTime >= ECCheckInterval):
#             ECCheck = True
#
#     if ECCheck == True:
#         #if EC is too low add both Nutrient A and B
#         if EC < 800:
#
#             if ECAOnFlag == False:
#                 ECAOnTime = time.time()
#                 ECBOnTime = time.time()
#                 actuation.write((nutrient_a_motor + ON).encode())
#                 actuation.write((nutrient_b_motor + ON).encode())
#                 print("!!! NUTRIENT A PUMP IS ON !!!")
#                 print("!!! NUTRIENT B PUMP IS ON !!!")
#                 ECAOnFlag = True
#                 ECBOnFlag = True
#
#         if ECAOnFlag == True :
#             if(time.time() - ECBOnTime >= ECBPumpDuration) and ECBOnFlag == True:
#                 actuation.write((nutrient_b_motor + OFF).encode())
#                 print("!!! NUTRIENT B PUMP IS OFF !!!")
#                 ECBOnFlag = False
#             if(time.time() - ECAOnTime >= ECAPumpDuration):
#                 actuation.write((nutrient_a_motor + OFF).encode())
#                 print("!!! NUTRIENT A PUMP IS OFF !!!")
#                 previousECCheckTime = time.time()
#                 ECCheck = False
#                 ECAOnFlag = False


# # Day-Night Control Unit (Grow Light Control Unit)
#     if LightSwitchDay == False:
#         if (time.time() - LightSwitchOffTime >= LightSwitchOffDuration):
#             actuation.write((light_switch + ON).encode())
#             print("!!! LIGHTS ARE ON. GOOD MORNING !!!")
#             LightSwitchOnTime = time.time()
#             LightSwitchDay = True
#
#     if LightSwitchDay == True:
#         if (time.time() - LightSwitchOnTime >= LighSwitchOnDuration):
#             actuation.write((light_switch + OFF).encode())
#             print("!!! LIGHTS ARE OFF. GOOD NIGHT !!!")
#             LightSwitchOffTime = time.time()
#             LightSwitchDay = False

# # Water Cooler Control Unit
#     if water_temperature > 22:
#         actuation.write((water_temperature_motor + ON).encode())
#     if water_temperature <= 22:
#         actuation.write((water_temperature_motor + OFF).encode())
#

# # Air Cooler Control Unit
#     if air_temperature > 22:
#         actuation.write((air_temperature_motor + ON).encode())
#     if air_temperature <= 22:
#         actuation.write((air_temperature_motor + OFF).encode())