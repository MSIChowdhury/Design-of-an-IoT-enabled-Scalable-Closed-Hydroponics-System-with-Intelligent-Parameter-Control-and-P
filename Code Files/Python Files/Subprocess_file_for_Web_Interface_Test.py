import subprocess

@app.route('/run_script/<script_name>', methods=['POST'])
def run_script(script_name):
    if script_name == 'Lettuce':
        # Execute the Lettuce script
        subprocess.run(['python3', '/path/to/Lettuce.py'])
    elif script_name == 'Option 2':
        # Execute the Option 2 script
        subprocess.run(['python3', '/path/to/Option2.py'])
    elif script_name == 'Option 3':
        # Execute the Option 3 script
        subprocess.run(['python3', '/path/to/Option3.py'])
    else:
        return "Invalid script name"

    return "Script executed successfully"

if __name__ == '__main__':
    app.run()
