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
    # LOAD ROUTES FOR A LINE
    # ----------------------------------------------------
    def _populate_directions_for_line(self, line):
        self.directionsList.clear()

        line_id = self._extract_line_id(line)
        line_code = self._extract_line_code(line)

        try:
            info = self.model.api.get_line_info(line_id)
        except Exception as e:
            lbl = QLabel(f"<b>Error cargando rutas</b><br>{e}")
            item = QListWidgetItem()
            item.setSizeHint(lbl.sizeHint())
            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, lbl)
            return

        routes = info.get("routes", [])

        if not routes:
            lbl = QLabel("<b>No hay rutas disponibles</b>")
            item = QListWidgetItem()
            item.setSizeHint(lbl.sizeHint())
            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, lbl)
            return

        for r in routes:
            origin = r.get("origin", "Origen")
            dest = r.get("destination", "Destino")
            rid = r.get("id")

            widget = QWidget()
            v = QVBoxLayout(widget)
            v.setContentsMargins(6, 4, 6, 4)

            title = QLabel(f"<b>{line_code} → {dest}</b>")
            v.addWidget(title)

            meta = QLabel(f"<span style='color:#888;'>Desde: {origin}</span>")
            meta.setStyleSheet("font-size:11px;")
            v.addWidget(meta)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, {
                "line": line_code,
                "direction": dest,
                "route_id": rid
            })

            self.directionsList.addItem(item)
            self.directionsList.setItemWidget(item, widget)

    # ----------------------------------------------------
    # CLICK EVENTS
    # ----------------------------------------------------
    def _on_line_clicked(self, item):
        idx = item.data(Qt.ItemDataRole.UserRole)
        self._populate_directions_for_line(self.lines_data[idx])

    def _on_direction_clicked(self, item):
        p = item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(
            self,
            "Dirección seleccionada",
            f"Línea: {p['line']}\n"
            f"Dirección: {p['direction']}\n"
            f"ID ruta: {p['route_id']}"
        )

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

    
    def _on_map_stop_selected(self, stop_id):
        self.tabWidget.setCurrentIndex(0)
        self.stopInput.setText(stop_id)
        self.check_stop()
     
    
    

