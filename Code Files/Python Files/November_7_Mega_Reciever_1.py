import serial
import time
from serial.tools import list_ports
import datetime
import thingspeak
import math

#Actuators Pin Numbers
air_temperature_motor = "50"
CO2_relay = "38"

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
sensing = serial.Serial("COM10", 9600)   #/dev/ttyUSB1
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


def printSensor():
    """ This Function prints The sensor values """
    print("CO2: ", CO2, "PPM")
    print("Air Temperature: ", round(Air_temperature, 2), " Celsius")
    print("Humidity: ", Humidity, "%")
    print("Water Temperature: ", Water_temperature, " Celsius")
    print("Water Level: ", round(Water_level, 2), " cm")
    print()

while (1):
    try:
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
        Water_temperature = float(lines_sensing[0])
        Water_level = float(lines_sensing[1])

        printSensor()
    except:
        print("")

    # # Air Cooler Control Unit
    # if CO2 < 500:
    #     actuation.write((CO2_relay + ON).encode())
    #     print("!!! CO2 Relay IS ON !!!")
    # if CO2 > 500:
    #     actuation.write((CO2_relay + OFF).encode())
    #     print("!!! CO2 Relay IS OFF !!!")
    #
    # # Air Cooler Control Unit
    # if Air_temperature > 24:
    #     actuation.write((air_temperature_motor + ON).encode())
    #     print("!!! AIR COOLER IS ON !!!")
    # if Air_temperature <= 18:
    #     actuation.write((air_temperature_motor + OFF).encode())
    #     print("!!! AIR COOLER IS OFF !!!")