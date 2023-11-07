import serial

arduinoData = serial.Serial("COM9", 9600)

while True:
    command = input("Enter command: ")
    command = command + '\r'
    arduinoData.write(command.encode())

