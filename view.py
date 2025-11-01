from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
)
from PyQt6 import QtWidgets
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, model):
        super().__init__()
        self.setupUi(self)
        self.model = model
        self.recent_stops = []

        # Connect buttons
        self.checkButton.clicked.connect(self.check_stop)
        self.stopInput.returnPressed.connect(self.check_stop)

    def check_stop(self):
        """When the user checks a bus stop."""
        stop = self.stopInput.text().strip()
        if not stop:
            QMessageBox.warning(self, "Error", "Please enter a stop number.")
            return

        try:
            result = self.model.fetch_arrivals(stop)
            self.show_arrivals(result)
            self.add_to_history(stop)
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Stop number must be numeric.")
        except LookupError as e:
            QMessageBox.information(self, "No data", str(e))
        except PermissionError as e:
            QMessageBox.critical(self, "Unauthorized", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not fetch data:\n{e}")

    def show_arrivals(self, result):
        """Display all arrivals in the scroll area."""
        layout = QVBoxLayout()
        for bus in result["data"]:
            card = QFrame()
            card.setObjectName("lineItem")
            row = QHBoxLayout(card)

            badge = QLabel(bus["line"])
            badge.setObjectName("badge")
            badge.setStyleSheet(
                f"background:{bus['color']}; color:black; padding:4px 10px; font-weight:700; border-radius:8px;"
            )
            row.addWidget(badge)

            dest = QLabel(bus["destination"])
            dest.setStyleSheet("font-weight:600;")
            row.addWidget(dest, 5)

            eta = QLabel(bus["eta"])
            eta.setObjectName("eta")
            row.addWidget(eta, 0, QtWidgets.Qt.AlignmentFlag.AlignRight)

            layout.addWidget(card)

        container = QWidget()
        container.setLayout(layout)
        self.scrollArea.setWidget(container)
        self.timestampLabel.setText(f"Last updated: {result['timestamp']}")

    def add_to_history(self, stop):
        """Create quick buttons for recently checked stops."""
        if stop in self.recent_stops:
            self.recent_stops.remove(stop)
        self.recent_stops.insert(0, stop)
        self.recent_stops = self.recent_stops[:6]

        grid = self.recentGrid
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, s in enumerate(self.recent_stops):
            b = QPushButton(s)
            b.clicked.connect(lambda _, x=s: self.load_from_history(x))
            grid.addWidget(b, i // 3, i % 3)

    def load_from_history(self, stop):
        """Re-check a stop from history."""
        self.stopInput.setText(stop)
        self.check_stop()
