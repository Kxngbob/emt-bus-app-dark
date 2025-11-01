import os
import requests


class ApiClient:
    """Simple EMT Palma API client for student project."""
    BASE = "https://www.emtpalma.cat/maas/api/v1/agency"
    TIMEOUT = 10

    def __init__(self):
        self.token = self._load_token()

  
    def _load_token(self):
        if not os.path.exists("token.txt"):
            raise RuntimeError("Missing token.txt file.")
        with open("token.txt", "r", encoding="utf-8") as f:
            token = f.read().strip()
        if not token:
            raise RuntimeError("token.txt is empty.")
        return token

    
    # Build HTTP headers
   
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        }

  
    # Fetch all bus lines and their colors
    
    def get_lines(self):
        """Get all line colors for display."""
        url = f"{self.BASE}/lines/"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            data = data.get("lines", [])
        colors = {}
        for line in data:
            short = str(line.get("shortName", "")).strip()
            color = line.get("color", "#aaaaaa")
            if short:
                colors[short] = color if color.startswith("#") else f"#{color}"
        return colors

    
    # Fetch real-time arrivals using /timestr endpoint
    
    def get_arrivals(self, stop_id):
        """Retrieve live arrivals from /stops/{id}/timestr endpoint."""
        if not stop_id.isdigit():
            raise ValueError("Stop number must be numeric.")

        url = f"{self.BASE}/stops/{stop_id}/timestr"
        resp = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)

        if resp.status_code == 404:
            raise LookupError("Stop not found.")
        if resp.status_code == 401:
            raise PermissionError("Invalid or expired token.")
        resp.raise_for_status()

        data = resp.json()

        #Handle the actual structure from /timestr
        if not isinstance(data, list):
            raise LookupError("Unexpected response format from server.")

        arrivals = []
        for entry in data:
            line_name = str(entry.get("lineCode", "?"))
            for vehicle in entry.get("vehicles", []):
                dest = vehicle.get("destination", "Unknown")
                seconds = vehicle.get("seconds", 0)
                eta_min = round(seconds / 60)
                arrivals.append((line_name, dest, eta_min))

        return arrivals
