import sys
from PyQt6.QtWidgets import QApplication
from model import BusModel
from view import MainWindow


def main():
    app = QApplication(sys.argv)
    model = BusModel()
    win = MainWindow(model)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
