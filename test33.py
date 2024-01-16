import serial
import time
from serial.tools import list_ports
import datetime
import thingspeak
import math


# See the available ports to use in Serial Communication address
ports = list_ports.comports()
for port in ports:
    print("Port: ")
    print(port)
    print()

# Serial Communication , Adress Must be changed in Raspberry Pi
sensing = serial.Serial('COM13', 9600, timeout=20)  # /dev/ttyUSB1

sensing.setDTR(False)
time.sleep(1)
sensing.flushInput()
sensing.setDTR(True)

while True:

    for _ in range(5):


        s_bytes = sensing.readline()
        decoded_bytes = s_bytes.decode('utf-8').strip("\n\r")
        print(decoded_bytes)
        sensing.flushInput()
        time.sleep(0.1)


    print("Printing End")
    time.sleep(5)
    print("Will close now")
    sensing.close()
    time.sleep(5)
    print("Will restart now")
    sensing = serial.Serial('COM13', 9600, timeout=20)  # /dev/ttyUSB1

    sensing.setDTR(False)
    time.sleep(1)
    sensing.flushInput()
    sensing.setDTR(True)

    # while True:
    #     print("Stuck")
