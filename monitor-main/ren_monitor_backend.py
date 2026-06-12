
import time
import json
import requests
import subprocess
import datetime
import pymysql
import routeros_api
import smtplib
import ssl
from email.message import EmailMessage
import os

# --- EMAIL CONFIG ---
EMAIL_CONFIG_FILE = "config_email.json"
last_email_time = 0
EMAIL_COOLDOWN = 300 # 5 Minutos entre correos para no saturar

def load_email_config():
    if os.path.exists(EMAIL_CONFIG_FILE):
        with open(EMAIL_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def send_email_alert(subject, body):
    global last_email_time
    if time.time() - last_email_time < EMAIL_COOLDOWN:
        return # Skip if too frequent

    conf = load_email_config()
    if not conf or "PON_AQUI" in conf['email_password']:
        print("[EMAIL] Falta configurar contraseña en config_email.json")
        return

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = conf['email_user']
        msg['To'] = conf['alert_recipient']

        context = ssl.create_default_context()
        with smtplib.SMTP(conf['smtp_server'], conf['smtp_port']) as server:
            server.starttls(context=context)
            server.login(conf['email_user'], conf['email_password'])
            server.send_message(msg)
        
        print(f"[EMAIL] Alerta enviada a {conf['alert_recipient']}")
        last_email_time = time.time()
    except Exception as e:
        print(f"[EMAIL] Error enviando correo: {e}")

# --- CONFIGURACIÓN ---
MK_IP = "10.24.0.1"
MK_USER = "Ejgonzalez"
MK_PASS = "Sara28031610"
API_URL = "http://localhost/ren_monitor/api_ingest.php"

# Configuración DB
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ren_monitor"
}

# Contexto para calcular tasas de bits (bps) y estados
ctx = {
    "prev_time": 0,
    "prev_ifaces": {}, # {name: bytes}
    "prev_wan_drops": 0,
    "secret_map": {}, # {user: profile}
    "last_secret_update": 0,
    "gateway_ip": "10.24.0.1" # IP del Gateway Mikrotik
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def run_speedtest():
    print("[SPEEDTEST] Iniciando prueba de velocidad real...")
    try:
        process = subprocess.Popen(['speedtest-cli', '--secure', '--json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            data = json.loads(stdout)
            result = {
                "download_mbps": round(data['download'] / 1_000_000, 2),
                "upload_mbps": round(data['upload'] / 1_000_000, 2),
                "ping_ms": data['ping'],
                "isp": data['client']['isp']
            }
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO speed_history (download_mbps, upload_mbps, ping_ms, isp) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (result['download_mbps'], result['upload_mbps'], result['ping_ms'], result['isp']))
            conn.commit()
            conn.close()
            print(f"[SPEEDTEST] OK: {result['download_mbps']} Mbps")
    except Exception as e:
        print(f"[SPEEDTEST] Error: {e}")

def scan_network(api):
    print("[SCANNER] Escaneando dispositivos...")
    try:
        arp_data = api.get_resource('/ip/arp').get()
        dhcp_data = api.get_resource('/ip/dhcp-server/lease').get()
        devices = {}
        for lease in dhcp_data:
            mac = lease.get('mac-address')
            if mac: devices[mac] = {"ip": lease.get('address'), "hostname": lease.get('host-name', 'Unknown'), "interface": lease.get('server', 'unknown'), "online": False}
        for entry in arp_data:
            mac = entry.get('mac-address')
            if mac:
                if mac not in devices: devices[mac] = {"ip": entry.get('address'), "hostname": "Unknown", "interface": entry.get('interface'), "online": True}
                else: devices[mac]["online"] = True
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE device_inventory SET is_online = FALSE")
            for mac, info in devices.items():
                sql = "INSERT INTO device_inventory (mac_address, ip_address, hostname, interface, is_online) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE ip_address=VALUES(ip_address), hostname=VALUES(hostname), is_online=VALUES(is_online), last_seen=CURRENT_TIMESTAMP"
                cursor.execute(sql, (mac, info['ip'], info['hostname'], info['interface'], info['online']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[SCANNER] Error: {e}")

def collect_telemetry(api):
    global ctx
    try:
        now_ts = time.time()
        
        # 1. Recursos de Sistema
        res = api.get_resource('/system/resource').get()[0]
        
        # 2. Tráfico de Interfaces y Top Consumers
        interfaces = api.get_resource('/interface').get()
        current_ifaces = {}
        traffic_list = []
        
        w1_rx_bits = 0; w1_tx_bits = 0; w2_rx_bits = 0; w2_tx_bits = 0; wan_drops = 0
        
        dt = now_ts - ctx["prev_time"] if ctx["prev_time"] > 0 else 1
        
        for i in interfaces:
            name = i.get('name')
            rx = int(i.get('rx-byte', 0))
            tx = int(i.get('tx-byte', 0))
            current_ifaces[name] = {"rx": rx, "tx": tx}
            
            # Cálculo de tasa para todas las interfaces (Top 5)
            if name in ctx["prev_ifaces"]:
                p_rx = ctx["prev_ifaces"][name]["rx"]
                p_tx = ctx["prev_ifaces"][name]["tx"]
                rx_bps = max(0, (rx - p_rx) * 8 / dt)
                tx_bps = max(0, (tx - p_tx) * 8 / dt)
                
                if (rx_bps + tx_bps) > 1000: # Solo > 1Kbps
                    traffic_list.append({
                        "Name": name, 
                        "Rx": int(rx_bps), 
                        "Tx": int(tx_bps),
                        "Total": int(rx_bps + tx_bps)
                    })
            
            # WAN específicas
            if name == "v_2689":
                if ctx["prev_time"] > 0:
                    w1_rx_bits = max(0, (rx - ctx["prev_ifaces"].get(name, {"rx":rx})["rx"]) * 8 / dt)
                    w1_tx_bits = max(0, (tx - ctx["prev_ifaces"].get(name, {"tx":tx})["tx"]) * 8 / dt)
                wan_drops = int(i.get('rx-drop', 0))
            elif name == "WAN2-ether3":
                if ctx["prev_time"] > 0:
                    w2_rx_bits = max(0, (rx - ctx["prev_ifaces"].get(name, {"rx":rx})["rx"]) * 8 / dt)
                    w2_tx_bits = max(0, (tx - ctx["prev_ifaces"].get(name, {"tx":tx})["tx"]) * 8 / dt)

        top_consumers = sorted(traffic_list, key=lambda x: x['Total'], reverse=True)[:5]
        
        # Guardar estados para la próxima vuelta
        ctx["prev_time"] = now_ts
        ctx["prev_ifaces"] = current_ifaces
        
        # 3. VPN y Perfiles (Cache cada 60s)
        if now_ts - ctx["last_secret_update"] > 60:
            secrets = api.get_resource('/ppp/secret').get()
            ctx["secret_map"] = {s.get('name'): s.get('profile', 'default') for s in secrets}
            ctx["last_secret_update"] = now_ts
            
        active_vpns = api.get_resource('/ppp/active').get()
        vpn_profiles = {}
        vpn_protos = {"l2tp": 0, "ovpn": 0, "sstp": 0, "pptp": 0}
        
        for v in active_vpns:
            user = v.get('name')
            proto = "l2tp" if "l2tp" in v.get('service', '') else "ovpn" if "ovpn" in v.get('service', '') else "sstp" if "sstp" in v.get('service', '') else "pptp"
            vpn_protos[proto] += 1
            prof = ctx["secret_map"].get(user, "Unknown")
            vpn_profiles[prof] = vpn_profiles.get(prof, 0) + 1

        ping_ms = 0; loss = 0; gateway_ping = 0
        try:
            # Ping a Internet (1.1.1.1)
            ping_res = api.get_resource('/').call('ping', {'address': '1.1.1.1', 'count': '1'})
            if ping_res:
                rtt = ping_res[0].get('avg-rtt', '0ms')
                ping_ms = float(''.join(c for c in rtt if c.isdigit() or c == '.'))
                loss = int(ping_res[0].get('packet-loss', 0))
            
            # Ping al Gateway Local (Diagnóstico de red interna)
            gw_res = api.get_resource('/').call('ping', {'address': ctx["gateway_ip"], 'count': '1'})
            if gw_res:
                rtt_gw = gw_res[0].get('avg-rtt', '0ms')
                gateway_ping = float(''.join(c for c in rtt_gw if c.isdigit() or c == '.'))
        except: pass

        # 5. Firewall Stats (Drops y Conexiones Activas)
        fw_drops = 0
        active_conns = 0
        try:
            # Conteo de ataques bloqueados
            filters = api.get_resource('/ip/firewall/filter').get()
            for f in filters:
                if f.get('action') == 'drop':
                    fw_drops += int(f.get('packets', 0))
            
            # Conteo de SESIONES/CONEXIONES activas (Rayos X de red)
            conns = api.get_resource('/ip/firewall/connection').get()
            active_conns = len(conns)
        except Exception as e:
            print(f"[TELEMETRIA] Error en Firewall: {e}")

        # 6. Colas de Tráfico (Queues)
        active_queues = 0
        try:
            queues = api.get_resource('/queue/simple').get()
            active_queues = len(queues)
        except: pass

        # 7. Logs de Error
        log_msg = ""
        try:
            logs = api.get_resource('/log').get()
            for l in reversed(logs[-10:]):
                if any(tag in l.get('topics', '') for tag in ['error', 'critical', 'warning']):
                    log_msg = f"{l.get('time')} {l.get('message')}"
                    break
        except: pass

        # 8. Salud del Sistema y Puertos (Ethernet Errors)
        temp = 0; volt = 0; eth_errors = {}
        try:
            health = api.get_resource('/system/health').get()
            for h in health:
                if 'temperature' in h.get('name', ''): temp = h.get('value', 0)
                if 'voltage' in h.get('name', ''): volt = h.get('value', 0)
            
            # Chequeo de errores en interfaces físicas
            eth_stats = api.get_resource('/interface/ethernet').get()
            for eth in eth_stats:
                e_name = eth.get('name')
                e_err = int(eth.get('rx-error', 0)) + int(eth.get('tx-error', 0)) + \
                        int(eth.get('fcs-error', 0)) + int(eth.get('align-error', 0))
                if e_err > 0: eth_errors[e_name] = e_err
        except: pass

        # payload FINAL
        payload = {
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_load": int(res.get('cpu-load', 0)),
            "free_memory": int(res.get('free-memory', 0)),
            "total_memory": int(res.get('total-memory', 0)),
            "hdd_free": int(res.get('free-hdd-space', 0)),
            "hdd_total": int(res.get('total-hdd-space', 0)),
            "temperature": temp,
            "voltage": volt,
            "uptime": res.get('uptime', 'unknown'),
            "dhcp_leases": len(api.get_resource('/ip/dhcp-server/lease').get()),
            "queue_count": active_queues,
            "wan_drops": wan_drops, # FIX: Usar variable real de drops, no active_conns
            "sfp_rx_power": 0,
            "log_message": log_msg,
            "wan1_rx": int(w1_rx_bits), "wan1_tx": int(w1_tx_bits),
            "wan2_rx": int(w2_rx_bits), "wan2_tx": int(w2_tx_bits),
            "vpn_count": len(active_vpns),
            "vpn_l2tp": vpn_protos["l2tp"], "vpn_ovpn": vpn_protos["ovpn"], "vpn_sstp": vpn_protos["sstp"], "vpn_pptp": vpn_protos["pptp"],
            "ping_avg_ms": ping_ms, "ping_loss_percent": loss,
            "vpn_profiles_detail": vpn_profiles,
            "top_consumers": top_consumers,
            "firewall_drops_total": fw_drops,
            "active_connections": active_conns,
            "gateway_ping": gateway_ping,
            "interface_errors": eth_errors
        }

        # --- CHECK ALERTS DIRECTLY IN BACKEND ---
        # 1. Connectivity Loss
        if payload['wan_drops'] > 0 or payload['ping_loss_percent'] > 50:
             send_email_alert("🚨 ALERTA CRITICA: Caída de Internet", 
                              f"Se detectó pérdida de conectividad.\nDrops: {payload['wan_drops']}\nPacket Loss: {payload['ping_loss_percent']}%")

        # 2. High Consumption (Traffic Spike > 50Mbps)
        if (payload['wan1_rx'] + payload['wan2_rx']) > 50_000_000:
             send_email_alert("⚠️ ALERTA DE TRAFICO: Consumo Alto", 
                              f"El consumo de red superó los 50 Mbps.\nWAN1 Rx: {payload['wan1_rx']/1000000:.2f} Mbps\nWAN2 Rx: {payload['wan2_rx']/1000000:.2f} Mbps")
        
        requests.post(API_URL, json=payload, timeout=2)

        requests.post(API_URL, json=payload, timeout=2)
        print(f"[{payload['created_at']}] SYNC | Claro: {int(payload['wan1_rx']/1000)} Kbps | Conexiones: {active_conns} | Ataques: {fw_drops}")

    except Exception as e:
        print(f"[TELEMETRIA] Error: {e}")

def main():
    print("=== MONITOR REN PRO BACKEND (MODE: SUPERIOR) ===")
    last_speedtest = 0; last_scan = 0
    while True:
        try:
            connection = routeros_api.RouterOsApiPool(MK_IP, username=MK_USER, password=MK_PASS, plaintext_login=True)
            api = connection.get_api()
            print("Conexión Establecida. Telemetría iniciada.")
            while True:
                start = time.time()
                collect_telemetry(api)
                
                # Tareas de fondo
                now = time.time()
                if now - last_speedtest > 3600:
                    run_speedtest(); last_speedtest = now
                if now - last_scan > 300:
                    scan_network(api); last_scan = now
                
                # Sleep de precisión
                time.sleep(max(0.1, 1.0 - (time.time() - start)))
        except Exception as e:
            print(f"Error: {e}. Reintentando en 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
