import threading
import time
import datetime
import json
import smtplib
import ssl
from email.message import EmailMessage
import pymysql
import logging
from typing import Dict, Any, List, Callable, Optional
from services.mikrotik_service import MikrotikService
from services.ping_service import PingService
from services.logging_service import LoggingService

class MonitoringService:
    def __init__(self, settings: Dict[str, Any], on_update_callback: Callable[[Dict[str, Any]], None]):
        self.settings = settings
        self.on_update = on_update_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Instantiate dependencies
        mk_cfg = settings.get("mikrotik", {})
        self.mk_service = MikrotikService(
            host=mk_cfg.get("host", "10.24.0.1"),
            username=mk_cfg.get("username", "admin"),
            password=mk_cfg.get("password", "")
        )
        self.ping_service = PingService(
            target_ip="8.8.8.8",
            gateway_ip=mk_cfg.get("host", "10.24.0.1")
        )
        self.logging_service = LoggingService(db_config=settings.get("database"))
        
        self.last_email_time = 0.0
        self.prev_time = 0.0
        self.prev_ifaces: Dict[str, Dict[str, int]] = {}
        self.last_speedtest = 0.0
        self.last_scan = 0.0
        
    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.mk_service.connect()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.logging_service.log("info", "Monitoring telemetry service started.")

    def stop(self) -> None:
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.mk_service.disconnect()
        self.logging_service.log("info", "Monitoring telemetry service stopped.")

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        self.settings = new_settings
        mk_cfg = new_settings.get("mikrotik", {})
        self.mk_service.host = mk_cfg.get("host", "10.24.0.1")
        self.mk_service.username = mk_cfg.get("username", "admin")
        self.mk_service.password = mk_cfg.get("password", "")
        self.mk_service.connect() # Reconnect with new settings
        self.ping_service.gateway_ip = mk_cfg.get("host", "10.24.0.1")
        self.logging_service.db_config = new_settings.get("database")

    def send_email_alert(self, subject: str, body: str) -> None:
        conf = self.settings.get("email", {})
        cooldown = conf.get("cooldown", 300)
        now = time.time()
        
        if now - self.last_email_time < cooldown:
            return # Within cooldown period
            
        email_user = conf.get("email_user", "")
        email_pass = conf.get("email_password", "")
        recipient = conf.get("alert_recipient", "")
        
        if not email_user or not email_pass or "PON_AQUI" in email_pass or "Sara2803@*" in email_pass:
            self.logging_service.log("warning", "Skipping email alert: Credentials are not configured in settings.json.")
            return

        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = email_user
            msg['To'] = recipient

            context = ssl.create_default_context()
            with smtplib.SMTP(conf.get("smtp_server", "smtp.gmail.com"), conf.get("smtp_port", 587)) as server:
                server.starttls(context=context)
                server.login(email_user, email_pass)
                server.send_message(msg)
            
            self.logging_service.log("info", f"Alert email successfully sent to {recipient}")
            self.last_email_time = now
        except Exception as e:
            self.logging_service.log("error", f"Error sending alert email: {e}")

    def _run_loop(self) -> None:
        while self.is_running:
            start_time = time.time()
            try:
                self._collect_step()
            except Exception as e:
                self.logging_service.log("error", f"Error in telemetry collection step: {e}")
            
            # Precise sleep to poll every 1s
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 1.0 - elapsed)
            time.sleep(sleep_time)

    def _collect_step(self) -> None:
        now_ts = time.time()
        
        # 1. Fetch system resources
        resources = self.mk_service.get_system_resource()
        cpu_load = int(resources.get("cpu-load", 0))
        free_mem = int(resources.get("free-memory", 0))
        total_mem = int(resources.get("total-memory", 1024))
        free_hdd = int(resources.get("free-hdd-space", 0))
        total_hdd = int(resources.get("total-hdd-space", 1024))
        uptime = resources.get("uptime", "unknown")
        
        # 2. Fetch interface traffic stats
        interfaces = self.mk_service.get_interfaces()
        dt = now_ts - self.prev_time if self.prev_time > 0 else 1.0
        self.prev_time = now_ts
        
        traffic_list = []
        w1_rx_bits = 0; w1_tx_bits = 0
        w2_rx_bits = 0; w2_tx_bits = 0
        wan_drops = 0
        
        current_ifaces = {}
        for i in interfaces:
            name = i.get('name')
            rx = int(i.get('rx-byte', 0))
            tx = int(i.get('tx-byte', 0))
            current_ifaces[name] = {"rx": rx, "tx": tx}
            
            if name in self.prev_ifaces:
                p_rx = self.prev_ifaces[name]["rx"]
                p_tx = self.prev_ifaces[name]["tx"]
                rx_bps = max(0, (rx - p_rx) * 8 / dt)
                tx_bps = max(0, (tx - p_tx) * 8 / dt)
                
                if (rx_bps + tx_bps) > 1000: # Over 1Kbps
                    traffic_list.append({
                        "Name": name,
                        "Rx": int(rx_bps),
                        "Tx": int(tx_bps),
                        "Total": int(rx_bps + tx_bps)
                    })
                    
                # Specific WAN calculations
                if name == "v_2689": # WAN1
                    w1_rx_bits = rx_bps
                    w1_tx_bits = tx_bps
                    wan_drops = int(i.get('rx-drop', 0))
                elif name == "WAN2-ether3": # WAN2
                    w2_rx_bits = rx_bps
                    w2_tx_bits = tx_bps
        
        self.prev_ifaces = current_ifaces
        top_consumers = sorted(traffic_list, key=lambda x: x['Total'], reverse=True)[:5]
        
        # 3. VPN Stats
        vpn_secrets = self.mk_service.get_vpn_secrets()
        secret_map = {s.get('name'): s.get('profile', 'default') for s in vpn_secrets}
        
        active_vpns = self.mk_service.get_vpn_active()
        vpn_profiles = {}
        vpn_protos = {"l2tp": 0, "ovpn": 0, "sstp": 0, "pptp": 0}
        
        for v in active_vpns:
            user = v.get('name')
            proto = "l2tp" if "l2tp" in v.get('service', '') else "ovpn" if "ovpn" in v.get('service', '') else "sstp" if "sstp" in v.get('service', '') else "pptp"
            vpn_protos[proto] += 1
            prof = secret_map.get(user, "Unknown")
            vpn_profiles[prof] = vpn_profiles.get(prof, 0) + 1
            
        # 4. Latency / Packet Loss
        ping_avg, ping_loss = self.ping_service.ping("8.8.8.8")
        gw_ping, _ = self.ping_service.ping(self.ping_service.gateway_ip)
        
        # 5. Security Stats
        fw_drops = self.mk_service.get_firewall_drops()
        active_conns = self.mk_service.get_active_connections_count()
        
        # 6. System health stats
        health = self.mk_service.get_system_health()
        temp = health.get("temperature", 0)
        volt = health.get("voltage", 0)
        
        # 7. Physical ports
        eth_errors = self.mk_service.get_ethernet_errors()
        queue_count = self.mk_service.get_queue_count()
        dhcp_leases_count = len(self.mk_service.get_dhcp_leases())
        
        # 8. Event Log Errors
        last_logs = self.mk_service.get_logs()
        log_msg = ""
        if last_logs:
            for l in reversed(last_logs):
                if any(tag in l.get('topics', '') for tag in ['error', 'critical', 'warning']):
                    log_msg = f"{l.get('time')} {l.get('message')}"
                    break
        
        # Build payload
        payload = {
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_load": cpu_load,
            "free_memory": free_mem,
            "total_memory": total_mem,
            "hdd_free": free_hdd,
            "hdd_total": total_hdd,
            "temperature": temp,
            "voltage": volt,
            "uptime": uptime,
            "dhcp_leases": dhcp_leases_count,
            "queue_count": queue_count,
            "wan_drops": wan_drops,
            "sfp_rx_power": 0.0,
            "log_message": log_msg,
            "wan1_rx": int(w1_rx_bits), 
            "wan1_tx": int(w1_tx_bits),
            "wan2_rx": int(w2_rx_bits), 
            "wan2_tx": int(w2_tx_bits),
            "vpn_count": len(active_vpns),
            "vpn_l2tp": vpn_protos["l2tp"], 
            "vpn_ovpn": vpn_protos["ovpn"], 
            "vpn_sstp": vpn_protos["sstp"], 
            "vpn_pptp": vpn_protos["pptp"],
            "ping_avg_ms": ping_avg, 
            "ping_loss_percent": ping_loss,
            "vpn_profiles_detail": vpn_profiles,
            "top_consumers": top_consumers,
            "firewall_drops_total": fw_drops,
            "active_connections": active_conns,
            "gateway_ping": gw_ping,
            "interface_errors": eth_errors
        }
        
        # Evaluate alert events & log warnings
        self._evaluate_alerts(payload)
        
        # Push to MySQL database if available
        self._save_to_db(payload)
        
        # Periodically scan network and run background jobs (similar to legacy backend)
        # Scan devices every 5 minutes (300 seconds)
        if now_ts - self.last_scan > 300:
            self._scan_network()
            self.last_scan = now_ts
            
        # Fire callback to notify GUI controllers
        self.on_update(payload)

    def _evaluate_alerts(self, payload: Dict[str, Any]) -> None:
        # Check Critical Alerts: Network Loss
        if payload['wan_drops'] > 0 or payload['ping_loss_percent'] > 50:
            subject = "🚨 ALERTA CRITICA: Caída de Internet - REN Enterprise Monitor"
            body = (f"Se detectó pérdida de conectividad en el sistema.\n"
                    f"Fecha: {payload['created_at']}\n"
                    f"Drops de WAN: {payload['wan_drops']}\n"
                    f"Pérdida de Ping: {payload['ping_loss_percent']}%\n"
                    f"Ping Promedio: {payload['ping_avg_ms']} ms")
            self.logging_service.log("critical", "Pérdida de conectividad detectada", "network")
            self.send_email_alert(subject, body)
            self._insert_system_alert("connectivity_loss", "critical", "Pérdida de conectividad / Pérdida alta de paquetes")

        # Check Warning Alerts: Bandwidth Spike (> 50Mbps total WAN)
        total_wan_traffic = payload['wan1_rx'] + payload['wan2_rx']
        if total_wan_traffic > 50_000_000:
            subject = "⚠️ ALERTA DE TRAFICO: Consumo de Red Alto (>50Mbps)"
            body = (f"El consumo de red superó el umbral de 50 Mbps.\n"
                    f"Fecha: {payload['created_at']}\n"
                    f"WAN1 Descarga: {payload['wan1_rx']/1_000_000:.2f} Mbps\n"
                    f"WAN2 Descarga: {payload['wan2_rx']/1_000_000:.2f} Mbps\n"
                    f"Conexiones activas: {payload['active_connections']}")
            self.logging_service.log("warning", f"Consumo de red alto detectado: {total_wan_traffic/1_000_000:.2f} Mbps", "traffic")
            self.send_email_alert(subject, body)
            self._insert_system_alert("high_bandwidth", "warning", f"Consumo de red superó 50 Mbps ({total_wan_traffic/1_000_000:.1f} Mbps)")

        # Check Hardware Warning Alerts: High CPU load
        if payload['cpu_load'] >= 90:
            self.logging_service.log("warning", f"Carga de CPU alta: {payload['cpu_load']}%", "system")
            self._insert_system_alert("high_cpu", "warning", f"Carga de CPU superior al 90% ({payload['cpu_load']}%)")

    def _insert_system_alert(self, alert_type: str, severity: str, message: str) -> None:
        db_cfg = self.settings.get("database")
        if not db_cfg:
            return
        try:
            conn = pymysql.connect(
                host=db_cfg['host'],
                user=db_cfg['user'],
                password=db_cfg['password'],
                database=db_cfg['database'],
                timeout=2
            )
            with conn.cursor() as cursor:
                # Add alert if it's not already logged recently (simple deduplication)
                cursor.execute(
                    "SELECT id FROM system_alerts WHERE alert_type = %s AND resolved_at IS NULL AND message = %s ORDER BY created_at DESC LIMIT 1",
                    (alert_type, message)
                )
                if not cursor.fetchone():
                    sql = "INSERT INTO system_alerts (alert_type, severity, message) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (alert_type, severity, message))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logging_service.logger.debug(f"Failed to save system alert to DB: {e}")

    def _save_to_db(self, payload: Dict[str, Any]) -> None:
        db_cfg = self.settings.get("database")
        if not db_cfg:
            return
        try:
            conn = pymysql.connect(
                host=db_cfg['host'],
                user=db_cfg['user'],
                password=db_cfg['password'],
                database=db_cfg['database'],
                timeout=2
            )
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO router_stats (
                    cpu_load, free_memory, total_memory, hdd_free, hdd_total, temperature, voltage, uptime,
                    dhcp_leases, queue_count, wan_drops, sfp_rx_power, log_message,
                    wan1_tx, wan1_rx, wan2_tx, wan2_rx,
                    vpn_count, vpn_l2tp, vpn_ovpn, vpn_sstp, vpn_pptp,
                    ping_avg_ms, ping_loss_percent, vpn_profiles_detail,
                    firewall_drops_total, top_consumers, active_connections,
                    gateway_ping, interface_errors
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                """
                # Convert dict objects to JSON strings
                vpn_prof_json = json.dumps(payload['vpn_profiles_detail'])
                top_consumers_json = json.dumps(payload['top_consumers'])
                iface_err_json = json.dumps(payload['interface_errors'])
                
                cursor.execute(sql, (
                    payload['cpu_load'], payload['free_memory'], payload['total_memory'], payload['hdd_free'], payload['hdd_total'], payload['temperature'], payload['voltage'], payload['uptime'],
                    payload['dhcp_leases'], payload['queue_count'], payload['wan_drops'], payload['sfp_rx_power'], payload['log_message'],
                    payload['wan1_tx'], payload['wan1_rx'], payload['wan2_tx'], payload['wan2_rx'],
                    payload['vpn_count'], payload['vpn_l2tp'], payload['vpn_ovpn'], payload['vpn_sstp'], payload['vpn_pptp'],
                    payload['ping_avg_ms'], payload['ping_loss_percent'], vpn_prof_json,
                    payload['firewall_drops_total'], top_consumers_json, payload['active_connections'],
                    payload['gateway_ping'], iface_err_json
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logging_service.logger.debug(f"Failed to save router_stats to MySQL: {e}")

    def _scan_network(self) -> None:
        self.logging_service.log("info", "Starting active network scanner sync...")
        try:
            arp_data = self.mk_service.get_arp_table()
            dhcp_data = self.mk_service.get_dhcp_leases()
            
            devices = {}
            for lease in dhcp_data:
                mac = lease.get('mac-address')
                if mac:
                    devices[mac] = {
                        "ip": lease.get('address'),
                        "hostname": lease.get('host-name', 'Unknown'),
                        "interface": lease.get('server', 'unknown'),
                        "online": False
                    }
            for entry in arp_data:
                mac = entry.get('mac-address')
                if mac:
                    if mac not in devices:
                        devices[mac] = {
                            "ip": entry.get('address'),
                            "hostname": "Unknown",
                            "interface": entry.get('interface'),
                            "online": True
                        }
                    else:
                        devices[mac]["online"] = True
            
            # Save to MySQL inventory table
            db_cfg = self.settings.get("database")
            if not db_cfg:
                return
                
            conn = pymysql.connect(
                host=db_cfg['host'],
                user=db_cfg['user'],
                password=db_cfg['password'],
                database=db_cfg['database'],
                timeout=2
            )
            with conn.cursor() as cursor:
                # First set all devices offline, then upsert current list
                cursor.execute("UPDATE device_inventory SET is_online = FALSE")
                for mac, info in devices.items():
                    sql = """
                    INSERT INTO device_inventory (mac_address, ip_address, hostname, interface, is_online)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE ip_address=VALUES(ip_address), hostname=VALUES(hostname), is_online=VALUES(is_online), last_seen=CURRENT_TIMESTAMP
                    """
                    cursor.execute(sql, (mac, info['ip'], info['hostname'], info['interface'], info['online']))
            conn.commit()
            conn.close()
            self.logging_service.log("info", f"Network scan completed. Discovered {len(devices)} device leases.")
        except Exception as e:
            self.logging_service.log("error", f"Error in background network device scan: {e}")
