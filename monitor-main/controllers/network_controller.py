import threading
from typing import Dict, Any, List, Callable
from models.network_model import NetworkModel
from services.mikrotik_service import MikrotikService

class NetworkController:
    def __init__(self, model: NetworkModel, mk_service: MikrotikService):
        self.model = model
        self.mk_service = mk_service
        self.is_scanning = False

    def trigger_lan_scan(self, on_device_found: Callable[[List[Dict[str, Any]]], None], on_complete: Callable[[], None]) -> None:
        """
        Runs network device scanner in a background thread.
        """
        if self.is_scanning:
            return
        self.is_scanning = True
        
        def _scan():
            try:
                # Poll leases and arp
                arp_data = self.mk_service.get_arp_table()
                dhcp_data = self.mk_service.get_dhcp_leases()
                
                devices = []
                # Simple mapping
                mac_to_host = {d.get("mac-address"): d.get("host-name", "Unknown") for d in dhcp_data if d.get("mac-address")}
                
                for entry in arp_data:
                    mac = entry.get("mac-address")
                    if mac:
                        hostname = mac_to_host.get(mac, "Dispositivo LAN")
                        devices.append({
                            "ip": entry.get("address", "0.0.0.0"),
                            "hostname": hostname,
                            "mac": mac,
                            "interface": entry.get("interface", "unknown")
                        })
                
                # Update model on main thread or via callback
                self.model.active_devices = devices
                on_device_found(devices)
            except Exception as e:
                print(f"[NetworkController] Error scanning: {e}")
            finally:
                self.is_scanning = False
                on_complete()
                
        threading.Thread(target=_scan, daemon=True).start()
