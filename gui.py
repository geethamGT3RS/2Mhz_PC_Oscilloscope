import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
import pyqtgraph as pg
import numpy as np
import socket
import struct

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
                received_data_array = received_data_array.astype(np.float16) * 5 / 4096
                self.signals.plot_data.emit(received_data_array)
                self.received_data.extend(received_data_array)

class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        server_host = '169.254.116.191'
        server_port = 8081
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_host, server_port))
        self.setWindowTitle("Oscilloscope")
        self.setGeometry(0, 0, 1920, 1080)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        self.plot_widget = pg.PlotWidget(self.central_widget)
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Oscilloscope")
        self.series_channel1 = self.plot_widget.plot(pen='r', name="Channel 1")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(y=False)  
        self.plot_widget.setYRange(-5, 5)
        main_layout.addWidget(self.plot_widget)
        worker = DataReceiver(self.client_socket, 4000)
        worker.signals.plot_data.connect(self.update_plot)
        QThreadPool.globalInstance().start(worker)

    def update_plot(self, data):
        self.series_channel1.setData(data)

    def closeEvent(self, event):
        self.client_socket.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    oscilloscope = Oscilloscope()
    oscilloscope.show()
    sys.exit(app.exec_())
