from PyQt6.QtWidgets import QWidget, QCheckBox, QComboBox, QPushButton

class MDAFileVisualization(QWidget):
    # UI attributes created by uic.loadUi
    fitButton: QPushButton
    clearFitsButton: QPushButton
    logXCheckBox: QCheckBox
    logYCheckBox: QCheckBox
    curveStyle: QComboBox
