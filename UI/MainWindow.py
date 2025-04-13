import sys
from PyQt5.QtWidgets import QApplication


from PolygonEditor import PolygonEditor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = PolygonEditor()
    window.show()
    sys.exit(app.exec_())