import sys
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QHBoxLayout, QDial, QToolTip
import serial
import serial.tools.list_ports
from pyqtgraph import PlotWidget
from PyQt5.QtGui import QCursor

class OscilloscopeLogic:
    def __init__(self, ui):
        self.ui = ui
        self.update_serial_ports()
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.setTitle("Real-Time Data")
        self.plot_widget.setLabel('left', 'Voltage', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='ms')
        self.plot_curve = self.plot_widget.plot(pen='r')
        self.plot_widget.setLimits(xMin=0, xMax=500, yMin=-3.5, yMax=3.5)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)

        self.ui.central_widget.layout().addWidget(self.plot_widget)

        self.serial_port = None
        self.data_buffer = np.zeros(500)
        self.is_paused = False
        self.triggered = False
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.ui.connect_button.clicked.connect(self.connect_serial)
        self.ui.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        self.ui.autoset_button.clicked.connect(lambda: self.autoset(self.data_buffer))


    def update_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        self.ui.port_combo.clear()
        for port in ports:
            self.ui.port_combo.addItem(port.device)

    def connect_serial(self):
        selected_port = self.ui.port_combo.currentText()
        if selected_port:
            try:
                self.serial_port = serial.Serial(selected_port, baudrate=2000000, timeout=0.1)
                self.ui.status_label.setText(f"Status: Connected to {selected_port}")
                self.data_buffer = np.zeros(500)
                self.plot_timer.start(5)
            except Exception as e:
                self.ui.status_label.setText(f"Failed to open serial port: {e}")
        else:
            self.ui.status_label.setText("No serial port selected!")

    def update_plot(self):
        if self.serial_port and not self.is_paused and self.serial_port.in_waiting > 0:
            try:
                data = self.serial_port.read(200)
                data_array = np.frombuffer(data, dtype=np.uint8)
                data_array = data_array.astype(np.float32) * 3.3 / 255

                trigger_level = self.ui.trigger_level_dial.value() / 100.0
                trigger_mode = self.ui.trigger_mode_combo.currentText()

                if not self.triggered:
                    for i in range(1, len(data_array)):
                        if (trigger_mode == "Rising" and data_array[i-1] < trigger_level <= data_array[i]) or \
                           (trigger_mode == "Falling" and data_array[i-1] > trigger_level >= data_array[i]):
                            self.triggered = True
                            break

                if self.triggered:
                    self.data_buffer = np.roll(self.data_buffer, -len(data_array))
                    self.data_buffer[-len(data_array):] = data_array[:]

                    vertical_scale = self.ui.vertical_scale_dial.value()
                    scaled_data = self.data_buffer * vertical_scale
                    horizontal_scale = self.ui.horizontal_scale_dial.value()
                    self.plot_widget.setXRange(0, 1000 / horizontal_scale)
                    self.plot_curve.setData(scaled_data)

            except Exception as e:
                print(f"Error reading from serial port: {e}")

    def toggle_pause_resume(self):
        if self.is_paused:
            self.is_paused = False
            self.triggered = False
            self.ui.pause_resume_button.setText("Pause")
        else:
            self.is_paused = True
            self.ui.pause_resume_button.setText("Resume")
    
    def closeEvent(self, event):
        if self.serial_port is not None:
            self.serial_port.close()
        event.accept()

    def on_mouse_moved(self, event):
        pos = event
        plot_item = self.plot_widget.getPlotItem()
        vb = plot_item.vb
        x_val, y_val = vb.mapSceneToView(pos).x(), vb.mapSceneToView(pos).y()
        global_pos = self.plot_widget.mapToGlobal(QCursor.pos())
        QToolTip.showText(global_pos, f"x: {x_val:.2f}, y: {y_val:.2f}")
        
    def set_vertical_scale(self, v_min, v_max):
        v_pp = v_max - v_min
        margin = 0.1 * v_pp
        self.plot_widget.setYRange(v_min - margin, v_max + margin)

    def autoset(self, data):
        v_max = np.max(data)
        v_min = np.min(data)
        v_pp = v_max - v_min
        self.set_vertical_scale(v_min, v_max)  # Pass v_min and v_max
        zero_crossings = np.where(np.diff(np.sign(data)))[0]
        if len(zero_crossings) > 1:
            periods = np.diff(zero_crossings) 
            avg_period = np.mean(periods)
            freq = self.sample_rate / avg_period 
            self.set_horizontal_scale(freq)
        trigger_level = (v_max + v_min) / 2
        self.set_trigger_level(trigger_level)


    def set_horizontal_scale(self, freq):
        time_per_div = 1 / (freq * 10)
        self.plot_widget.setXRange(0, time_per_div * 10)

    def set_trigger_level(self, trigger_level):
        self.trigger_level = trigger_level
        self.trigger_widget.setValue(trigger_level)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from oscilloscope_ui import OscilloscopeUI
    ui = OscilloscopeUI()
    logic = OscilloscopeLogic(ui)
    ui.show()
    sys.exit(app.exec_())
