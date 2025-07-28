from PyQt6.QtWidgets import QWidget, QComboBox, QLabel, QGroupBox

class MainWindow(QWidget):
    # UI attributes created by uic.loadUi
    folder: QComboBox
    info: QLabel
    groupbox: QGroupBox
