from typing import Dict, Any, List

class DiagnosticsModel:
    def __init__(self):
        self.is_running = False
        self.progress = 0.0
        self.results: List[Dict[str, Any]] = []
        self.last_report_path = ""
        
    def reset(self) -> None:
        self.is_running = True
        self.progress = 0.0
        self.results = []
        self.last_report_path = ""

    def add_result(self, name: str, status: str, value: str, notes: str) -> None:
        """
        status should be: "PASS", "WARN", or "FAIL"
        """
        self.results.append({
            "name": name,
            "status": status,
            "value": value,
            "notes": notes
        })

    def update_progress(self, progress: float) -> None:
        self.progress = min(100.0, max(0.0, progress))
