from datetime import datetime
from api_client import ApiClient
import re


class BusModel:
    """Connects API client with view logic."""
    def __init__(self):
        self.api = ApiClient()
        self.last_stop = None
        self.colors = self.api.get_lines()

    def _normalize(self, code: str) -> str:
        """Strip non-digits, pad to 2 digits."""
        digits = re.sub(r"\D", "", code or "")
        return digits.zfill(2) if digits else code

    def fetch_arrivals(self, stop_id):
        """Fetch arrivals and prepare them for display."""
        arrivals = self.api.get_arrivals(stop_id)
        if not arrivals:
            raise LookupError("No arrivals available for this stop.")
        self.last_stop = stop_id

        formatted = []
        for line, dest, eta in arrivals:
            norm = self._normalize(line)

            # Normalize all color keys once for consistent lookup
            color = "#6b7280"
            for key, val in self.colors.items():
                if self._normalize(key) == norm:
                    color = val if val.startswith("#") else f"#{val}"
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
