import os
import requests


class ApiClient:
    """
    Low-level HTTP client for the EMT MAAS API.
    Handles token loading, headers, and all API requests.
    """

    BASE = "https://www.emtpalma.cat/maas/api/v1/agency"
    TIMEOUT = 10

    def __init__(self):
        # Load the Bearer token from token.txt
        self.token = self._load_token()

    # ----------------------------------------------------
    # TOKEN / HEADERS
    # ----------------------------------------------------
    def _load_token(self):
        """
        Reads token.txt and returns its content.
        Required for all EMT API requests.
        """
        if not os.path.exists("token.txt"):
            raise RuntimeError("Missing token.txt file.")

        with open("token.txt", "r", encoding="utf-8") as f:
            token = f.read().strip()

        if not token:
            raise RuntimeError("token.txt is empty.")

        return token

    def _headers(self):
        """
        HTTP headers with the authorization token.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        }

    # ----------------------------------------------------
    # LINE LIST (raw) — used for Tab 2
    # ----------------------------------------------------
    def get_lines_raw(self):
        url = f"{self.BASE}/lines/"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("lines", []) if isinstance(data, dict) else data

    # ----------------------------------------------------
    # LINE COLORS (for Tab 1)
    # ----------------------------------------------------
    def get_lines(self):
        """
        Return dict mapping line code → line color.
        Used to render colored badges in Tab 1.
        """
        url = f"{self.BASE}/lines/"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, dict):
            data = data.get("lines", [])

        colors = {}

        for line in data:
            code = line.get("code") or line.get("shortName") or ""
            if not code:
                continue

            # EMT provides either full hex (#123456) or raw hex ("123456")
            raw_color = line.get("color")
            if raw_color and raw_color.startswith("#"):
                color = raw_color
            else:
                rc = line.get("routeColor")
                color = f"#{rc}" if rc else "#aaaaaa"

            colors[code] = color

        return colors

    # ----------------------------------------------------
    # STOP ARRIVALS — Tab 1
    # ----------------------------------------------------
    def get_arrivals(self, stop_id):
        """
        Calls /stops/{id}/timestr and parses the arrivals.
        """
        if not stop_id.isdigit():
            raise ValueError("Stop number must be numeric.")

        url = f"{self.BASE}/stops/{stop_id}/timestr"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)

        if resp.status_code == 404:
            raise LookupError("Stop not found.")
        if resp.status_code == 401:
            raise PermissionError("Invalid token.")

        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, list):
            raise ValueError("Unexpected format returned by server.")

        arrivals = []
        for entry in data:
            line_name = str(entry.get("lineCode", "?"))

            for vehicle in entry.get("vehicles", []):
                dest = vehicle.get("destination", "Unknown")
                seconds = vehicle.get("seconds", 0)
                eta_min = max(0, round(seconds / 60))
                arrivals.append((line_name, dest, eta_min))

        return arrivals

    # ----------------------------------------------------
    # SUBLINES (Tab 2 — first click)
    # ----------------------------------------------------
    def get_sublines(self, line_id):
        url = f"{self.BASE}/lines/{line_id}/sublines"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ----------------------------------------------------
    # DIRECTIONS FOR SUBLINE (Tab 2 — second click)
    # ----------------------------------------------------
    def get_directions_for_subline(self, subline_id):
        url = f"{self.BASE}/lines/directions-subline"
        params = {"subLineId": subline_id}
        resp = requests.get(url, headers=self._headers(),
                            params=params, timeout=self.TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ----------------------------------------------------
    # ROUTE STOPS FOR TRIP (used by map)
    # ----------------------------------------------------
    def get_route_stops(self, line_id, trip_id):
        """
        Calls:
        /lines/{lineId}/stops?tripId=...&isLine=0&isLineNearStop=0&both=1
        Returns raw list of stops.
        """
        url = f"{self.BASE}/lines/{line_id}/stops"
        params = {
            "tripId": trip_id,
            "isLine": 0,
            "isLineNearStop": 0,
            "both": 1,
        }
        resp = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    # ----------------------------------------------------
    # ROUTE SHAPE FOR TRIP (used by map)
    # ----------------------------------------------------
    def get_route_shape(self, line_id, trip_id):
        """
        Calls:
        /lines/{lineId}/shape?tripId=...
        Returns raw list of shape points.
        """
        url = f"{self.BASE}/lines/{line_id}/shape"
        params = {"tripId": trip_id}
        resp = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
