import sys
import time
import serial
import serial.tools.list_ports

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton,
    QCheckBox, QMessageBox, QButtonGroup, QDialog
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

class IPMCApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serialObj = None
        self.isConnected = False
        self.signalType = 0

        self.initUI()

    def initUI(self):
        self.setWindowTitle("IPMC Controller v1.1")
        self.setFixedSize(600, 350)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)

        # Top layout: CONNECT button, status label, Sync checkbox
        topLayout = QHBoxLayout()

        self.connectButton = QPushButton("CONNECT IPMC")
        self.connectButton.setFont(QFont("Arial", 11, QFont.Bold))
        self.connectButton.clicked.connect(self.connectOrDisconnect)
        self.connectButton.setMinimumSize(200, 60)
        topLayout.addWidget(self.connectButton)

        self.connectionStatusLabel = QLabel("Disconnected")
        self.connectionStatusLabel.setFont(QFont("Arial", 11, QFont.Bold))
        self.connectionStatusLabel.setStyleSheet("color: rgb(204, 45, 45);")
        topLayout.addWidget(self.connectionStatusLabel)

        topLayout.addStretch()

        self.syncCheckbox = QCheckBox("Synchronize sensors")
        self.syncCheckbox.setChecked(True)
        self.syncCheckbox.stateChanged.connect(self.syncCheckboxChanged)
        topLayout.addWidget(self.syncCheckbox)

        mainLayout.addLayout(topLayout)

        # Label para mostrar en qué puerto se está escaneando
        self.statusLabel = QLabel("")
        self.statusLabel.setFont(QFont("Arial", 9))
        mainLayout.addWidget(self.statusLabel)

        # Middle layout: SIGNAL SELECTION (left) y CURRENT SIGNAL (right)
        middleLayout = QHBoxLayout()
        mainLayout.addLayout(middleLayout)

        # SIGNAL SELECTION
        self.selectionGroup = QGroupBox("SIGNAL SELECTION")
        self.selectionGroup.setFont(QFont("Arial", 9, QFont.Bold))
        self.selectionGroup.setStyleSheet("""
            QGroupBox {
                background-color: #F0F0F0;
                border: 1px solid gray;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 2px;
            }
        """)
        selectionLayout = QGridLayout()
        selectionLayout.setContentsMargins(10, 15, 10, 10)
        selectionLayout.setHorizontalSpacing(10)
        selectionLayout.setVerticalSpacing(10)
        self.selectionGroup.setLayout(selectionLayout)
        middleLayout.addWidget(self.selectionGroup, stretch=1)

        # Frequency row
        freqLabel = QLabel("Select Frequency (Hz)")
        self.freqInput = QLineEdit("30")
        freqSendButton = QPushButton("Send")
        freqSendButton.clicked.connect(self.sendFrequency)
        selectionLayout.addWidget(freqLabel,      0, 0)
        selectionLayout.addWidget(self.freqInput, 0, 1)
        selectionLayout.addWidget(freqSendButton, 0, 2)

        # Amplitude IPMC 1
        amp1Label = QLabel("Select Peak-Peak (V) - IPMC 1")
        self.amp1Input = QLineEdit("3")
        amp1SendButton = QPushButton("Send")
        amp1SendButton.clicked.connect(self.sendAmplitude1)
        selectionLayout.addWidget(amp1Label,      1, 0)
        selectionLayout.addWidget(self.amp1Input, 1, 1)
        selectionLayout.addWidget(amp1SendButton, 1, 2)

        # Amplitude IPMC 2
        amp2Label = QLabel("Select Peak-Peak (V) - IPMC 2")
        self.amp2Input = QLineEdit("3")
        self.amp2Input.setEnabled(False)
        amp2SendButton = QPushButton("Send")
        amp2SendButton.setEnabled(False)
        amp2SendButton.clicked.connect(self.sendAmplitude2)
        selectionLayout.addWidget(amp2Label,      2, 0)
        selectionLayout.addWidget(self.amp2Input, 2, 1)
        selectionLayout.addWidget(amp2SendButton, 2, 2)
        self.amp2SendButton = amp2SendButton

        # Select Type + image + send button
        typeLayout = QHBoxLayout()

        self.selectImageLabel = QLabel()
        self.setImage(self.selectImageLabel, "images/sine.JPG", 110, 116)
        typeLayout.addWidget(self.selectImageLabel, alignment=Qt.AlignLeft)

        self.typeGroupBox = QGroupBox("Select Type")
        self.typeGroupBox.setFont(QFont("Arial", 9, QFont.Bold))
        self.typeGroupBox.setStyleSheet("""
            QGroupBox {
                background-color: #F0F0F0;
                border: 1px solid gray;
                margin-top: 6px;
            }
        """)
        typeRadioLayout = QVBoxLayout()
        self.typeGroupBox.setLayout(typeRadioLayout)

        self.radioSine = QRadioButton("Sine")
        self.radioSquare = QRadioButton("Square")
        self.radioSawtooth = QRadioButton("Sawtooth")
        self.radioTriangular = QRadioButton("Triangular")
        self.radioSine.setChecked(True)

        typeRadioLayout.addWidget(self.radioSine)
        typeRadioLayout.addWidget(self.radioSquare)
        typeRadioLayout.addWidget(self.radioSawtooth)
        typeRadioLayout.addWidget(self.radioTriangular)

        self.signalTypeGroup = QButtonGroup()
        self.signalTypeGroup.addButton(self.radioSine, 0)
        self.signalTypeGroup.addButton(self.radioSquare, 1)
        self.signalTypeGroup.addButton(self.radioSawtooth, 2)
        self.signalTypeGroup.addButton(self.radioTriangular, 3)

        typeLayout.addWidget(self.typeGroupBox, alignment=Qt.AlignVCenter)

        sendTypeBtn = QPushButton("Send")
        sendTypeBtn.clicked.connect(self.sendType)
        typeLayout.addWidget(sendTypeBtn, alignment=Qt.AlignRight)

        selectionLayout.addLayout(typeLayout, 3, 0, 1, 3)

        # CURRENT SIGNAL
        self.currentGroup = QGroupBox("CURRENT SIGNAL")
        self.currentGroup.setFont(QFont("Arial", 9, QFont.Bold))
        self.currentGroup.setStyleSheet("""
            QGroupBox {
                background-color: #F0F0F0;
                border: 1px solid gray;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 2px;
            }
        """)
        currentLayout = QVBoxLayout()
        currentLayout.setContentsMargins(10, 15, 10, 10)
        currentLayout.setSpacing(10)
        self.currentGroup.setLayout(currentLayout)
        middleLayout.addWidget(self.currentGroup, stretch=1)

        self.currentImageLabel = QLabel()
        self.setImage(self.currentImageLabel, "images/sine.JPG", 152, 160)
        currentLayout.addWidget(self.currentImageLabel, alignment=Qt.AlignHCenter)

        self.currentFreqLabel = QLabel("Frequency    30 Hz")
        self.currentFreqLabel.setFont(QFont("Arial", 10))
        currentLayout.addWidget(self.currentFreqLabel, alignment=Qt.AlignHCenter)

        self.currentAmp1Label = QLabel("Amplitude IMPC 1    3 V")
        self.currentAmp1Label.setFont(QFont("Arial", 10))
        currentLayout.addWidget(self.currentAmp1Label, alignment=Qt.AlignHCenter)

        self.currentAmp2Label = QLabel("Amplitude IMPC 2    3 V")
        self.currentAmp2Label.setFont(QFont("Arial", 10))
        currentLayout.addWidget(self.currentAmp2Label, alignment=Qt.AlignHCenter)

        mainLayout.addStretch()

    # ----------------------------------------------------------------
    #   POPUP PARA ESCANEAR PUERTOS
    # ----------------------------------------------------------------
    def connectOrDisconnect(self):
        if not self.isConnected:
            # Mostrar popup "Scanning..."
            scanningDialog = QDialog(self)
            scanningDialog.setWindowTitle("Scanning")
            scanningDialog.setWindowModality(Qt.ApplicationModal)
            layout = QVBoxLayout(scanningDialog)
            label = QLabel("Scanning for available IPMC device...\nPlease wait")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            scanningDialog.resize(300, 80)
            
            # Mostramos el popup
            scanningDialog.show()
            QApplication.processEvents()  # Refresca la interfaz

            # Realizamos el escaneo de puertos
            try:
                if self.connectIPMC():
                    self.isConnected = True
                    self.connectButton.setText("DISCONNECT IPMC")
                    self.connectionStatusLabel.setText("Connected")
                    self.connectionStatusLabel.setStyleSheet("color: rgb(120, 170, 48); font-weight: bold;")
                    self.statusLabel.setText("")
                else:
                    self.isConnected = False
                    self.connectButton.setText("CONNECT IPMC")
                    self.connectionStatusLabel.setText("Disconnected")
                    self.connectionStatusLabel.setStyleSheet("color: rgb(204, 45, 45); font-weight: bold;")
            finally:
                # Cerrar el popup, pase lo que pase
                scanningDialog.close()

        else:
            self.disconnectIPMC()
            self.isConnected = False
            self.connectButton.setText("CONNECT IPMC")
            self.connectionStatusLabel.setText("Disconnected")
            self.connectionStatusLabel.setStyleSheet("color: rgb(204, 45, 45); font-weight: bold;")
            self.statusLabel.setText("")

    def connectIPMC(self):
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            QMessageBox.warning(self, "Connection Error", "No available COM ports were found.")
            self.statusLabel.setText("No COM ports available.")
            return False

        for port in ports:
            try:
                self.statusLabel.setText(f"Checking port {port.device}...")
                self.statusLabel.setStyleSheet("color: rgb(204, 100, 0); font-weight: bold;")
                QApplication.processEvents()
                s = serial.Serial(port.device, 115200, timeout=2)
                found = False
                start_time = time.time()
                while time.time() - start_time < 3:
                    if s.in_waiting:
                        data = s.readline().decode('utf-8', errors='ignore').strip()
                        if "IPMC_READY" in data:
                            found = True
                            break
                    time.sleep(0.2)
                    QApplication.processEvents()
                if found:
                    s.write(b"S\n")
                    time.sleep(1)
                    if s.in_waiting:
                        response = s.read(1)
                        if response == b'\x01':
                            self.statusLabel.setText(f"Device found on {port.device}")
                            self.serialObj = s
                            return True
                s.close()
            except Exception as e:
                print(f"Error on port {port.device}: {e}")

        self.statusLabel.setText("Could not establish connection to the IPMC device.")
        QMessageBox.warning(self, "Connection Error", "Could not establish a connection to the IPMC device.")
        return False

    def disconnectIPMC(self):
        if self.serialObj and self.serialObj.is_open:
            try:
                self.serialObj.write(b"E")
                self.serialObj.close()
            except Exception as e:
                print("Error during disconnect:", e)
        self.serialObj = None

    # ----------------------------------------------------------------
    #   CHECKBOX: SYNCHRONIZE SENSORS
    # ----------------------------------------------------------------
    def syncCheckboxChanged(self, state):
        if self.syncCheckbox.isChecked():
            self.amp2Input.setEnabled(False)
            self.amp2SendButton.setEnabled(False)
        else:
            self.amp2Input.setEnabled(True)
            self.amp2SendButton.setEnabled(True)

    # ----------------------------------------------------------------
    #   ENVÍO DE FRECUENCIA
    # ----------------------------------------------------------------
    def sendFrequency(self):
        if not self.checkConnection():
            return
        try:
            value = float(self.freqInput.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Frequency must be a number.")
            return
        if value < 0.1 or value > 30:
            QMessageBox.warning(self, "Invalid Frequency", "Value must be between 0.1 and 30 Hz.")
            return
        try:
            cmd = f"F1{int(value*10)}\n"
            self.serialObj.write(cmd.encode())
            time.sleep(0.5)
            if self.serialObj.in_waiting:
                response = self.serialObj.read(1)
                if response == b'\x01':
                    self.currentFreqLabel.setText(f"Frequency    {value} Hz")
        except Exception as e:
            QMessageBox.warning(self, "Communication Error", f"Error sending frequency: {e}")

    # ----------------------------------------------------------------
    #   ENVÍO DE AMPLITUD 1
    # ----------------------------------------------------------------
    def sendAmplitude1(self):
        if not self.checkConnection():
            return
        try:
            value = float(self.amp1Input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Amplitude must be a number.")
            return
        if value < 0 or value > 20:
            QMessageBox.warning(self, "Invalid Amplitude", "Value must be between 0 and 20 V.")
            return
        try:
            cmd = f"A0{int(value)}\n" if self.syncCheckbox.isChecked() else f"A1{int(value)}\n"
            self.serialObj.write(cmd.encode())
            time.sleep(0.5)
            self.currentAmp1Label.setText(f"Amplitude IMPC 1    {value} V")
            if self.syncCheckbox.isChecked():
                self.currentAmp2Label.setText(f"Amplitude IMPC 2    {value} V")
        except Exception as e:
            QMessageBox.warning(self, "Communication Error", f"Error sending amplitude 1: {e}")

    # ----------------------------------------------------------------
    #   ENVÍO DE AMPLITUD 2
    # ----------------------------------------------------------------
    def sendAmplitude2(self):
        if not self.checkConnection():
            return
        try:
            value = float(self.amp2Input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Amplitude must be a number.")
            return
        if value < 0 or value > 20:
            QMessageBox.warning(self, "Invalid Amplitude", "Value must be between 0 and 20 V.")
            return
        try:
            cmd = f"A2{int(value)}\n"
            self.serialObj.write(cmd.encode())
            time.sleep(0.5)
            self.currentAmp2Label.setText(f"Amplitude IMPC 2    {value} V")
        except Exception as e:
            QMessageBox.warning(self, "Communication Error", f"Error sending amplitude 2: {e}")

    # ----------------------------------------------------------------
    #   ENVÍO DE TIPO DE SEÑAL
    # ----------------------------------------------------------------
    def sendType(self):
        if not self.checkConnection():
            return
        # Revisamos qué botón está seleccionado
        if self.radioSine.isChecked():
            self.signalType = 0
            imagePath = "images/sine.JPG"
        elif self.radioSquare.isChecked():
            self.signalType = 1
            imagePath = "images/square.JPG"
        elif self.radioSawtooth.isChecked():
            self.signalType = 2
            imagePath = "images/sawtooth.JPG"
        elif self.radioTriangular.isChecked():
            self.signalType = 3
            imagePath = "images/triangular.JPG"
        else:
            QMessageBox.warning(self, "Selection Error", "No valid signal type selected.")
            return
        try:
            cmd = f"T1{self.signalType}\n"
            self.serialObj.write(cmd.encode())
            time.sleep(0.3)
            self.setImage(self.currentImageLabel, imagePath, 152, 160)
        except Exception as e:
            QMessageBox.warning(self, "Communication Error", f"Error sending type: {e}")

    # ----------------------------------------------------------------
    #   MÉTODOS AUXILIARES
    # ----------------------------------------------------------------
    def checkConnection(self):
        if not self.serialObj or not self.serialObj.is_open:
            QMessageBox.warning(self, "Connection Error",
                                "Serial connection is not established. Please connect the device first.")
            return False
        return True

    def setImage(self, label, imagePath, width, height):
        pixmap = QPixmap(imagePath)
        label.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        self.disconnectIPMC()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = IPMCApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
