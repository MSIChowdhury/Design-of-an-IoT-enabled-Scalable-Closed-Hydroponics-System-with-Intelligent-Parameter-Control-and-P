import subprocess
import cv2
from flask import Flask, request, render_template, jsonify, Response
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
    
def generate_frames():
    camera = cv2.VideoCapture(0)  # 0 indicates the default camera (your USB webcam)

    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
