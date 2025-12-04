import os
import statistics
import folium

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl


class MapBridge(QObject):
    """
    Bridge between JavaScript and Python.
    JS calls: sendStopToPython(stop_id)
    Python receives: stopSelected(stop_id)
    """

    stopSelected = pyqtSignal(str)

    @pyqtSlot(str)
    def receiveStop(self, stop_id: str):
        self.stopSelected.emit(stop_id)


class MapWindow(QWidget):
    """
    Separate window containing a Leaflet map rendered via Folium.
    Shows:
    - Route polyline (shape)
    - Stop markers (with popup buttons that notify Python)
    """

    def __init__(self, line_name: str, stops, shape_points=None):
        """
        :param line_name: Visible line code ("3", "A1", etc.)
        :param stops: list of (stop_id, lat, lon, name)
        :param shape_points: optional list of (lat, lon) for route polyline
        """
        super().__init__()

        self.setWindowTitle(f"Mapa de línea {line_name}")
        self.resize(700, 600)

        self.shape_points = shape_points or []

        layout = QVBoxLayout(self)

        # Web view that will host the folium HTML
        self.web = QWebEngineView()
        layout.addWidget(self.web)

        # Build initial map and save HTML
        self.html_path = self._build_folium_map(line_name, stops, self.shape_points)

        # Setup channel and bridge for JS <-> Python
        self.channel = QWebChannel(self.web.page())
        self.bridge = MapBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        # Inject JS bridge into the HTML
        self._inject_bridge_js()

        url = QUrl.fromLocalFile(os.path.abspath(self.html_path))
        self.web.load(url)

    # ----------------------------------------------------
    # Create the folium map with markers + optional polyline
    # ----------------------------------------------------
    def _build_folium_map(self, line_name, stops, shape_points):
        """
        Build folium map with route stops and optional polyline.
        """
        # Center on average of stop coordinates if available
        if stops:
            lats = [s[1] for s in stops]
            lons = [s[2] for s in stops]
            center = [statistics.mean(lats), statistics.mean(lons)]
        else:
            center = [39.57, 2.65]  # fallback center (Palma)

        m = folium.Map(location=center, zoom_start=13)

        # Draw route polyline if we have shape points
        if shape_points:
            coords = [[lat, lon] for (lat, lon) in shape_points]
            folium.PolyLine(coords, weight=4, color="blue", opacity=0.8).add_to(m)

        # Add markers for each stop
        for stop_id, lat, lon, name in stops:
            popup_html = f"""
                <b>{name}</b><br>
                <button onclick="sendStopToPython('{stop_id}')">
                    Consultar parada {stop_id}
                </button>
            """
            folium.Marker(
                [lat, lon],
                popup=popup_html,
                tooltip=f"{stop_id} - {name}",
                icon=folium.Icon(color="red")
            ).add_to(m)

        html_path = os.path.join(os.path.dirname(__file__), "map_line.html")
        m.save(html_path)
        return html_path

    # ----------------------------------------------------
    # Inject QtWebChannel JS + bridge into folium HTML
    # ----------------------------------------------------
    def _inject_bridge_js(self):
        """
        Attach JS code so the map can talk back to Python
        using the Qt WebChannel API.
        """
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        injection = """
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
    var bridge = null;
    new QWebChannel(qt.webChannelTransport, function(channel) {
        bridge = channel.objects.bridge;
    });

    function sendStopToPython(stop_id) {
        if (bridge && bridge.receiveStop) {
            bridge.receiveStop(stop_id);
        }
    }
</script>
</body>
"""

        if "</body>" in html:
            html = html.replace("</body>", injection)
        else:
            html += injection

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
