from datetime import datetime
from api_client import ApiClient


class BusModel:
    def __init__(self):
        self.api = ApiClient()
        self.last_stop = None
        self.colors = self.api.get_lines()

    def fetch_arrivals(self, stop_id):
        arrivals = self.api.get_arrivals(stop_id)
        if not arrivals:
            raise LookupError("No arrivals available for this stop.")
        self.last_stop = stop_id

        formatted = []
        for line, dest, eta in arrivals:
            formatted.append({
                "line": line,
                "destination": dest,
                "eta": f"{eta} min",
                "color": self.colors.get(line, "#6b7280")
            })
        return {"timestamp": datetime.now().strftime("%H:%M:%S"), "data": formatted}
