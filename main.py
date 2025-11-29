import sys
from PyQt6.QtWidgets import QApplication
from model import BusModel
from view import MainWindow


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # Create data layer
    model = BusModel()

    # Create and show main window
    window = MainWindow(model)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
