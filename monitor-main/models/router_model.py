from typing import Dict, Any

class RouterModel:
    def __init__(self):
        # Hardware specs / usage
        self.cpu_load = 0
        self.free_memory = 0
        self.total_memory = 1024
        self.hdd_free = 0
        self.hdd_total = 1024
        
        # System health indicators
        self.temperature = 0
        self.voltage = 0.0
        self.uptime = "unknown"
        
        # Ports and link errors
        self.interface_errors: Dict[str, int] = {}
        
    def update_from_payload(self, payload: Dict[str, Any]) -> None:
        self.cpu_load = payload.get("cpu_load", 0)
        self.free_memory = payload.get("free_memory", 0)
        self.total_memory = payload.get("total_memory", 1024)
        self.hdd_free = payload.get("hdd_free", 0)
        self.hdd_total = payload.get("hdd_total", 1024)
        self.temperature = payload.get("temperature", 0)
        self.voltage = payload.get("voltage", 0.0)
        self.uptime = payload.get("uptime", "unknown")
        self.interface_errors = payload.get("interface_errors", {})

    @property
    def ram_usage_percent(self) -> float:
        if self.total_memory <= 0:
            return 0.0
        used = self.total_memory - self.free_memory
        return round((used / self.total_memory) * 100.0, 1)

    @property
    def hdd_usage_percent(self) -> float:
        if self.hdd_total <= 0:
            return 0.0
        used = self.hdd_total - self.hdd_free
        return round((used / self.hdd_total) * 100.0, 1)
