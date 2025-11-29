from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QMessageBox, QListWidget, QListWidgetItem,
    QGridLayout
)
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from ui_mainwindow import Ui_MainWindow
from map_window import MapWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, model):
        super().__init__()
        self.model = model

        # Build original UI (Tab 1)
        self.setupUi(self)
        self.tab1 = self.centralwidget

        # Setup tabs
        self._setup_tabs()
        self._rebind_tab1_widgets()

        # Setup Tab 2
        self._setup_lines_tab()

        # Tab 1 behaviour
        self.checkButton.clicked.connect(self.check_stop)
        self.stopInput.returnPressed.connect(self.check_stop)

        self.recent_stops = []

    # ----------------------------------------------------
    # TAB FIX BINDINGS
    # ----------------------------------------------------
    def _rebind_tab1_widgets(self):
        self.scrollArea = self.tab1.findChild(QtWidgets.QScrollArea, "scrollArea")
        self.timestampLabel = self.tab1.findChild(QLabel, "timestampLabel")
        self.recentGrid = self.tab1.findChild(QGridLayout, "recentGrid")

    # ----------------------------------------------------
    # TAB WRAPPER
    # ----------------------------------------------------
    def _setup_tabs(self):
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.addTab(self.tab1, "Paso por parada")
        self.tab2 = QWidget()
        self.tabWidget.addTab(self.tab2, "Consulta de líneas")
        self.setCentralWidget(self.tabWidget)

    # ----------------------------------------------------
    # TAB 2 BUILD
    # ----------------------------------------------------
    def _setup_lines_tab(self):
        layout = QVBoxLayout(self.tab2)

        titles = QHBoxLayout()
        layout.addLayout(titles)

        t1 = QLabel("Líneas")
        t1.setStyleSheet("font-size:16px; font-weight:700;")
        titles.addWidget(t1)

        t2 = QLabel("Sublíneas y dirección")
        t2.setStyleSheet("font-size:16px; font-weight:700;")
        titles.addWidget(t2)

        content = QHBoxLayout()
        layout.addLayout(content)

        self.linesList = QListWidget()
        self.directionsList = QListWidget()
        content.addWidget(self.linesList)
        content.addWidget(self.directionsList)

        try:
            self.lines_data = self.model.api.get_lines_raw()
        except Exception as e:
            QMessageBox.critical(self, "API Error", str(e))
            self.lines_data = []

        self._populate_lines()

        self.linesList.itemClicked.connect(self._on_line_clicked)
        self.directionsList.itemClicked.connect(self._on_direction_clicked)

    # ----------------------------------------------------
    # TAB 2 HELPERS
    # ----------------------------------------------------
    def _extract_line_code(self, line):
        return line.get("code") or line.get("shortName") or "?"

    def _extract_line_id(self, line):
        return line.get("routeGtfsId") or line.get("id")

    def _populate_lines(self):
        self.linesList.clear()

        for idx, line in enumerate(self.lines_data):
            code = self._extract_line_code(line)
            name = line.get("name", "")

            raw_color = line.get("color")
            if raw_color and raw_color.startswith("#"):
                color = raw_color
            else:
                rc = line.get("routeColor")
                color = f"#{rc}" if rc else "#999999"

            widget = QWidget()
            h = QHBoxLayout(widget)
            h.setContentsMargins(6, 4, 6, 4)

            badge = QLabel(code)
            badge.setStyleSheet(
                f"background:{color}; color:white;"
                "padding:6px 12px; border-radius:6px; font-weight:700;"
            )
            h.addWidget(badge)

            label = QLabel(name)
            label.setStyleSheet("font-weight:600; padding-left:10px;")
            h.addWidget(label)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, idx)

            self.linesList.addItem(item)
            self.linesList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # SUBLINES (RIGHT LIST, FIRST LEVEL FOR TAB 2)
    # ----------------------------------------------------
    def _populate_sublines(self, sublines, line):
        """
        First click on a line -> we show its sublines here.
        Each entry is type 'subline' and holds subline_id.
        """
        self.directionsList.clear()
        line_code = self._extract_line_code(line)

        if not sublines:
            lbl = QLabel("<b>No hay sublíneas para esta línea.</b>")
            item = QListWidgetItem()
            item.setSizeHint(lbl.sizeHint())
            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, lbl)
            return

        for sub in sublines:
            name = sub.get("longName", "Sublinea")
            sid = sub.get("subLineId")

            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(6, 4, 6, 4)

            t = QLabel(f"<b>{line_code} — {name}</b>")
            layout.addWidget(t)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())

            # store subline info
            item.setData(Qt.ItemDataRole.UserRole, {
                "type": "subline",
                "line": line_code,
                "subline_id": sid
            })

            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # DIRECTIONS (SECOND LEVEL FOR TAB 2)
    # ----------------------------------------------------
    def _populate_directions(self, directions, line_code):
        """
        Click on a subline -> we show its directions/headsigns here.
        Each entry is type 'direction' and later opens the map.
        """
        self.directionsList.clear()

        if not directions:
            lbl = QLabel("<b>No hay direcciones para esta sublínea.</b>")
            item = QListWidgetItem()
            item.setSizeHint(lbl.sizeHint())
            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, lbl)
            return

        for d in directions:
            head = d.get("headSign", "Destino")
            trip = d.get("tripId")

            widget = QWidget()
            v = QVBoxLayout(widget)
            v.setContentsMargins(6, 4, 6, 4)

            t = QLabel(f"<b>{line_code} → {head}</b>")
            v.addWidget(t)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, {
                "type": "direction",
                "line": line_code,
                "direction": head,
                "trip_id": trip
            })

            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # CLICK EVENTS
    # ----------------------------------------------------
    def _on_line_clicked(self, item):
        idx = item.data(Qt.ItemDataRole.UserRole)
        line = self.lines_data[idx]

        line_id = self._extract_line_id(line)
        if not line_id:
            QMessageBox.warning(self, "Error", "No line ID found.")
            return

        try:
            sublines = self.model.get_sublines(line_id)
        except Exception as e:
            QMessageBox.critical(self, "Error loading sublines", str(e))
            return

        self._populate_sublines(sublines, line)

    def _on_direction_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return

        # First click on a subline -> load its directions
        if data.get("type") == "subline":
            sid = data.get("subline_id")
            line_code = data.get("line", "?")
            try:
                directions = self.model.get_directions(sid)
            except Exception as e:
                QMessageBox.critical(self, "Error loading directions", str(e))
                return

            self._populate_directions(directions, line_code)
            return

        # Second click on a real direction -> open map
        if data.get("type") == "direction":
            line_code = data["line"]
            direction = data.get("direction", "")

            # TODO: replace this with REAL EMT stop data when you hook trips to stops
            stops = [
                ("17", 39.5715, 2.6500, f"Parada 17 ({direction})"),
                ("33", 39.5750, 2.6400, f"Parada 33 ({direction})"),
                ("401", 39.5650, 2.6550, f"Parada 401 ({direction})"),
            ]

            self.mapWindow = MapWindow(line_code, stops)
            self.mapWindow.bridge.stopSelected.connect(self._on_map_stop_selected)
            self.mapWindow.show()

    # ----------------------------------------------------
    # TAB 1 STOP LOOKUP
    # ----------------------------------------------------
    def check_stop(self):
        stop = self.stopInput.text().strip()

        if not stop:
            QMessageBox.warning(self, "Error", "Enter stop number.")
            return

        try:
            result = self.model.fetch_arrivals(stop)
            self.show_arrivals(result)
            self.add_to_history(stop)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def show_arrivals(self, result):
        layout = QVBoxLayout()

        for bus in result["data"]:
            card = QFrame()
            row = QHBoxLayout(card)

            badge = QLabel(bus["line"])
            badge.setStyleSheet(
                f"background:{bus['color']}; color:black;"
                "padding:4px 10px; font-weight:700;"
            )
            row.addWidget(badge)

            row.addWidget(QLabel(bus["destination"]), 5)
            row.addWidget(QLabel(bus["eta"]), 0, Qt.AlignmentFlag.AlignRight)

            layout.addWidget(card)

        container = QWidget()
        container.setLayout(layout)
        self.scrollArea.setWidget(container)

        self.timestampLabel.setText(f"Last updated: {result['timestamp']}")

    def add_to_history(self, stop):
        if stop in self.recent_stops:
            self.recent_stops.remove(stop)
        self.recent_stops.insert(0, stop)
        self.recent_stops = self.recent_stops[:6]

        while self.recentGrid.count():
            w = self.recentGrid.takeAt(0).widget()
            if w:
                w.deleteLater()

        for i, s in enumerate(self.recent_stops):
            btn = QPushButton(s)
            btn.clicked.connect(lambda _, x=s: self.load_from_history(x))
            self.recentGrid.addWidget(btn, i // 3, i % 3)

    def load_from_history(self, stop):
        self.stopInput.setText(stop)
        self.check_stop()

    # ----------------------------------------------------
    # MAP → TAB 1
    # ----------------------------------------------------
    def _on_map_stop_selected(self, stop_id: str):
        """
        Called when the user clicks a stop in the map.
        It switches to Tab 1 and behaves like consulting that stop.
        """
        self.tabWidget.setCurrentIndex(0)
        self.stopInput.setText(stop_id)
        self.check_stop()
