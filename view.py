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
    """
    Main GUI controller.
    Handles:
    - Tab 1 (stop lookup)
    - Tab 2 (lines → sublines → directions)
    - Opening map window with real EMT data
    """

    def __init__(self, model):
        super().__init__()
        self.model = model

        # Build UI created in Qt Designer
        self.setupUi(self)
        self.tab1 = self.centralwidget

        # Setup tabs
        self._setup_tabs()

        # Re-bind Tab 1 widgets after embedding them in a tab
        self._rebind_tab1_widgets()

        # Build Tab 2 layout
        self._setup_lines_tab()

        # Tab 1 logic
        self.checkButton.clicked.connect(self.check_stop)
        self.stopInput.returnPressed.connect(self.check_stop)

        self.recent_stops = []

    # ----------------------------------------------------
    # Fix references to widgets in Tab 1
    # ----------------------------------------------------
    def _rebind_tab1_widgets(self):
        self.scrollArea = self.tab1.findChild(QtWidgets.QScrollArea, "scrollArea")
        self.timestampLabel = self.tab1.findChild(QLabel, "timestampLabel")
        self.recentGrid = self.tab1.findChild(QGridLayout, "recentGrid")

    # ----------------------------------------------------
    # Tabs container
    # ----------------------------------------------------
    def _setup_tabs(self):
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.addTab(self.tab1, "Paso por parada")
        self.tab2 = QWidget()
        self.tabWidget.addTab(self.tab2, "Consulta de líneas")
        self.setCentralWidget(self.tabWidget)

    # ----------------------------------------------------
    # TAB 2: Layout (lines on left, sublines/directions on right)
    # ----------------------------------------------------
    def _setup_lines_tab(self):
        layout = QVBoxLayout(self.tab2)

        # Titles row
        titles = QHBoxLayout()
        layout.addLayout(titles)

        lbl_left = QLabel("Líneas")
        lbl_left.setStyleSheet("font-size:16px; font-weight:700;")
        titles.addWidget(lbl_left)

        lbl_right = QLabel("Sublíneas y dirección")
        lbl_right.setStyleSheet("font-size:16px; font-weight:700;")
        titles.addWidget(lbl_right)

        # Two list widgets
        content = QHBoxLayout()
        layout.addLayout(content)

        self.linesList = QListWidget()
        self.directionsList = QListWidget()
        content.addWidget(self.linesList)
        content.addWidget(self.directionsList)

        # Load EMT lines
        try:
            self.lines_data = self.model.api.get_lines_raw()
        except Exception as e:
            QMessageBox.critical(self, "API Error", str(e))
            self.lines_data = []

        self._populate_lines()

        # Click handlers
        self.linesList.itemClicked.connect(self._on_line_clicked)
        self.directionsList.itemClicked.connect(self._on_direction_clicked)

    # ----------------------------------------------------
    # Helpers to extract fields from line dicts
    # ----------------------------------------------------
    def _extract_line_code(self, line):
        return line.get("code") or line.get("shortName") or "?"

    def _extract_line_id(self, line):
        # Numeric ID used by EMT line endpoints
        return line.get("id") or line.get("routeGtfsId")

    # ----------------------------------------------------
    # Left column: Lines list
    # ----------------------------------------------------
    def _populate_lines(self):
        self.linesList.clear()

        for idx, line in enumerate(self.lines_data):
            code = self._extract_line_code(line)
            name = line.get("name", "")

            # Color logic (Tab 2 badge)
            raw_color = line.get("color")
            if raw_color and raw_color.startswith("#"):
                color = raw_color
            else:
                rc = line.get("routeColor")
                color = f"#{rc}" if rc else "#999999"

            # Visual row
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
    # Right column — Sublines (first level)
    # ----------------------------------------------------
    def _populate_sublines(self, sublines, line):
        """
        Show sublines of a selected line.
        Each item is clickable and will load directions.
        """
        self.directionsList.clear()
        line_code = self._extract_line_code(line)
        line_id = self._extract_line_id(line)

        if not sublines:
            lbl = QLabel("<b>No hay sublíneas para esta línea.</b>")
            item = QListWidgetItem()
            item.setSizeHint(lbl.sizeHint())
            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, lbl)
            return

        for sub in sublines:
            name = sub.get("longName", "Sublínea")
            sid = sub.get("subLineId")

            widget = QWidget()
            v = QVBoxLayout(widget)
            v.setContentsMargins(6, 4, 6, 4)

            t = QLabel(f"<b>{line_code} — {name}</b>")
            v.addWidget(t)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())

            # We keep line code, line ID and subline ID for the next click
            item.setData(Qt.ItemDataRole.UserRole, {
                "type": "subline",
                "line": line_code,
                "line_id": line_id,
                "subline_id": sid
            })

            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # Right column — Directions (second level)
    # ----------------------------------------------------
    def _populate_directions(self, directions, line_code, line_id):
        """
        Show directions (headSigns) for a chosen subline.
        Direction items are the ones that open the map.
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

            # Store all info needed to fetch route + open map
            item.setData(Qt.ItemDataRole.UserRole, {
                "type": "direction",
                "line": line_code,
                "line_id": line_id,
                "direction": head,
                "trip_id": trip
            })

            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # TAB 2 click handling
    # ----------------------------------------------------
    def _on_line_clicked(self, item):
        """
        First click: user selects a line.
        → We load sublines of that line.
        """
        idx = item.data(Qt.ItemDataRole.UserRole)
        line = self.lines_data[idx]

        line_id = self._extract_line_id(line)
        if not line_id:
            QMessageBox.warning(self, "Error", "No line ID found for this line.")
            return

        try:
            sublines = self.model.get_sublines(line_id)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar sublíneas", str(e))
            return

        self._populate_sublines(sublines, line)

    def _on_direction_clicked(self, item):
        """
        Two possible clicks in the right list:
        - Click on SUBLINE  → we load directions.
        - Click on DIRECTION → we fetch route data and open map.
        """
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return

        t = data.get("type")

        # First level: subline → load directions
        if t == "subline":
            sid = data["subline_id"]
            line_code = data["line"]
            line_id = data.get("line_id")

            try:
                directions = self.model.get_directions(sid)
            except Exception as e:
                QMessageBox.critical(self, "Error al cargar direcciones", str(e))
                return

            self._populate_directions(directions, line_code, line_id)
            return

        # Second level: direction → fetch stops + shape + open map
        if t == "direction":
            line_code = data["line"]
            line_id = data.get("line_id")
            direction = data.get("direction")
            trip_id = data.get("trip_id")

            if not line_id or not trip_id:
                QMessageBox.warning(self, "Error", "Datos de línea o viaje incompletos.")
                return

            try:
                stops = self.model.get_route_stops(line_id, trip_id)
                shape = self.model.get_route_shape(line_id, trip_id)
            except Exception as e:
                QMessageBox.critical(self, "Error al cargar datos de mapa", str(e))
                return

            if not stops:
                QMessageBox.warning(self, "Sin paradas", "No se han encontrado paradas para esta ruta.")
                return

            # Open map window with real EMT data
            self.mapWindow = MapWindow(line_code, stops, shape)
            self.mapWindow.bridge.stopSelected.connect(self._on_map_stop_selected)
            self.mapWindow.show()

    # ----------------------------------------------------
    # TAB 1 — Stop lookup
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
        """
        Render arrivals cards in the scroll area for Tab 1.
        """
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
        """
        Manage the quick-access buttons for recently checked stops.
        """
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
        """
        Called when user clicks a button in the history grid.
        """
        self.stopInput.setText(stop)
        self.check_stop()

    # ----------------------------------------------------
    # MAP → TAB 1: When a stop is clicked on the map
    # ----------------------------------------------------
    def _on_map_stop_selected(self, stop_id: str):
        """
        Called by the MapWindow when user presses
        'Consultar parada' on a marker popup.
        """
        self.tabWidget.setCurrentIndex(0)
        self.stopInput.setText(stop_id)
        self.check_stop()
