import os
import requests


class ApiClient:
    BASE = "https://www.emtpalma.cat/maas/api/v1/agency"
    TIMEOUT = 10

    def __init__(self):
        self.token = self._load_token()

    def _load_token(self):
        """Load the API token from token.txt."""
        if not os.path.exists("token.txt"):
            raise RuntimeError("Missing token.txt file.")
        with open("token.txt", "r", encoding="utf-8") as f:
            return f.read().strip()

    def _headers(self):
        """Basic headers for EMT Palma API."""
        return {"Authorization": f"Bearer {self.token}"}

    def get_lines(self):
        """Retrieve all bus lines and their colors."""
        url = f"{self.BASE}/lines/"
        response = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            data = data.get("lines", [])
        return {str(line.get("shortName")): line.get("color", "#aaaaaa") for line in data}

    def get_arrivals(self, stop_id):
        """Retrieve arrival times for a given stop."""
        if not stop_id.isdigit():
            raise ValueError("Stop number must be numeric.")

        url = f"{self.BASE}/stops/{stop_id}/lines"
        response = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)

        if response.status_code == 404:
            raise LookupError("Stop not found.")
        if response.status_code == 401:
            raise PermissionError("Invalid or expired token.")
        response.raise_for_status()

        data = response.json()

        # handle both dict or list responses
        if isinstance(data, list):
            lines_data = data
        elif isinstance(data, dict):
            lines_data = data.get("lines", [])
        else:
            lines_data = []

        arrivals = []
        for line in lines_data:
            line_name = line.get("shortName", "?")
            destination = line.get("destination", {}).get("name", "Unknown")
            for nxt in line.get("nextArrivals", []):
                eta = nxt.get("arrivalInMinutes", "?")
                arrivals.append((line_name, destination, eta))

        return arrivals
