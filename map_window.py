import os
import statistics

import folium

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl


class MapBridge(QObject):
    stopSelected = pyqtSignal(str)

    @pyqtSlot(str)
    def receiveStop(self, stop_id: str):
        self.stopSelected.emit(stop_id)


class MapWindow(QWidget):
    def __init__(self, line_name: str, stops):
        super().__init__()
        self.setWindowTitle(f"Mapa de línea {line_name}")
        self.resize(800, 650)

        layout = QVBoxLayout(self)

        self.web = QWebEngineView()
        layout.addWidget(self.web)

        self.html_path = self._build_folium_map(line_name, stops)

        self.channel = QWebChannel(self.web.page())
        self.bridge = MapBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        self._inject_leaflet_head()
        self._inject_bridge_js()

        url = QUrl.fromLocalFile(os.path.abspath(self.html_path))
        self.web.load(url)

    # -------------------------------------------------------------------
    # Build folium HTML
    # -------------------------------------------------------------------
    def _build_folium_map(self, line_name, stops):
        if stops:
            lats = [s[1] for s in stops]
            lons = [s[2] for s in stops]
            center = [statistics.mean(lats), statistics.mean(lons)]
        else:
            center = [39.57, 2.65]  # Palma default

        m = folium.Map(location=center, zoom_start=13)

        for stop_id, lat, lon, name in stops:
            popup_html = f"""
                <b>{name}</b><br>
                <button onclick="sendStopToPython('{stop_id}')">
                    Consultar parada {stop_id}
                </button>
            """
            folium.Marker(
                [lat, lon],
                tooltip=f"{stop_id} - {name}",
                popup=popup_html,
                icon=folium.Icon(color="red")
            ).add_to(m)

        html_path = os.path.join(os.path.dirname(__file__), "map_line.html")
        m.save(html_path)
        return html_path

    # -------------------------------------------------------------------
    # FIX #1: Move Leaflet JS to the HEAD so folium scripts can use L.icon
    # -------------------------------------------------------------------
    def _inject_leaflet_head(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        leaflet_head = """
    <!-- FIX: Load Leaflet BEFORE folium JS -->
    <link rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
"""

        # inject right after <head>
        if "<head>" in html:
            html = html.replace("<head>", "<head>" + leaflet_head)

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)

    # -------------------------------------------------------------------
    # FIX #2: Add bridge JS at end of document
    # -------------------------------------------------------------------
    def _inject_bridge_js(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        bridge_js = """
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        var pybridge = null;

        new QWebChannel(qt.webChannelTransport, function(channel) {
            pybridge = channel.objects.bridge;
        });

        function sendStopToPython(stop_id) {
            if (pybridge) {
                pybridge.receiveStop(stop_id);
            } else {
                console.log("Bridge missing");
            }
        }
    </script>
</body>
"""

        if "</body>" in html:
            html = html.replace("</body>", bridge_js)
        else:
            html += bridge_js

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
