import socket

def is_port_available(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # Adjust the timeout as needed
            s.bind((host, port))
        return True
    except (OSError, ConnectionError):
        return False

# Example usage:
hostname = '192.168.1.4'  # Replace with your hostname or IP
port = 6000  # Replace with the port you want to check

if is_port_available(hostname, port):
    print(f"The address {hostname}:{port} is available for binding.")
else:
    print(f"The address {hostname}:{port} is not available for binding.")
