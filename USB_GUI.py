import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QDial, QLabel, QPushButton
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
import numpy as np
import serial
import serial.tools.list_ports

class WorkerSignals(QObject):
    plot_data = pyqtSignal(np.ndarray)

class DataReceiver(QRunnable):
    def __init__(self, serial_port, baud_rate, expected_points, trigger_value, average_method):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.expected_points = expected_points
        self.trigger_value = trigger_value
        self.average_method = average_method
        self.signals = WorkerSignals()
        self.received_data = []
        self.data_buffer = []
        self.running = True

    def run(self):
        ser = None
        try:
            ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            ser.flushInput()
            ser.flushOutput()
            print(f"Connected to {self.serial_port} at {self.baud_rate} baud.")
            
            while self.running:
                try:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        if line:  # Ensure line is not empty
                            try:
                                value = int(line)
                                voltage = value * (5.0 / 1023)
                                self.received_data.append(voltage)

                                if len(self.received_data) >= self.expected_points:
                                    # Trigger logic: only emit if the signal crosses the trigger value
                                    if any(v >= self.trigger_value for v in self.received_data):
                                        self.data_buffer.append(self.received_data[:self.expected_points])
                                        if len(self.data_buffer) > 10:  # Buffer size, adjust as needed
                                            self.data_buffer.pop(0)  # Remove oldest set of data

                                        # Compute the average based on the selected method
                                        if self.average_method == 'No Average':
                                            averaged_data = np.array(self.data_buffer[-1])
                                        elif self.average_method == 'Simple Average':
                                            averaged_data = np.mean(self.data_buffer, axis=0)
                                        elif self.average_method == 'Weighted Average':
                                            weights = np.linspace(1, 0, len(self.data_buffer))  # Simple decreasing weights
                                            weighted_sum = np.average(self.data_buffer, axis=0, weights=weights)
                                            averaged_data = weighted_sum
                                        else:
                                            averaged_data = np.array(self.data_buffer[-1])
                                            
                                        self.signals.plot_data.emit(averaged_data)
                                        
                                    self.received_data = self.received_data[self.expected_points:]
                            except ValueError:
                                print(f"Invalid data received: {line}")
                except UnicodeDecodeError as e:
                    print(f"Decoding error: {e}. Retrying...")
                    ser.flushInput()  # Clear the input buffer on decoding error
                    continue
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        finally:
            if ser is not None and ser.is_open:
                ser.close()
                print("Serial port closed.")

    def stop(self):
        self.running = False


from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout

class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()

        # Find available serial ports
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("No serial ports found.")
            sys.exit()

        self.baud_rate = 115200  # Must match the Arduino's baud rate
        self.expected_points = 200
        self.average_method = 'No Average'  # Default averaging method

        self.setWindowTitle("Oscilloscope")
        self.setGeometry(0, 0, 1920, 1080)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)

        # Plot widget
        self.plot_widget = pg.PlotWidget(self.central_widget)
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Oscilloscope", color='w', size='16pt')
        self.series_channel1 = self.plot_widget.plot(pen='r', name="Channel 1")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(y=False)
        self.plot_widget.setYRange(0, 5)

        # Add a dotted line for the trigger value
        self.trigger_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', style=pg.QtCore.Qt.DotLine))
        self.plot_widget.addItem(self.trigger_line)

        main_layout.addWidget(self.plot_widget)

        # Right-side layout for controls
        control_layout = QVBoxLayout()

        # Add dropdown to select USB port
        self.combo_box = QComboBox(self.central_widget)
        for port in ports:
            self.combo_box.addItem(port.device)
        self.combo_box.currentIndexChanged.connect(self.port_selected)
        self.combo_box.setStyleSheet("QComboBox { font-size: 14px; }")
        control_layout.addWidget(self.combo_box)

        # Trigger dial label
        self.label_trigger = QLabel("Trigger Value:", self.central_widget)
        self.label_trigger.setFont(QFont("Arial", 12))
        control_layout.addWidget(self.label_trigger)

        # QDial for trigger control
        self.trigger_dial = QDial(self.central_widget)
        self.trigger_dial.setMinimum(0)
        self.trigger_dial.setMaximum(50)
        self.trigger_dial.setSingleStep(1)
        self.trigger_dial.setValue(25)  # Default to middle value
        self.trigger_dial.setNotchesVisible(True)
        self.trigger_dial.setStyleSheet("""
            QDial {
                border: 1px solid #ddd;
                border-radius: 10px;
                background: #555;
                width: 150px;
                height: 150px;
            }
            QDial::handle {
                border: 1px solid #aaa;
                background: #f0f0f0;
                width: 15px;
                height: 15px;
                border-radius: 7px;
            }
        """)
        self.trigger_dial.setWrapping(True)
        self.trigger_value = self.trigger_dial.value() / 10  # Scale to 0.0 - 5.0
        self.trigger_dial.valueChanged.connect(self.update_trigger_value)
        control_layout.addWidget(self.trigger_dial)

        # Horizontal scaling dial
        self.label_scale = QLabel("Horizontal Scale:", self.central_widget)
        self.label_scale.setFont(QFont("Arial", 12))
        control_layout.addWidget(self.label_scale)

        self.scale_dial = QDial(self.central_widget)
        self.scale_dial.setMinimum(1)
        self.scale_dial.setMaximum(self.expected_points)
        self.scale_dial.setValue(10)  # Default to a reasonable scale
        self.scale_dial.setSingleStep(1)
        self.scale_dial.setNotchesVisible(True)
        self.scale_dial.setStyleSheet("""
            QDial {
                border: 1px solid #ddd;
                border-radius: 10px;
                background: #555;
                width: 150px;
                height: 150px;
            }
            QDial::handle {
                border: 1px solid #aaa;
                background: #f0f0f0;
                width: 15px;
                height: 15px;
                border-radius: 7px;
            }
        """)
        self.scale_dial.valueChanged.connect(self.update_scale)
        control_layout.addWidget(self.scale_dial)

        # Averaging method dropdown
        self.label_avg_method = QLabel("Averaging Method:", self.central_widget)
        self.label_avg_method.setFont(QFont("Arial", 12))
        control_layout.addWidget(self.label_avg_method)

        self.avg_method_dropdown = QComboBox(self.central_widget)
        self.avg_method_dropdown.addItem("No Average")
        self.avg_method_dropdown.addItem("Simple Average")
        self.avg_method_dropdown.addItem("Weighted Average")
        self.avg_method_dropdown.setStyleSheet("QComboBox { font-size: 14px; }")
        self.avg_method_dropdown.currentIndexChanged.connect(self.update_avg_method)
        control_layout.addWidget(self.avg_method_dropdown)

        # Start button
        self.start_button = QPushButton("Start", self.central_widget)
        self.start_button.setFont(QFont("Arial", 12))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(self.start_worker)
        control_layout.addWidget(self.start_button)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)



        # Start with the first available port
        self.serial_port = self.combo_box.currentText()
        self.worker = None

    def port_selected(self):
        self.serial_port = self.combo_box.currentText()

    def update_avg_method(self, index):
        self.average_method = self.avg_method_dropdown.currentText()
        if self.worker is not None:
            self.worker.stop()
            self.start_worker()

    def start_worker(self):
        if self.worker is not None:
            self.worker.stop()

        self.worker = DataReceiver(self.serial_port, self.baud_rate, self.expected_points, self.trigger_value, self.average_method)
        self.worker.signals.plot_data.connect(self.update_plot)
        QThreadPool.globalInstance().start(self.worker)

    def update_plot(self, data):
        self.series_channel1.setData(data)

    def update_trigger_value(self, value):
        self.trigger_value = value / 10  # Update the trigger value based on dial position
        self.trigger_line.setPos(self.trigger_value)
        print(f"Trigger value set to: {self.trigger_value}")

    def update_scale(self, value):
        # Adjust the x-axis range based on the dial value
        scale_factor = value / 10.0  # Adjust scaling factor to your needs
        self.plot_widget.setXRange(0, scale_factor)
        print(f"Horizontal scale set to: {scale_factor}")

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    oscilloscope = Oscilloscope()
    oscilloscope.show()
    sys.exit(app.exec_())
