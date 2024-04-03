import socket
import numpy as np
import struct
import matplotlib.pyplot as plt

# Create a TCP socket
server_host = '169.254.116.191'  # Update with the server's IP address
server_port = 8080
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_host, server_port))

received_data = b''
try:
    while True:
        # Receive data packet of 800 bytes
        chunk = client_socket.recv(800)
        if not chunk:
            break
        received_data += chunk

        # Plot the received data every time a packet is received
        if len(received_data) >= 800:
            # Unpack the received data into a NumPy array
            received_values = struct.unpack('f' * (len(received_data) // 4), received_data)
            plt.plot(received_values)
            plt.show()
            received_data = b''  # Reset received data buffer

finally:
    client_socket.close()
