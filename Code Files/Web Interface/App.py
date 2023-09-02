import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('automated-hydroponics-data-40ded0143ddf.json', scope)
gc = gspread.authorize(credentials)

# Replace 'Your Spreadsheet Name' with your Google Sheets spreadsheet name
spreadsheet = gc.open('Test')

@app.route('/')
def index():
    return render_template('index.html', data=read_data())

@socketio.on('connect')
def handle_connect():
    emit('update_data', read_data())

def read_data():
    try:
        # Replace 'Sheet1' with the name of your sheet in the spreadsheet
        worksheet = spreadsheet.worksheet('Sheet1')
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        print(f"Error reading data from Google Sheets: {str(e)}")
        return []

if __name__ == '__main__':
    while True:
        # Check for updates every 10 seconds (adjust as needed)
        data = read_data()
        socketio.emit('update_data', data)
        time.sleep(10)
