import serial
import serial.tools.list_ports

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
available_ports = list_serial_ports()
if not available_ports:
    print("No serial ports found.")
    exit()

print("Available ports:")
for i, port in enumerate(available_ports):
    print(f"{i + 1}: {port}")

port_index = int(input("Select the COM port number: ")) - 1
selected_port = available_ports[port_index]
baud_rate = 115200
try:
    ser = serial.Serial(selected_port, baud_rate, timeout=1)
    print(f"Connected to {selected_port} at {baud_rate} baud.")
except serial.SerialException as e:
    print(f"Could not open serial port {selected_port}: {e}")
    exit()

# Read data continuously
try:
    while True:
        if ser.in_waiting > 0:
            # Read a line from the serial port
            line = ser.readline().decode('utf-8').rstrip()
            print(f"Received: {line}")
except KeyboardInterrupt:
    print("Exiting program")
finally:
    # Close the serial port
    ser.close()
    print("Serial port closed.")
