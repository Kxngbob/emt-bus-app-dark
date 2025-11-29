from datetime import datetime
from api_client import ApiClient
import re


class BusModel:

    def __init__(self):
        self.api = ApiClient()
        self.last_stop = None

        # Load line colors for Tab 1
        try:
            self.colors = self.api.get_lines()
        except:
            self.colors = {}

    # ----------------------------------------------------
    # Normalize to match EMT logic
    # ----------------------------------------------------
    def _normalize(self, code: str) -> str:
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
    # Fetch arrivals for Tab 1
    # ----------------------------------------------------
    def fetch_arrivals(self, stop_id):

        arrivals = self.api.get_arrivals(stop_id)
        if not arrivals:
            raise LookupError("No arrivals for this stop.")

        formatted = []

        for line, dest, eta in arrivals:

            norm = self._normalize(line)
            color = "#6b7280"

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
