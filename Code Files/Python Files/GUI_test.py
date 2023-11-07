from flask import Flask, request
import time
import threading

app = Flask(__name__)
stop_flag = False
stop_flag_lock = threading.Lock()

def counter():
    num = 0
    while True:
        with stop_flag_lock:
            if stop_flag:
                print("STOPPED")
                break
        print(num)
        num += 1
        time.sleep(1)

# Start the counter in a separate thread
counter_thread = threading.Thread(target=counter)
counter_thread.start()

# Replace 'your_ddns_hostname' with your Dynu DDNS hostname
hostname = '0.0.0.0'
port = 5000  # Use the port you configured in your code

@app.route('/send_command', methods=['POST'])
def send_command():
    global stop_flag
    command = request.form['command']
    print(f'Received command: {command}')
    
    if command == "STOP":
        with stop_flag_lock:
            stop_flag = True  # Set the flag to stop the counter
    
    return 'Command received: ' + command

if __name__ == '__main__':
    app.run(host=hostname, port=port)




