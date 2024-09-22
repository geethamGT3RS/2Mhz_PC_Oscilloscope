import sys
import serial
import serial.tools.list_ports
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QHBoxLayout, QDial, QToolTip
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

class USBOscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Oscilloscope")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")  # Dark theme for the window

        # Set a unified style for the tooltips
        QToolTip.setFont(QFont('SansSerif', 10))

        main_layout = QHBoxLayout()

        # Left panel with controls
        left_panel = QVBoxLayout()
        self.port_label = QLabel("Select USB Port:")
        self.port_label.setFont(QFont('Arial', 12))
        self.port_label.setStyleSheet("padding: 5px;")
        left_panel.addWidget(self.port_label)

        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        self.refresh_ports()
        left_panel.addWidget(self.port_combo)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_serial)
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-size: 16px; 
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_panel.addWidget(self.connect_button)

        self.status_label = QLabel("Status: Not connected")
        self.status_label.setFont(QFont('Arial', 12))
        left_panel.addWidget(self.status_label)

        # Horizontal scale dial
        self.horizontal_scale_dial = QDial()
        self.horizontal_scale_dial.setRange(1, 500)
        self.horizontal_scale_dial.setValue(10)
        self.horizontal_scale_dial.setNotchesVisible(True)
        self.horizontal_scale_dial.setStyleSheet("background-color: #3d3d3d; color: white;")
        left_panel.addWidget(QLabel("Horizontal Scale:"))
        left_panel.addWidget(self.horizontal_scale_dial)

        # Vertical scale dial
        self.vertical_scale_dial = QDial()
        self.vertical_scale_dial.setRange(1, 500)
        self.vertical_scale_dial.setValue(10)
        self.vertical_scale_dial.setNotchesVisible(True)
        self.vertical_scale_dial.setStyleSheet("background-color: #3d3d3d; color: white;")
        left_panel.addWidget(QLabel("Vertical Scale:"))
        left_panel.addWidget(self.vertical_scale_dial)

        # Trigger level control
        self.trigger_level_dial = QDial()
        self.trigger_level_dial.setRange(0, 500)  # 0-3.3V in 0.01V steps
        self.trigger_level_dial.setValue(165)  # Default trigger level is 1.65V
        self.trigger_level_dial.setNotchesVisible(True)
        self.trigger_level_dial.setStyleSheet("background-color: #3d3d3d; color: white;")
        left_panel.addWidget(QLabel("Trigger Level (V*100):"))
        left_panel.addWidget(self.trigger_level_dial)

        # Trigger mode ComboBox
        self.trigger_mode_combo = QComboBox()
        self.trigger_mode_combo.addItem("Rising")
        self.trigger_mode_combo.addItem("Falling")
        self.trigger_mode_combo.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        left_panel.addWidget(QLabel("Trigger Mode:"))
        left_panel.addWidget(self.trigger_mode_combo)

        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        self.pause_resume_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800; 
                color: white; 
                font-size: 16px; 
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        left_panel.addWidget(self.pause_resume_button)

        main_layout.addLayout(left_panel)
        # Right panel with the plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Real-Time Data")
        self.plot_widget.setLabel('left', 'Voltage', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='ms')
        self.plot_curve = self.plot_widget.plot(pen='r')

        # Set Y and X ranges for the plot
        self.plot_widget.setYRange(-3.5, 3.5)  # Updated for 3.3V signal
        self.plot_widget.setXRange(0, 1000)  # Adjust for frequency range
        self.plot_widget.setLimits(xMin=0, xMax=1000, yMin=-3.5, yMax=3.5)
        main_layout.addWidget(self.plot_widget)

        # Enable mouse interaction for displaying tooltips
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)

        # Set central widget
        self.central_widget = QWidget()
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

        self.serial_port = None
        self.data_buffer = np.zeros(1000)  # Buffer size for data
        self.is_paused = False
        self.triggered = False

        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)

        self.connection_check_timer = QTimer()
        self.connection_check_timer.timeout.connect(self.check_serial_connection)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def connect_serial(self):
        selected_port = self.port_combo.currentText()
        if selected_port:
            try:
                self.serial_port = serial.Serial(selected_port, baudrate=2000000, timeout=0.1)
                self.status_label.setText(f"Status: Connected to {selected_port}")
                self.data_buffer = np.zeros(1000)
                self.plot_timer.start(5)
            except Exception as e:
                self.status_label.setText(f"Failed to open serial port: {e}")

    def update_plot(self):
        if self.serial_port is not None and not self.is_paused and self.serial_port.in_waiting > 0:
            try:
                # Read bytes from the serial port
                data = self.serial_port.read(200)  # Read in chunks to fit frequency
                data_array = np.frombuffer(data, dtype=np.uint8)  # Convert to uint8
                data_array = data_array.astype(np.float32) * 3.3 / 255  # Scale to 0-3.3V

                # Implement Triggering
                trigger_level = self.trigger_level_dial.value() / 100.0  # Convert to voltage
                trigger_mode = self.trigger_mode_combo.currentText()

                if not hasattr(self, 'triggered'):
                    self.triggered = False

                # Trigger Logic
                if not self.triggered:
                    for i in range(1, len(data_array)):
                        if (trigger_mode == "Rising" and data_array[i-1] < trigger_level <= data_array[i]) or \
                           (trigger_mode == "Falling" and data_array[i-1] > trigger_level >= data_array[i]):
                            self.triggered = True
                            break

                if self.triggered:
                    # Update data buffer with new data
                    self.data_buffer = np.roll(self.data_buffer, -len(data_array))
                    self.data_buffer[-len(data_array):] = data_array[:]

                    vertical_scale = self.vertical_scale_dial.value()
                    scaled_data = self.data_buffer * vertical_scale

                    horizontal_scale = self.horizontal_scale_dial.value()
                    self.plot_widget.setXRange(0, 1000 / horizontal_scale)  # Adjust X range
                    self.plot_curve.setData(scaled_data)

            except Exception as e:
                print(f"Error reading from serial port: {e}")

    def toggle_pause_resume(self):
        if self.is_paused:
            self.is_paused = False
            self.triggered = False  # Reset the trigger when resuming
            self.data_buffer = np.zeros(1000)  # Reset the data buffer
            self.pause_resume_button.setText("Pause")
            self.pause_resume_button.setStyleSheet("QPushButton { background-color: lightgreen; font-size: 16px; padding: 5px; }")
        else:
            self.is_paused = True
            self.pause_resume_button.setText("Resume")
            self.pause_resume_button.setStyleSheet("QPushButton { background-color: lightcoral; font-size: 16px; padding: 5px; }")

    def check_serial_connection(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        selected_port = self.port_combo.currentText()
        if self.serial_port is not None and selected_port not in ports:
            self.status_label.setText(f"Status: {selected_port} disconnected")
            self.serial_port.close()
            self.serial_port = None
            self.plot_timer.stop()
        self.refresh_ports()

    def on_mouse_moved(self, evt):
        pos = evt
        vb = self.plot_widget.plotItem.vb
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()
            # Show tooltip with x and y values
            QToolTip.showText(self.mapToGlobal(self.cursor().pos()), f"x: {x_val:.2f}, y: {y_val:.2f}")

    def closeEvent(self, event):
        if self.serial_port is not None:
            self.serial_port.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    oscilloscope = USBOscilloscope()
    oscilloscope.show()
    sys.exit(app.exec_())
