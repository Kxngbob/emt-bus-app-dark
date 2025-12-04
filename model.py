from datetime import datetime
from api_client import ApiClient
import re


class BusModel:
    """
    Middle layer between UI and API.
    Handles formatting, lookups and EMT-specific normalization.
    """

    def __init__(self):
        self.api = ApiClient()
        self.last_stop = None

        # Load line colors for Tab 1
        try:
            self.colors = self.api.get_lines()
        except Exception:
            self.colors = {}

    # ----------------------------------------------------
    # Normalization helpers
    # ----------------------------------------------------
    def _normalize(self, code: str) -> str:
        """
        EMT uses:
        - 'A1', 'A2' (letter + number)
        - '3', '15', '30' (numbers)
        Normalize codes so lookups match.
        """
        if not code:
            return ""

        code = str(code).strip()

        # Airport and letter lines (A1, A2...)
        if code[0].isalpha():
            return code.upper()

        # Pure numeric lines
        digits = re.sub(r"\D", "", code)
        return str(int(digits)) if digits else code

    # ----------------------------------------------------
    # TAB 1 — Arrivals per stop
    # ----------------------------------------------------
    def fetch_arrivals(self, stop_id):
        """
        Fetch arrivals, attach line colors and format result
        for the UI in Tab 1.
        """
        arrivals = self.api.get_arrivals(stop_id)
        if not arrivals:
            raise LookupError("No arrivals for this stop.")

        formatted = []

        for line, dest, eta in arrivals:
            norm = self._normalize(line)
            color = "#6b7280"  # default grey

            # Match line color from EMT line list
            for key, value in self.colors.items():
                if self._normalize(key) == norm:
                    color = value if value.startswith("#") else f"#{value}"
                    break

            formatted.append({
                "line": line,
                "destination": dest,
                "eta": f"{eta} min",
                "color": color
            })

        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "data": formatted
        }

    # ----------------------------------------------------
    # TAB 2 — Sublines (first click)
    # ----------------------------------------------------
    def get_sublines(self, line_id: int):
        """
        Retrieve sublines for a given line.
        """
        return self.api.get_sublines(line_id)

    # ----------------------------------------------------
    # TAB 2 — Directions for a subline (second click)
    # ----------------------------------------------------
    def get_directions(self, subline_id: int):
        """
        Retrieve directions/head-signs for a given subline.
        """
        return self.api.get_directions_for_subline(subline_id)

    # ----------------------------------------------------
    # MAP — Route stops for line + trip
    # ----------------------------------------------------
    def get_route_stops(self, line_id: int, trip_id: int):
        """
        Returns a list of stops formatted for the map:
        [
            (stop_code, lat, lon, name),
            ...
        ]
        """
        raw_stops = self.api.get_route_stops(line_id, trip_id)
        stops = []

        for s in raw_stops:
            stop_code = s.get("stopCode") or s.get("stopGtfsId") or str(s.get("id"))
            name = s.get("stopName") or s.get("stopDesc") or stop_code

            try:
                lat = float(s.get("stopLat"))
                lon = float(s.get("stopLon"))
            except (TypeError, ValueError):
                # Skip any stop without valid coordinates
                continue

            stops.append((stop_code, lat, lon, name))

        return stops

    # ----------------------------------------------------
    # MAP — Route shape for line + trip
    # ----------------------------------------------------
    def get_route_shape(self, line_id: int, trip_id: int):
        """
        Returns list of (lat, lon) tuples for the route polyline.
        """
        raw_shape = self.api.get_route_shape(line_id, trip_id)
        coords = []

        for p in raw_shape:
            try:
                lat = float(p.get("latitude"))
                lon = float(p.get("longitude"))
            except (TypeError, ValueError):
                continue
            coords.append((lat, lon))

        return coords
