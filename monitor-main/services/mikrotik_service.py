import logging
import random
import time
import math
from typing import Dict, Any, List, Optional
import routeros_api

class MikrotikService:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.api = None
        self.is_mock = False
        
        self.prev_time = time.time()
        self.prev_bytes = {
            "v_2689": {"rx": 1000000000, "tx": 500000000},
            "WAN2-ether3": {"rx": 500000000, "tx": 250000000},
            "ether1": {"rx": 200000000, "tx": 200000000},
            "ether2": {"rx": 300000000, "tx": 400000000},
            "bridge": {"rx": 800000000, "tx": 800000000}
        }
        self.mock_start_time = time.time()
        self.mock_fw_drops = 1450
        
    def connect(self) -> bool:
        if self.is_mock:
            return True
        try:
            logging.info(f"Connecting to MikroTik at {self.host}...")
            self.connection = routeros_api.RouterOsApiPool(
                self.host, 
                username=self.username, 
                password=self.password, 
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            self.is_mock = False
            logging.info("Connected successfully to MikroTik.")
            return True
        except Exception as e:
            logging.warning(f"Failed to connect to MikroTik ({e}). Falling back to MOCK MODE.")
            self.is_mock = True
            return True

    def disconnect(self) -> None:
        if self.connection and not self.is_mock:
            try:
                self.connection.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting: {e}")
        self.connection = None
        self.api = None

    def get_system_resource(self) -> Dict[str, Any]:
        if self.is_mock:
            # Simulate CPU/RAM fluctuations. Let's make it occasionally cross thresholds
            # to test Yellow health warning! (CPU > 80% or RAM > 85%)
            t = time.time() - self.mock_start_time
            # Base load: 20-30%, fluctuates with sine wave + random noise. Spikes occasionally
            cpu_base = 25 + 15 * math.sin(t / 60.0) + random.uniform(-5, 5)
            if int(t) % 120 > 100: # Periodic spike every 2 minutes for 20 seconds
                cpu_base = 82 + random.uniform(-2, 2)
            
            # Memory simulation (Total 1GB, Free fluctuates around 250MB - 120MB)
            total_mem = 1073741824 # 1 GB
            free_mem = int(250000000 + 50000000 * math.sin(t / 45.0) + random.uniform(-5000000, 5000000))
            if int(t) % 150 > 130: # Periodic memory stress (free RAM goes down, usage > 85%)
                free_mem = int(total_mem * 0.12) # 88% usage
            
            total_hdd = 134217728 # 128 MB
            free_hdd = int(total_hdd * 0.65 + random.uniform(-100000, 100000))
            
            uptime_sec = int(t)
            days = uptime_sec // 86400
            hours = (uptime_sec % 86400) // 3600
            mins = (uptime_sec % 3600) // 60
            secs = uptime_sec % 60
            uptime_str = f"{days}d {hours:02d}:{mins:02d}:{secs:02d}"

            return {
                "cpu-load": str(max(1, min(100, int(cpu_base)))),
                "free-memory": str(free_mem),
                "total-memory": str(total_mem),
                "free-hdd-space": str(free_hdd),
                "total-hdd-space": str(total_hdd),
                "uptime": uptime_str
            }
        
        try:
            res = self.api.get_resource('/system/resource').get()
            if res:
                return res[0]
        except Exception as e:
            logging.error(f"Error fetching system resources: {e}")
            self.connect() # try to reconnect
        return {}

    def get_interfaces(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            now = time.time()
            dt = now - self.prev_time
            self.prev_time = now
            
            # Simulate byte increment based on simulated speed (bps)
            # WAN1: ~10Mbps to 70Mbps Rx, WAN2: ~5Mbps to 30Mbps Rx
            t = now - self.mock_start_time
            wan1_rx_bps = (35 + 20 * math.sin(t / 30.0) + random.uniform(-5, 5)) * 1_000_000
            wan1_tx_bps = (5 + 3 * math.sin(t / 30.0) + random.uniform(-1, 1)) * 1_000_000
            
            wan2_rx_bps = (15 + 10 * math.cos(t / 45.0) + random.uniform(-2, 2)) * 1_000_000
            wan2_tx_bps = (2 + 1 * math.cos(t / 45.0) + random.uniform(-0.5, 0.5)) * 1_000_000
            
            # Simulate occasional link drops to WAN2 or WAN1
            if int(t) % 300 > 280: # WAN2 drop for 20s
                wan2_rx_bps = 0
                wan2_tx_bps = 0
            
            speeds = {
                "v_2689": {"rx": wan1_rx_bps, "tx": wan1_tx_bps},
                "WAN2-ether3": {"rx": wan2_rx_bps, "tx": wan2_tx_bps},
                "ether1": {"rx": 5_000_000, "tx": 2_000_000},
                "ether2": {"rx": 10_000_000, "tx": 8_000_000},
                "bridge": {"rx": wan1_rx_bps + wan2_rx_bps, "tx": wan1_tx_bps + wan2_tx_bps}
            }
            
            interfaces_list = []
            for name, sp in speeds.items():
                # Add bytes
                self.prev_bytes[name]["rx"] += int(sp["rx"] * dt / 8)
                self.prev_bytes[name]["tx"] += int(sp["tx"] * dt / 8)
                interfaces_list.append({
                    "name": name,
                    "rx-byte": str(self.prev_bytes[name]["rx"]),
                    "tx-byte": str(self.prev_bytes[name]["tx"]),
                    "rx-drop": "0" if name != "v_2689" else str(int(t // 100))
                })
            return interfaces_list

        try:
            return self.api.get_resource('/interface').get()
        except Exception as e:
            logging.error(f"Error fetching interfaces: {e}")
            self.connect()
        return []

    def get_vpn_secrets(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"name": "user_sales1", "profile": "Standard"},
                {"name": "user_sales2", "profile": "Standard"},
                {"name": "user_dev1", "profile": "VIP"},
                {"name": "user_dev2", "profile": "VIP"},
                {"name": "user_exec1", "profile": "Executive"},
                {"name": "user_guest", "profile": "Guest"}
            ]
        try:
            return self.api.get_resource('/ppp/secret').get()
        except Exception as e:
            logging.error(f"Error fetching VPN secrets: {e}")
        return []

    def get_vpn_active(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            # Randomly connect/disconnect active VPN users
            t = time.time() - self.mock_start_time
            active_users = []
            if t % 60 < 45:
                active_users.append({"name": "user_sales1", "service": "l2tp"})
            if t % 90 < 70:
                active_users.append({"name": "user_dev1", "service": "ovpn"})
            if t % 120 < 90:
                active_users.append({"name": "user_exec1", "service": "sstp"})
            if t % 80 < 50:
                active_users.append({"name": "user_sales2", "service": "pptp"})
            return active_users
            
        try:
            return self.api.get_resource('/ppp/active').get()
        except Exception as e:
            logging.error(f"Error fetching active VPNs: {e}")
        return []

    def get_arp_table(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"address": "10.24.0.50", "mac-address": "00:1A:2B:3C:4D:5E", "interface": "bridge"},
                {"address": "10.24.0.51", "mac-address": "00:1A:2B:3C:4D:5F", "interface": "bridge"},
                {"address": "10.24.0.100", "mac-address": "12:34:56:78:9A:BC", "interface": "bridge"},
                {"address": "10.24.0.101", "mac-address": "12:34:56:78:9A:BD", "interface": "bridge"},
                {"address": "10.24.0.150", "mac-address": "AA:BB:CC:DD:EE:FF", "interface": "bridge"}
            ]
        try:
            return self.api.get_resource('/ip/arp').get()
        except Exception as e:
            logging.error(f"Error fetching ARP table: {e}")
        return []

    def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"address": "10.24.0.50", "host-name": "Sales-PC1", "mac-address": "00:1A:2B:3C:4D:5E", "server": "dhcp_sales"},
                {"address": "10.24.0.51", "host-name": "Sales-PC2", "mac-address": "00:1A:2B:3C:4D:5F", "server": "dhcp_sales"},
                {"address": "10.24.0.100", "host-name": "Dev-Laptop1", "mac-address": "12:34:56:78:9A:BC", "server": "dhcp_dev"},
                {"address": "10.24.0.101", "host-name": "Dev-Laptop2", "mac-address": "12:34:56:78:9A:BD", "server": "dhcp_dev"},
                {"address": "10.24.0.150", "host-name": "CEO-iPad", "mac-address": "AA:BB:CC:DD:EE:FF", "server": "dhcp_exec"}
            ]
        try:
            return self.api.get_resource('/ip/dhcp-server/lease').get()
        except Exception as e:
            logging.error(f"Error fetching DHCP leases: {e}")
        return []

    def get_firewall_drops(self) -> int:
        if self.is_mock:
            # Slowly increment attacks blocked
            self.mock_fw_drops += random.choice([0, 0, 1, 0, 2, 0])
            return self.mock_fw_drops
        try:
            fw_drops = 0
            filters = self.api.get_resource('/ip/firewall/filter').get()
            for f in filters:
                if f.get('action') == 'drop':
                    fw_drops += int(f.get('packets', 0))
            return fw_drops
        except Exception as e:
            logging.error(f"Error fetching firewall filter drops: {e}")
        return 0

    def get_active_connections_count(self) -> int:
        if self.is_mock:
            t = time.time() - self.mock_start_time
            # Flucuates around 150 connections
            return int(150 + 40 * math.sin(t / 20.0) + random.uniform(-10, 10))
        try:
            conns = self.api.get_resource('/ip/firewall/connection').get()
            return len(conns)
        except Exception as e:
            logging.error(f"Error fetching active connections: {e}")
        return 0

    def get_queue_count(self) -> int:
        if self.is_mock:
            return 3
        try:
            queues = self.api.get_resource('/queue/simple').get()
            return len(queues)
        except Exception as e:
            logging.error(f"Error fetching simple queues: {e}")
        return 0

    def get_logs(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            # Simulate a live event log feed
            t = time.time() - self.mock_start_time
            logs = [
                {"time": "08:30:15", "message": "user admin logged in via local", "topics": "info,account"},
                {"time": "08:32:00", "message": "DHCP lease IP 10.24.0.101 assigned to Dev-Laptop2", "topics": "info,dhcp"},
            ]
            if int(t) % 60 > 55:
                logs.append({"time": "09:00:01", "message": "VPN user_sales1 connected via L2TP", "topics": "info,ppp,account"})
            if int(t) % 90 > 85:
                logs.append({"time": "09:02:14", "message": "WAN2 connection speed degraded, ping > 200ms", "topics": "warning,route"})
            if int(t) % 120 > 115:
                logs.append({"time": "09:05:40", "message": "Firewall blocked syn flood portscan from 198.51.100.42", "topics": "warning,firewall"})
            return logs

        try:
            return self.api.get_resource('/log').get()
        except Exception as e:
            logging.error(f"Error fetching logs: {e}")
        return []

    def get_system_health(self) -> Dict[str, Any]:
        if self.is_mock:
            t = time.time() - self.mock_start_time
            # Temperature around 42 degrees, voltage around 24V
            temp = int(42 + 5 * math.sin(t / 100.0) + random.uniform(-1, 1))
            # Test temperature degradation (temp > 75)
            if int(t) % 240 > 200:
                temp = 79
            
            volt = int(24 + random.uniform(-0.2, 0.2))
            return {
                "temperature": temp,
                "voltage": volt
            }
            
        temp = 0
        volt = 0
        try:
            health = self.api.get_resource('/system/health').get()
            for h in health:
                if 'temperature' in h.get('name', ''): 
                    temp = int(h.get('value', 0))
                if 'voltage' in h.get('name', ''): 
                    volt = int(h.get('value', 0))
        except Exception as e:
            logging.error(f"Error fetching system health: {e}")
        return {"temperature": temp, "voltage": volt}

    def get_ethernet_errors(self) -> Dict[str, int]:
        if self.is_mock:
            t = time.time() - self.mock_start_time
            # Ethernet errors simulated on ether1 under stress
            if int(t) % 180 > 150:
                return {"ether1": 4}
            return {}
        
        errors = {}
        try:
            eth_stats = self.api.get_resource('/interface/ethernet').get()
            for eth in eth_stats:
                e_name = eth.get('name')
                e_err = int(eth.get('rx-error', 0)) + int(eth.get('tx-error', 0)) + \
                        int(eth.get('fcs-error', 0)) + int(eth.get('align-error', 0))
                if e_err > 0: 
                    errors[e_name] = e_err
        except Exception as e:
            logging.error(f"Error fetching ethernet interface errors: {e}")
        return errors
