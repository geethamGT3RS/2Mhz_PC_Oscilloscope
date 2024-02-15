import socket
import struct
import numpy as np
import time

server_host = '0.0.0.0'
server_port = 8080
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_host, server_port))
server_socket.listen(1)

print("Waiting for TCP connection...")
client_socket, client_address = server_socket.accept()
print("Connected to:", client_address)

# Adjust the packet size to achieve the desired transfer rate
packet_size = 1024 * 1024  # 1 MB packet size
num_samples_per_packet = packet_size // struct.calcsize('e')
sine_wave_values = 3 * np.sin(np.linspace(0, 2*np.pi, num_samples_per_packet))
data_size_bytes = 10000000
num_samples = data_size_bytes // 2
#try:
bytes_sent = 0
start_time = time.time() 
while True:
    sine_wave_values = (1 * np.sin(np.linspace(0, 2 * np.pi*100, num_samples))).astype(np.float16)
    #sine_wave_values = (1).astype(np.float16)
    sine_wave_bytes = sine_wave_values.tobytes()
    client_socket.sendall(sine_wave_bytes)
    bytes_sent += len(sine_wave_bytes)

    
    elapsed_time = time.time() - start_time
    if elapsed_time >= 1:
        print("Bytes sent in 1 second:", bytes_sent)
        bytes_sent = 0
        start_time = time.time()

#finally:
    #client_socket.close()
    #server_socket.close()
