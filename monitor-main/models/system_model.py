from typing import Dict, Any, List

class SystemModel:
    def __init__(self):
        # Health state: "GREEN", "YELLOW", "RED"
        self.health_state = "GREEN"
        self.health_description = "Sistema Operativo"
        
        self.ping_avg_ms = 0.0
        self.ping_loss_percent = 0
        self.gateway_ping = 0.0
        
        self.firewall_drops_total = 0
        self.log_message = ""
        self.recent_logs: List[str] = []
        self.active_alerts: List[Dict[str, Any]] = []

    def update_from_payload(self, payload: Dict[str, Any]) -> None:
        self.ping_avg_ms = payload.get("ping_avg_ms", 0.0)
        self.ping_loss_percent = payload.get("ping_loss_percent", 0)
        self.gateway_ping = payload.get("gateway_ping", 0.0)
        
        self.firewall_drops_total = payload.get("firewall_drops_total", 0)
        self.log_message = payload.get("log_message", "")
        
        if self.log_message and (not self.recent_logs or self.recent_logs[-1] != self.log_message):
            self.recent_logs.append(self.log_message)
            if len(self.recent_logs) > 30:
                self.recent_logs.pop(0)
                
        # Calculate health status based on specific guidelines
        self._calculate_health(payload)

    def _calculate_health(self, payload: Dict[str, Any]) -> None:
        cpu_load = payload.get("cpu_load", 0)
        
        # Calculate memory usage
        free_mem = payload.get("free_memory", 0)
        total_mem = payload.get("total_memory", 1024)
        ram_usage_pct = 0.0
        if total_mem > 0:
            ram_usage_pct = ((total_mem - free_mem) / total_mem) * 100.0
            
        wan1_speed = payload.get("wan1_rx", 0) + payload.get("wan1_tx", 0)
        wan2_speed = payload.get("wan2_rx", 0) + payload.get("wan2_tx", 0)
        
        wan_drops = payload.get("wan_drops", 0)
        ping_loss = payload.get("ping_loss_percent", 0)
        temp = payload.get("temperature", 0)
        
        # 1. Critical Errors (RED)
        # - No internet (ping loss 100%)
        # - Both WANs down (speeds are 0 and ping loss is 100%)
        # - Router disconnected (represented by empty/0 payload values when not mocking)
        if ping_loss >= 100 or (wan1_speed == 0 and wan2_speed == 0 and ping_loss >= 90):
            self.health_state = "RED"
            self.health_description = "✖ Error Crítico: Sin Internet"
        elif payload.get("cpu_load") is None or total_mem == 1024 and free_mem == 0:
            self.health_state = "RED"
            self.health_description = "✖ Error Crítico: Router Desconectado"
        
        # 2. Warning Alerts (YELLOW)
        # - WAN1 or WAN2 speed is zero (one WAN down)
        # - WAN drops detected
        # - CPU >= 80%
        # - RAM >= 85%
        # - High Temperature (> 75 degrees)
        elif wan1_speed == 0 or wan2_speed == 0 or wan_drops > 0 or cpu_load >= 80 or ram_usage_pct >= 85 or temp >= 75:
            self.health_state = "YELLOW"
            degradations = []
            if wan1_speed == 0: degradations.append("WAN1 Inactiva")
            if wan2_speed == 0: degradations.append("WAN2 Inactiva")
            if cpu_load >= 80: degradations.append(f"CPU Alta ({cpu_load}%)")
            if ram_usage_pct >= 85: degradations.append(f"RAM Alta ({ram_usage_pct:.0f}%)")
            if temp >= 75: degradations.append(f"Temp Alta ({temp}°C)")
            if wan_drops > 0: degradations.append("Drops en WAN")
            
            self.health_description = "⚠ Advertencia: " + ", ".join(degradations)
            
        # 3. All OK (GREEN)
        # - WAN1 active and WAN2 active
        # - CPU < 80%
        # - RAM < 85%
        else:
            self.health_state = "GREEN"
            self.health_description = "✓ Sistema Operativo"
            
    def update_alerts_list(self, alerts: List[Dict[str, Any]]) -> None:
        self.active_alerts = alerts
