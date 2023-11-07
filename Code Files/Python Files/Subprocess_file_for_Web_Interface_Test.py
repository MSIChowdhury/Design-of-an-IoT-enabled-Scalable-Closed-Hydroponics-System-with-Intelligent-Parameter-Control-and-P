import subprocess
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)
CORS(app)  # Add this line to enable CORS for your app

# Define the currently running script (for demonstration purposes)
current_script = "None"

# Route to display the web interface
@app.route('/')
def index():
    return render_template('index.html')

# Route to run selected Python script
@app.route('/run_script', methods=['POST'])
def run_script():
    script_name = request.form['script_name']

    if script_name == 'Lettuce':
        script_path = 'Lettuce.py'
    elif script_name == 'Option 2':
        script_path = 'Option 2.py'
    elif script_name == 'Option 3':
        script_path = 'Option 3.py'
    else:
        return "Invalid script name"

    # Execute the selected Python script
    try:
        subprocess.run(['python3', script_path], check=True)
        # After running the script, redirect to the index page
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        return f"Script execution failed: {e}"
        
@app.route('/current_script', methods=['GET'])
def get_current_script():
    global current_script
    return jsonify({"scriptName": current_script})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
