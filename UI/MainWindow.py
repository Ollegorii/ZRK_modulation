import sys
from PyQt5.QtWidgets import QApplication
import logging

from UI.PolygonEditor import PolygonEditor


# from .PolygonEditor import PolygonEditor

def setup_logging():
    logging.basicConfig(
        filename='./logs/app.log',
        filemode='w',       
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

if __name__ == "__main__":
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = PolygonEditor()
    window.show()
    sys.exit(app.exec_())