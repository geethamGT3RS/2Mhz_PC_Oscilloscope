import sys
import serial
import serial.tools.list_ports
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QHBoxLayout, QDial
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class USBOscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Oscilloscope")
        self.setGeometry(100, 100, 800, 600)

        # Create main layout
        main_layout = QHBoxLayout()

        # Left panel layout
        left_panel = QVBoxLayout()
        self.port_label = QLabel("Select USB Port:")
        left_panel.addWidget(self.port_label)

        self.port_combo = QComboBox()
        self.refresh_ports()
        left_panel.addWidget(self.port_combo)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_serial)
        self.connect_button.setStyleSheet("QPushButton { background-color: lightblue; font-size: 16px; padding: 5px; }")
        left_panel.addWidget(self.connect_button)

        self.status_label = QLabel("Status: Not connected")
        left_panel.addWidget(self.status_label)

        # Horizontal scale dial
        self.horizontal_scale_dial = QDial()
        self.horizontal_scale_dial.setRange(1, 100)  # Scale from 1x to 100x
        self.horizontal_scale_dial.setValue(10)  # Default scale
        self.horizontal_scale_dial.setNotchesVisible(True)
        left_panel.addWidget(QLabel("Horizontal Scale:"))
        left_panel.addWidget(self.horizontal_scale_dial)

        # Vertical scale dial
        self.vertical_scale_dial = QDial()
        self.vertical_scale_dial.setRange(1, 20)  # Scale from 1 to 20
        self.vertical_scale_dial.setValue(10)  # Default scale
        self.vertical_scale_dial.setNotchesVisible(True)
        left_panel.addWidget(QLabel("Vertical Scale:"))
        left_panel.addWidget(self.vertical_scale_dial)

        # Pause/Resume toggle button
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        self.pause_resume_button.setStyleSheet("QPushButton { background-color: lightgreen; font-size: 16px; padding: 5px; }")
        left_panel.addWidget(self.pause_resume_button)

        main_layout.addLayout(left_panel)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Real-Time Data")
        self.plot_curve = self.plot_widget.plot(pen='r')
        self.plot_widget.setYRange(-10, 10)
        self.plot_widget.setXRange(0, 10000)
        self.plot_widget.setLimits(xMin=0, xMax=10000, yMin=-10, yMax=10)
        main_layout.addWidget(self.plot_widget)

        self.central_widget = QWidget()
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

        self.serial_port = None
        self.data_buffer = np.zeros(10000)
        self.is_paused = False

        # Timers for plot updating and connection checking
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)

        self.connection_check_timer = QTimer()
        self.connection_check_timer.timeout.connect(self.check_serial_connection)

    def refresh_ports(self):
        """Refresh the list of available serial ports."""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def connect_serial(self):
        """Connect to the selected serial port."""
        selected_port = self.port_combo.currentText()
        if selected_port:
            try:
                self.serial_port = serial.Serial(selected_port, baudrate=1000000, timeout=0.1)
                self.status_label.setText(f"Status: Connected to {selected_port}")
                self.data_buffer = np.zeros(10000)  # Reset the data buffer
                self.plot_timer.start(5)  # Update the plot every 5 ms
            except Exception as e:
                self.status_label.setText(f"Failed to open serial port: {e}")

    def update_plot(self):
        """Update the plot with new data from the serial port."""
        if self.serial_port is not None and not self.is_paused and self.serial_port.in_waiting > 0:
            try:
                # Read 2000 bytes from the serial port (1000 samples for uint16 data)
                data = self.serial_port.read(2000)
                data_array = np.frombuffer(data, dtype=np.uint16)
                data_array = data_array.astype(np.float32) * 3.3 / 4096  # Scale to voltage

                # Update the rolling data buffer
                self.data_buffer = np.roll(self.data_buffer, -len(data_array))
                self.data_buffer[-len(data_array):] = data_array

                # Apply horizontal and vertical scaling
                horizontal_scale = self.horizontal_scale_dial.value()
                vertical_scale = self.vertical_scale_dial.value()
                num_samples_to_display = int(len(self.data_buffer) / horizontal_scale)
                scaled_data = self.data_buffer[-num_samples_to_display:] * vertical_scale

                # Update the X-axis range and plot the data
                self.plot_widget.setXRange(0, num_samples_to_display)
                self.plot_curve.setData(scaled_data)

            except Exception as e:
                print(f"Error reading from serial port: {e}")

    def toggle_pause_resume(self):
        """Toggle between pausing and resuming the plot."""
        if self.is_paused:
            self.is_paused = False
            self.data_buffer = np.zeros(10000)  # Clear the buffer when resuming
            self.pause_resume_button.setText("Pause")
            self.pause_resume_button.setStyleSheet("QPushButton { background-color: lightgreen; font-size: 16px; padding: 5px; }")
        else:
            self.is_paused = True
            self.pause_resume_button.setText("Resume")
            self.pause_resume_button.setStyleSheet("QPushButton { background-color: lightcoral; font-size: 16px; padding: 5px; }")

    def check_serial_connection(self):
        """Check if the serial connection is still active and refresh the ports list."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        selected_port = self.port_combo.currentText()

        if self.serial_port is not None and selected_port not in ports:
            # Handle serial port disconnection
            self.status_label.setText(f"Status: {selected_port} disconnected")
            self.serial_port.close()
            self.serial_port = None
            self.plot_timer.stop()

        # Refresh the available ports
        self.refresh_ports()

    def closeEvent(self, event):
        """Handle the window close event by closing the serial port."""
        if self.serial_port is not None:
            self.serial_port.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    oscilloscope = USBOscilloscope()
    oscilloscope.show()
    sys.exit(app.exec_())
