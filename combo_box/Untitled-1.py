import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QCheckBox, QMainWindow, QGridLayout, QButtonGroup, QHBoxLayout
 
app = QApplication(sys.argv)
window = QMainWindow()
grid = QHBoxLayout()
bg = QButtonGroup()

window.setGeometry(400,400,300,300)
window.setWindowTitle("CodersLegacy")
checks = []
for i in range(5):
    c = QCheckBox("Opt %i" % i, window)
    grid.addWidget(c, i)
    checks.append(c)

cb1 = QCheckBox("win 1")
cb2 = QCheckBox("win 2")
cb3 = QCheckBox("win 3")

grid.addWidget(cb1)
grid.addWidget(cb2)
grid.addWidget(cb3)

window.setLayout(grid)

window.show()
sys.exit(app.exec())