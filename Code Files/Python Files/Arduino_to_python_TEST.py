from serial.tools import list_ports
import serial
import time


ports = list_ports.comports()
for port in ports:
    print("Port: ")
    print(port)
    


serialCom = serial.Serial("/dev/ttyACM0",9600)


serialCom.setDTR(False)
time.sleep(1)
serialCom.flushInput()
serialCom.setDTR(True)

received_data = []

while(1):
    try:
        #Read a line of data
        s_bytes = serialCom.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")

        lines = decoded_bytes.split(',')

        Timestamp = float(lines[0])/1000
        EC = float(lines[1])
        pH = float(lines[2])
        Humidity = float(lines[3])
        Air_temperature = float(lines[4])
        Water_temperature = float(lines[5])
        Distance = float(lines[6])
        Timestamp_python = float(time.time())
        print(Timestamp_python)
        

    except:
        print("ERROR! There was an error in the code!")
