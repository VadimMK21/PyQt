import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget, QApplication, QCheckBox, QMainWindow, QGridLayout, QPushButton ,QButtonGroup, QVBoxLayout

def window():
    app = QApplication(sys.argv)
    widget = QWidget()
    grid = QVBoxLayout()
    
    for i in range(n):
        c = QCheckBox("Option %i" % i)
        grid.addWidget(c, i)
        checks.append(c)
    pb = QPushButton("Clear")
    pch = QPushButton("Checks")
    grid.addWidget(pb)
    grid.addWidget(pch)

    #c.clicked.connect(print_con)
    pb.clicked.connect(clear_ch)
    pch.clicked.connect(print_checks)
    widget.setLayout(grid)
    widget.setGeometry(100,100,200,100)
    widget.setWindowTitle("PyQt")
    widget.show()

    sys.exit(app.exec())

def clear_ch():
    for i in range(n):
        checks[i].setChecked(False)

def print_checks():
    for i in range(n):
        if checks[i].isChecked() == True:
            text = checks[i].text()
            isChecked = checks[i].isChecked()
            print(text, isChecked)

if __name__ == '__main__':
    checks = []
    n = 25
    window()