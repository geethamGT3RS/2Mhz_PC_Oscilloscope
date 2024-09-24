import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
import serial
import time

class MultimeterGUI(QWidget):
    def __init__(self):
        super().__init__()
        
        # Serial setup (replace COM port as per your system)
        self.ser = serial.Serial('COM3', 115200, timeout=1)
        time.sleep(2)  # Wait for ESP32 to initialize

        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('ESP32 Multimeter')

        # Create buttons and label
        self.voltage_button = QPushButton('Measure Voltage (V)', self)
        self.current_button = QPushButton('Measure Current (I)', self)
        self.resistance_button = QPushButton('Measure Resistance (R)', self)
        self.result_label = QLabel('Result: ', self)

        # Connect buttons to their functions
        self.voltage_button.clicked.connect(self.measure_voltage)
        self.current_button.clicked.connect(self.measure_current)
        self.resistance_button.clicked.connect(self.measure_resistance)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.voltage_button)
        vbox.addWidget(self.current_button)
        vbox.addWidget(self.resistance_button)
        vbox.addWidget(self.result_label)
        
        self.setLayout(vbox)

    def send_command(self, cmd):
        self.ser.write(cmd.encode())  # Send command to ESP32
        time.sleep(1)  # Wait for data from ESP32
        result = self.ser.readline().decode().strip()  # Read result from ESP32
        return result

    def measure_voltage(self):
        result = self.send_command('V')
        self.result_label.setText(f'Result: Voltage = {result} V')

    def measure_current(self):
        result = self.send_command('I')
        self.result_label.setText(f'Result: Current = {result} A')

    def measure_resistance(self):
        result = self.send_command('R')
        self.result_label.setText(f'Result: Resistance = {result} Ohms')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MultimeterGUI()
    ex.show()
    sys.exit(app.exec_())
