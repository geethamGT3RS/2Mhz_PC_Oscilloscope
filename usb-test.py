import serial
import time

SERIAL_PORT = 'COM10'
BAUD_RATE = 230400
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as e:
    print(f"Error: {e}")
    exit(1)
time.sleep(2)

try:
    while True:
        if ser.in_waiting > 0:
            # Read available bytes
            raw_data = ser.read(ser.in_waiting)
            
            # Print raw data in hexadecimal format
            hex_data = raw_data.hex()
            print(f"Raw Data (Hex): {hex_data}")
            
            # Optionally, you can also print the data as integers
            int_data = list(raw_data)
            print(f"Raw Data (Int): {int_data}")
            
            # Decode the data assuming it's UTF-8 (if it's textual)
            line = raw_data.decode('utf-8', errors='ignore').rstrip()
            print(f"Decoded Line: {line}")
            
except KeyboardInterrupt:
    print("Program terminated.")
finally:
    ser.close()
    print("Serial connection closed.")
