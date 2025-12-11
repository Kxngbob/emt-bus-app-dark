"""
Manual test script for MapWindow.
This allows testing the map without running the full EMT App.
"""
import sys
import os

# Add project root folder to Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

import sys
import time

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
 
from map_window import MapWindow


def pause(msg="Press ENTER to continue..."):
    input(msg)


def run_test_scenarios():
    """
    Runs several visual map test scenarios using fake data.
    Tester will manually verify each result.
    """

    # --------------------------------------------------------
    # TEST SCENARIO 1 – Simple line with 3 fake stops
    # --------------------------------------------------------
    print("Running Scenario 1: Simple line preview...")
    stops1 = [
        ("101", 39.575, 2.650, "Fake Stop A"),
        ("102", 39.578, 2.655, "Fake Stop B"),
        ("103", 39.572, 2.645, "Fake Stop C"),
    ]

    win1 = MapWindow("TEST-LINE-1", stops1)
    win1.show()
    pause("\n[SCENARIO 1] Check map markers appear correctly. Press ENTER to continue.")

    win1.close()

    # --------------------------------------------------------
    # TEST SCENARIO 2 – Long line with many markers
    # --------------------------------------------------------
    print("Running Scenario 2: Many-stops test...")
    stops2 = [
        (str(200+i), 39.57 + i * 0.001, 2.65 + i * 0.001, f"Stop {i}")
        for i in range(10)
    ]

    win2 = MapWindow("TEST-LINE-2", stops2)
    win2.show()
    pause("\n[SCENARIO 2] Verify the map handles many markers. Press ENTER to continue.")

    win2.close()

    # --------------------------------------------------------
    # TEST SCENARIO 3 – Very close locations (overlapping markers)
    # --------------------------------------------------------
    print("Running Scenario 3: Overlapping markers...")
    stops3 = [
        ("301", 39.572100, 2.650100, "Cluster A"),
        ("302", 39.572110, 2.650110, "Cluster B"),
        ("303", 39.572120, 2.650120, "Cluster C"),
    ]

    win3 = MapWindow("TEST-LINE-CLUSTER", stops3)
    win3.show()
    pause("\n[SCENARIO 3] Check cluster behavior. Press ENTER to finish.")

    win3.close()

    print("\nAll scenarios completed successfully.")
    time.sleep(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # WebEngine permissions
    profile = QWebEngineProfile.defaultProfile()
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)

    run_test_scenarios()
    sys.exit(app.exec())
