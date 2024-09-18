import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QDial, QLabel, QMessageBox
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QRunnable, QThreadPool
import socket
from PyQt5 import QtCore
from scipy import signal

class WorkerSignals(QObject):
    plot_data = pyqtSignal(np.ndarray)

class DataReceiver(QRunnable):
    def __init__(self, client_socket, expected_bytes):
        super().__init__()
        self.client_socket = client_socket
        self.expected_bytes = expected_bytes
        self.signals = WorkerSignals()
        self.received_data = []

    def run(self):
        while True:
            received_data = b''
            bytes_received = 0
            while bytes_received < self.expected_bytes:
                data = self.client_socket.recv(self.expected_bytes - bytes_received)
                if not data:
                    break
                received_data += data
                bytes_received += len(data)
            if bytes_received >= self.expected_bytes:
                received_data_array = np.frombuffer(received_data, dtype=np.uint16)
                voltage_data = received_data_array * (5.0 / 1023)
                print("Emitted")
                self.signals.plot_data.emit(voltage_data)
                self.received_data.extend(voltage_data)


class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        server_host = '169.254.37.152'
        server_port = 8081
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_host, server_port))
        self.expected_bytes = 2000 
        self.setWindowTitle("Oscilloscope")
        self.setGeometry(0, 0, 1920, 1080)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        
        
        # Layout for buttons and dial on the left side
        button_layout = QVBoxLayout()

        # Start button
        self.start_button = QPushButton("Start", self)
        button_layout.addWidget(self.start_button)

        # Add spacing
        button_layout.addSpacing(20)  

        # Stop button
        self.stop_button = QPushButton("Stop", self)
        button_layout.addWidget(self.stop_button)

        # Add spacing
        button_layout.addSpacing(20)  

        # Save button
        self.save_button = QPushButton("Save", self)
        button_layout.addWidget(self.save_button)

        # Add spacing
        button_layout.addSpacing(100)  

        # Trigger knob label
        self.label_trigger = QLabel("Trigger Value:", self)
        button_layout.addWidget(self.label_trigger)

        # Add spacing
        button_layout.addSpacing(10)  

        # QDial for trigger control
        self.trigger_dial = QDial()
        self.trigger_dial.setMinimum(-10)
        self.trigger_dial.setMaximum(10)
        self.trigger_dial.setSingleStep(2)
        self.trigger_dial.setValue(0)
        self.trigger_dial.setNotchesVisible(True)
        self.trigger_value = 0
        self.trigger_dial.valueChanged.connect(self.update_trigger_value)
        button_layout.addWidget(self.trigger_dial)

        # Add spacing
        button_layout.addSpacing(100)  

        # Horizontal scaling knob label
        self.label_scale = QLabel("Horizontal Scale:", self)
        button_layout.addWidget(self.label_scale)

        # Add spacing
        button_layout.addSpacing(10)  

        # QDial for scaling control
        self.scale_dial = QDial()
        self.scale_dial.setMinimum(1)
        self.scale_dial.setMaximum(10)
        self.scale_dial.setSingleStep(1)
        self.scale_dial.setValue(0)
        self.scale_dial.setNotchesVisible(True)
        self.scale_value = 1
        self.scale_dial.valueChanged.connect(self.scale)
        button_layout.addWidget(self.scale_dial)

        # Add final spacing
        button_layout.addStretch()  

        main_layout.addLayout(button_layout)


        button_styles = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 20px 40px;
                border: 5px solid #0F0F0F;
                border-radius: 10px;
                font-size: 24px;
                margin: 5px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }
        """

        self.start_button.setStyleSheet(button_styles)
        self.stop_button.setStyleSheet(button_styles)
        self.save_button.setStyleSheet(button_styles)

        # Plot widget
        self.plot_widget = pg.PlotWidget(self.central_widget)
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Oscilloscope")
        self.series_channel1 = self.plot_widget.plot(pen='r', name="Channel 1")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(-5, 5)
        main_layout.addWidget(self.plot_widget)

        self.zero_crossing_index = -1

        self.start_button.clicked.connect(self.start_plotting)
        self.stop_button.clicked.connect(self.stop_plotting)
        self.save_button.clicked.connect(self.save_plot)

        self.plot_data_timer = QTimer()
        self.plot_data_timer.timeout.connect(self.plot_data)
        self.plotting = False
        self.plot_widget.enterEvent = self.enter_plot
        self.plot_widget.leaveEvent = self.leave_plot
         # Enable mouse tracking for the plot widget
        self.plot_widget.setMouseTracking(True)

        # Connect the mouse press event to a function
        self.plot_widget.scene().sigMouseClicked.connect(self.on_plot_clicked)

    def start_plotting(self):
        self.plotting = True
        self.plot_data_timer.start(50)

    def stop_plotting(self):
        self.plotting = False
        self.plot_data_timer.stop()

    def save_plot(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getSaveFileName(self, "Save Plot", "", "Images (*.png *.jpg)")
        if file_path:
            image = self.plot_widget.grab()
            image.save(file_path)

    def plot_data(self):
        worker = DataReceiver(self.client_socket, self.expected_bytes)
        worker.signals.plot_data.connect(self.update_plot)
        QThreadPool.globalInstance().start(worker)

    def update_plot(self, received_data_array):
        if self.zero_crossing_index == -1:
            self.find_and_set_first_zero_crossing(received_data_array)
        self.plot_with_triggering(received_data_array)

    def find_and_set_first_zero_crossing(self, data):
        for i in range(len(data) - 1):
            x = data[i] - self.trigger_value
            y = data[i+1] - self.trigger_value
            if x * y <= 0 and x < y:
                self.zero_crossing_index=data[i+1]
                break
 
    def plot_with_triggering(self, received_data_array):
        for i in range(len(received_data_array) - 1):
            if received_data_array[i] == self.zero_crossing_index:
                shifted_received_data = received_data_array[i:]
                resampled_data = shifted_received_data[::self.scale_value]#signal.resample_poly(shifted_received_data, 1, self.scale_value)
                num_points = len(resampled_data)
                x_data = np.linspace(0, (2*num_points*self.scale_value/self.expected_bytes), num_points)
                self.series_channel1.setData(x_data, resampled_data)
                break
    
    def update_trigger_value(self, value):
        self.trigger_value = value / 10
        self.zero_crossing_index = -1
    
    def scale(self, value):
        self.scale_value = value

    def on_plot_clicked(self, event):
        if event.double():
            pos = event.pos()
            # Convert the mouse coordinates to data coordinates
            data_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x, y = data_pos.x(), data_pos.y()
            # Display the clicked coordinates in a QMessageBox
            message_box = QMessageBox(self)
            message_box.setWindowTitle("X,Y coordinates")
            message_box.setText(f"X : {x}, Y : {y}")
            message_box.exec()

    def enter_plot(self, event):
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leave_plot(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)


    def closeEvent(self, event):
        self.stop_plotting()
        self.client_socket.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    oscilloscope = Oscilloscope()
    oscilloscope.show()
    sys.exit(app.exec_())
