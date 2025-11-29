import os
import statistics
import folium

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl


# ---------------------------------------------------------
# BRIDGE (JS → Python)
# ---------------------------------------------------------
class MapBridge(QObject):
    stopSelected = pyqtSignal(str)

    @pyqtSlot(str)
    def receiveStop(self, stop_id: str):
        self.stopSelected.emit(stop_id)


# ---------------------------------------------------------
# MAP WINDOW
# ---------------------------------------------------------
class MapWindow(QWidget):
    """
    Creates a folium map, loads it in QWebEngineView,
    and injects the WebChannel bridge so JS calls Python.
    """

    def __init__(self, line_name: str, stops):
        super().__init__()
        self.setWindowTitle(f"Mapa de línea {line_name}")
        self.resize(700, 600)

        layout = QVBoxLayout(self)

        # Web view
        self.web = QWebEngineView()
        layout.addWidget(self.web)

        # Build folium map
        self.html_path = self._build_folium_map(line_name, stops)

        # WebChannel setup
        self.channel = QWebChannel(self.web.page())
        self.bridge = MapBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        # Inject JS bridge code into the generated HTML
        self._inject_bridge_js()

        # Load HTML into webview
        url = QUrl.fromLocalFile(os.path.abspath(self.html_path))
        self.web.load(url)

    # ---------------------------------------------------------
    # BUILD FOLIUM MAP HTML
    # ---------------------------------------------------------
    def _build_folium_map(self, line_name, stops):

        if stops:
            lats = [s[1] for s in stops]
            lons = [s[2] for s in stops]
            center = [statistics.mean(lats), statistics.mean(lons)]
        else:
            center = [39.57, 2.65]  # Palma default

        m = folium.Map(location=center, zoom_start=13)

        # Markers with a JS callback button
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

    # ---------------------------------------------------------
    # INJECT WEBCHANNEL + JS BRIDGE
    # ---------------------------------------------------------
    def _inject_bridge_js(self):
        """
        Insert JS inside <body> BEFORE </body> without breaking Folium's script order.
        """

        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Code injected right before </body>
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
        } else {
            console.log("Bridge not ready");
        }
    }
</script>
"""

        # Insert BEFORE </body>
        html = html.replace("</body>", injection + "\n</body>")

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
 