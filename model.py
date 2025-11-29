from datetime import datetime
from api_client import ApiClient
import re


class BusModel:

    def __init__(self):
        self.api = ApiClient()
        self.last_stop = None

        # Load line colors for Tab 1 (timestr uses only numeric/letter codes)
        try:
            self.colors = self.api.get_lines()
        except:
            self.colors = {}

    # ----------------------------------------------------
    # Normalize codes used by EMT
    # ----------------------------------------------------
    def _normalize(self, code: str) -> str:
        if not code:
            return ""

        code = str(code).strip()

        # Lines like A1, A2, A32...
        if code[0].isalpha():
            return code.upper()

        # Numeric-only (1, 2, 3, 30...)
        digits = re.sub(r"\D", "", code)
        return str(int(digits)) if digits else code

    # ----------------------------------------------------
    # Tab 1: Arrivals lookup
    # ----------------------------------------------------
    def fetch_arrivals(self, stop_id):
        arrivals = self.api.get_arrivals(stop_id)
        if not arrivals:
            raise LookupError("No arrivals for this stop.")

        formatted = []

        for line, dest, eta in arrivals:
            norm = self._normalize(line)
            color = "#6b7280"  # default grey

            # Match with EMT line colors
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
    # Tab 2: SUBLINES
    # ----------------------------------------------------
    def get_sublines(self, line_id: int):
        """
        Returns list of:
        {
            "subLineId": 1046,
            "longName": "...",
            "shortName": "...",
            "externalCode": 1,
            "lineId": 19
        }
        """
        return self.api.get_sublines(line_id)

    # ----------------------------------------------------
    # Tab 2: DIRECTIONS for a subline
    # ----------------------------------------------------
    def get_directions(self, subline_id: int):
        """
        Returns list of:
        {
            "tripId": 49,
            "headSign": "UIB i Parc Bit",
            "directionId": 1,
            "jday": null
        }
        """
        return self.api.get_directions_for_subline(subline_id)
