import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

from model import BusModel
from view import MainWindow


def main():
    """
    Entry point of the EMT Bus App.
    - Creates QApplication
    - Enables required WebEngine settings so Leaflet maps load
    - Instantiates data model and main window
    """

    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # WebEngine: allow JS + allow local HTML to load Leaflet,
    # CDN resources and injected JavaScript.
    # Without these, the map stays white or fails silently.
    # --------------------------------------------------------
    profile = QWebEngineProfile.defaultProfile()
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)

    # --------------------------------------------------------
    # Data layer (API client + formatting logic)
    # --------------------------------------------------------
    model = BusModel()

    # --------------------------------------------------------
    # GUI layer
    # --------------------------------------------------------
    window = MainWindow(model)
    window.show()

    # --------------------------------------------------------
    # Qt event loop
    # --------------------------------------------------------
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
