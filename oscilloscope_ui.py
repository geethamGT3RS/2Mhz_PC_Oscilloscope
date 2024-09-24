import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QHBoxLayout, QDial, QToolTip
from PyQt5.QtGui import QFont

class OscilloscopeUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Oscilloscope")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        QToolTip.setFont(QFont('SansSerif', 10))

        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        self.port_label = QLabel("Select USB Port:")
        self.port_label.setFont(QFont('Arial', 12))
        self.port_label.setStyleSheet("padding: 5px;")
        left_panel.addWidget(self.port_label)

        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        left_panel.addWidget(self.port_combo)

        self.connect_button = QPushButton("Connect")
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
        self.horizontal_scale_dial = self.create_dial("Horizontal Scale", 1, 500, 10)
        self.vertical_scale_dial = self.create_dial("Vertical Scale", 1, 500, 10)
        left_panel.addWidget(QLabel("Horizontal Scale:"))
        left_panel.addWidget(self.horizontal_scale_dial)

        left_panel.addWidget(QLabel("Vertical Scale:"))
        left_panel.addWidget(self.vertical_scale_dial)

        self.trigger_level_dial = QDial()
        self.trigger_level_dial.setRange(0, 500)
        self.trigger_level_dial.setValue(165)
        self.trigger_level_dial.setNotchesVisible(True)
        self.trigger_level_dial.setStyleSheet("background-color: #3d3d3d; color: white;")
        left_panel.addWidget(QLabel("Trigger Level (V*100):"))
        left_panel.addWidget(self.trigger_level_dial)

        self.trigger_mode_combo = QComboBox()
        self.trigger_mode_combo.addItem("Rising")
        self.trigger_mode_combo.addItem("Falling")
        self.trigger_mode_combo.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        left_panel.addWidget(QLabel("Trigger Mode:"))
        left_panel.addWidget(self.trigger_mode_combo)

        self.pause_resume_button = QPushButton("Pause")
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

        self.autoset_button = QPushButton("Auto set")
        self.autoset_button.setStyleSheet("""
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
        left_panel.addWidget(self.autoset_button)

        main_layout.addLayout(left_panel)
        self.central_widget = QWidget()
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

    def create_dial(self, label, min_val, max_val, default_val):
        dial = QDial()
        dial.setRange(min_val, max_val)
        dial.setValue(default_val)
        dial.setNotchesVisible(True)
        dial.setStyleSheet("background-color: #3d3d3d; color: white;")
        return dial

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = OscilloscopeUI()
    ui.show()
    sys.exit(app.exec_())
