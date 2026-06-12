from typing import Dict, Any, List

class NetworkModel:
    def __init__(self, max_history_len: int = 60):
        self.max_history_len = max_history_len
        
        # Real-time traffic rates
        self.wan1_rx = 0
        self.wan1_tx = 0
        self.wan2_rx = 0
        self.wan2_tx = 0
        
        # Historical lists for charts (Bps or Kbps)
        self.history_wan1_rx: List[float] = []
        self.history_wan1_tx: List[float] = []
        self.history_wan2_rx: List[float] = []
        self.history_wan2_tx: List[float] = []
        
        # VPN statistics
        self.vpn_count = 0
        self.vpn_l2tp = 0
        self.vpn_ovpn = 0
        self.vpn_sstp = 0
        self.vpn_pptp = 0
        self.vpn_profiles_detail: Dict[str, int] = {}
        
        # Active connections count
        self.active_connections = 0
        self.dhcp_leases = 0
        self.queue_count = 0
        
        # Top consumer devices list
        self.top_consumers: List[Dict[str, Any]] = []
        self.active_devices: List[Dict[str, Any]] = []

    def update_from_payload(self, payload: Dict[str, Any]) -> None:
        self.wan1_rx = payload.get("wan1_rx", 0)
        self.wan1_tx = payload.get("wan1_tx", 0)
        self.wan2_rx = payload.get("wan2_rx", 0)
        self.wan2_tx = payload.get("wan2_tx", 0)
        
        # Append histories (convert bps to Kbps for better chart reading)
        self.history_wan1_rx.append(self.wan1_rx / 1000.0)
        self.history_wan1_tx.append(self.wan1_tx / 1000.0)
        self.history_wan2_rx.append(self.wan2_rx / 1000.0)
        self.history_wan2_tx.append(self.wan2_tx / 1000.0)
        
        # Constrain history size
        if len(self.history_wan1_rx) > self.max_history_len:
            self.history_wan1_rx.pop(0)
            self.history_wan1_tx.pop(0)
            self.history_wan2_rx.pop(0)
            self.history_wan2_tx.pop(0)
            
        self.vpn_count = payload.get("vpn_count", 0)
        self.vpn_l2tp = payload.get("vpn_l2tp", 0)
        self.vpn_ovpn = payload.get("vpn_ovpn", 0)
        self.vpn_sstp = payload.get("vpn_sstp", 0)
        self.vpn_pptp = payload.get("vpn_pptp", 0)
        self.vpn_profiles_detail = payload.get("vpn_profiles_detail", {})
        
        self.active_connections = payload.get("active_connections", 0)
        self.dhcp_leases = payload.get("dhcp_leases", 0)
        self.queue_count = payload.get("queue_count", 0)
        self.top_consumers = payload.get("top_consumers", [])
