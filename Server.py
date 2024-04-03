import socket
import os
import struct

# Define the named pipe (FIFO) path
pipe_name = '/tmp/adc_data_pipe'

# Create a TCP socket
server_host = '0.0.0.0'
server_port = 8081
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_host, server_port))
server_socket.listen(1)

print("Waiting for TCP connection...")
client_socket, client_address = server_socket.accept()
print("Connected to:", client_address)

# Open the named pipe for reading
pipe_fd = os.open(pipe_name, os.O_RDONLY)

try:
    data_buffer = b''  # Buffer to store the received data

    while True:
        # Read the voltage from the pipe
        voltage_bytes = os.read(pipe_fd, 4000)
        data_buffer += voltage_bytes  # Append the received data to the buffer
        if len(data_buffer) >= 4000:  # Check if the buffer size exceeds 40000 bytes
            client_socket.sendall(data_buffer)  # Send the data over the socket
            data_buffer = b''  # Reset the buffer
        
finally:
    os.close(pipe_fd)

