import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QDial, QLabel,QMessageBox
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QRunnable, QThreadPool
from PyQt5 import QtCore, QtGui, QtWidgets
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


class LabeledDial(QtWidgets.QWidget):
    _dialProperties = ('minimum', 'maximum', 'value', 'singleStep', 'pageStep',
        'notchesVisible', 'tracking', 'wrapping', 
        'invertedAppearance', 'invertedControls', 'orientation')
    _inPadding = 3
    _outPadding = 2
    valueChanged = QtCore.pyqtSignal(int)




    def __init__(self, *args, **kwargs):
        dialArgs = {k:v for k, v in kwargs.items() if k in self._dialProperties}
        for k in dialArgs.keys():
            kwargs.pop(k)
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout(self)
        self.dial = QtWidgets.QDial(self, **dialArgs)
        layout.addWidget(self.dial)
        self.dial.valueChanged.connect(self.valueChanged)
        self.setFocusProxy(self.dial)
        self.value = self.dial.value
        self.setValue = self.dial.setValue
        self.minimum = self.dial.minimum
        self.maximum = self.dial.maximum
        self.wrapping = self.dial.wrapping
        self.notchesVisible = self.dial.notchesVisible
        self.setNotchesVisible = self.dial.setNotchesVisible
        self.setNotchTarget = self.dial.setNotchTarget
        self.notchSize = self.dial.notchSize
        self.invertedAppearance = self.dial.invertedAppearance
        self.setInvertedAppearance = self.dial.setInvertedAppearance
        self.updateSize()

    def inPadding(self):
        return self._inPadding

    def setInPadding(self, padding):
        self._inPadding = max(0, padding)
        self.updateSize()

    def outPadding(self):
        return self._outPadding

    def setOutPadding(self, padding):
        self._outPadding = max(0, padding)
        self.updateSize()

    def setMinimum(self, minimum):
        self.dial.setMinimum(minimum)
        self.updateSize()

    def setMaximum(self, maximum):
        self.dial.setMaximum(maximum)
        self.updateSize()

    def setWrapping(self, wrapping):
        self.dial.setWrapping(wrapping)
        self.updateSize()

    def updateSize(self):
        fm = self.fontMetrics()
        minWidth = max(fm.width(str(v)) for v in range(self.minimum(), self.maximum() + 1))
        self.offset = max(minWidth, fm.height()) / 2
        margin = int(self.offset + self._inPadding + self._outPadding) 
        self.layout().setContentsMargins(margin, margin, margin, margin)

    def translateMouseEvent(self, event):
        return QtGui.QMouseEvent(event.type(), 
            self.dial.mapFrom(self, event.pos()), 
            event.button(), event.buttons(), event.modifiers())
    
    def eventFilter(self, obj, event):
        if obj == self.plot_widget:
            # Forward the mouse events to the plot widget
            if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseMove, QtCore.QEvent.MouseButtonRelease):
                QApplication.sendEvent(self.plot_widget, event)
                return True
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.FontChange:
            self.updateSize()

    def mousePressEvent(self, event):
        self.dial.mousePressEvent(self.translateMouseEvent(event))

    def mouseMoveEvent(self, event):
        self.dial.mouseMoveEvent(self.translateMouseEvent(event))

    def mouseReleaseEvent(self, event):
        self.dial.mouseReleaseEvent(self.translateMouseEvent(event))

    def paintEvent(self, event):
        radius = min(self.width(), self.height()) / 2
        radius -= (self.offset / 2 + self._outPadding)
        invert = -1 if self.invertedAppearance() else 1
        if self.wrapping():
            angleRange = 360
            startAngle = 270
            rangeOffset = 0
        else:
            angleRange = 300
            startAngle = 240 if invert > 0 else 300
            rangeOffset = 1
        fm = self.fontMetrics()
        reference = QtCore.QLineF.fromPolar(radius, 0).translated(self.rect().center())
        fullRange = self.maximum() - self.minimum()
        textRect = QtCore.QRect()
        qp = QtGui.QPainter(self)
        qp.setRenderHints(qp.Antialiasing)
        for p in range(0, fullRange + rangeOffset, self.notchSize()):
            value = self.minimum() + p
            if invert < 0:
                value -= 1
                if value < self.minimum():
                    continue
            angle = p / fullRange * angleRange * invert
            reference.setAngle(startAngle - angle)
            text = str(value)
            textRect.setSize(fm.size(QtCore.Qt.TextSingleLine, text))
            textRect.moveCenter(reference.p2().toPoint())
            qp.drawText(textRect, QtCore.Qt.AlignCenter, text)
        qp.end()
class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        server_host = '169.254.116.191'
        #server_host = '127.0.0.1'
        server_port = 8081
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_host, server_port))
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

        # LabeledDial for trigger control
        self.trigger_dial = LabeledDial(minimum=-10, maximum=10, singleStep=2, value=0)
        self.trigger_dial.setNotchesVisible(True)
        self.trigger_value = 0
        self.trigger_dial.valueChanged.connect(self.update_trigger_value)
        button_layout.addWidget(self.trigger_dial)

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
        if self.plotting:
            expected_bytes = 4000
            worker = DataReceiver(self.client_socket, expected_bytes)
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
                self.zero_crossing=data[i+1]
                break
 
    def plot_with_triggering(self, received_data_array):
        for i in range(len(received_data_array) - 1):
            if received_data_array[i] == self.zero_crossing:
                shifted_received_data = received_data_array[i:]
                num_points = len(shifted_received_data)
                x_data = np.linspace(0, 2*num_points/5000000, num_points)
                self.series_channel1.setData(x_data, shifted_received_data)
                break
    
    def update_trigger_value(self, value):
        self.trigger_value = value / 10
        self.zero_crossing_index = -1

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
