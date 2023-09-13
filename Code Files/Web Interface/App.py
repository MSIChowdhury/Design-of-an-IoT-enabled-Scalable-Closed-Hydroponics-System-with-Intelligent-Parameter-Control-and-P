from flask import Flask, render_template, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Authenticate with Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('automated-hydroponics-data-40ded0143ddf.json', scope)
client = gspread.authorize(creds)

# Replace 'your-spreadsheet-id' with the actual ID of your Google Sheet
sheet = client.open_by_key('1tNPUnAiREPqyRNLcT3wuB3RoOHPEF8JCjK0DRQ6Jm64').sheet1

@app.route('/')
def index():
    data = sheet.get_all_records()
    return render_template('index.html', data=data)

@app.route('/update')
def update_data():
    data = sheet.get_all_records()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
