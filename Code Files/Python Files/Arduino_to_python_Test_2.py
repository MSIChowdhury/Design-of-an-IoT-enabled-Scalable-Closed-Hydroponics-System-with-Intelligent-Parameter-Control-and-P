from serial.tools import list_ports
import serial
import time
import gspread
import serial
import time
from serial.tools import list_ports
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import thingspeak



channel_id = '2271152'
write_key = 'JO2OUEE6JT9J6OIV'


# Set your credentials JSON file path and Google Sheet name
CREDENTIALS_FILE = 'automated-hydroponics-data-40ded0143ddf.json'
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
    


serialCom = serial.Serial("/dev/ttyACM0",9600)


serialCom.setDTR(False)
time.sleep(1)
serialCom.flushInput()
serialCom.setDTR(True)

received_data = []

while(1):
    try:
        #Read a line of data
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        s_bytes = serialCom.readline()
        decoded_bytes = s_bytes.decode("utf-8").strip("\n\r")

        lines = decoded_bytes.split(',')

        #Timestamp = float(lines[0])/1000
        EC = float(lines[0])
        pH = float(lines[1])
        Humidity = float(lines[2])
        Air_temperature = float(lines[3])
        Water_temperature = float(lines[4])
        Distance = float(lines[5])
        print("Current time:", current_time)
        send_time = str(current_time)
        data_to_send = [send_time, EC, pH, Humidity, Air_temperature, Water_temperature, Distance]  # Send EC to the Google Sheet
        worksheet.append_row(data_to_send)
        channel = thingspeak.Channel(id=channel_id, api_key=write_key)
        response = channel.update({'field1': EC, 'field2': pH, 'field3': Humidity, 'field4': Air_temperature, 'field5': Water_temperature, 'field6': Distance,})
        

    except:
        print("ERROR! There was an error in the code!")



