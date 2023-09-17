from serial.tools import list_ports
import serial
import time


ports = list_ports.comports()
for port in ports:
    print(port)

print()
serialCom = serial.Serial("COM7",9600)


serialCom.setDTR(False)
time.sleep(1)
serialCom.flushInput()
serialCom.setDTR(True)

received_data = []

def printSensor():
    print("pH: ", pH)
    print("EC: ", EC, " microSiemens/m")
    print("Water Temperature: ", Water_temperature, " Celsius")
    print("Air Temperature: ", Air_temperature, " Celsius")
    print("Humidity: ", Humidity, "%")
    print()

while(1):
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
        printSensor()
    except:
        print("ERROR! There was an error in the code!")