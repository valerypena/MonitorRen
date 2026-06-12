import os
import time
import datetime
import urllib.request
import socket
import logging
from typing import Dict, Any, List, Callable, Tuple

class SystemDiagnostic:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        
    def run_all_checks(self, current_payload: Dict[str, Any], progress_cb: Callable[[float], None]) -> Tuple[List[Dict[str, Any]], str, str]:
        """
        Runs the diagnostic checks.
        Returns:
            Tuple[List[Dict[str, Any]], str, str]: (results_list, report_path, final_state)
        """
        results = []
        progress_cb(10.0)
        time.sleep(0.2) # Short sleep to feel realistic and allow progress to draw
        
        # 1. Connectivity Check (Google DNS 8.8.8.8)
        progress_cb(25.0)
        dns_ip = "8.8.8.8"
        try:
            # Socket ping
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            # Try connecting to DNS port 53 (standard DNS port)
            start_ping = time.time()
            s.connect((dns_ip, 53))
            rtt = (time.time() - start_ping) * 1000.0
            s.close()
            results.append({
                "name": "Conectividad (Google DNS 8.8.8.8)",
                "status": "PASS",
                "value": f"{rtt:.1f} ms",
                "notes": "Puerto 53 DNS abierto y respondiendo"
            })
        except Exception as e:
            results.append({
                "name": "Conectividad (Google DNS 8.8.8.8)",
                "status": "FAIL",
                "value": "Sin Respuesta",
                "notes": f"Error de conexión de red: {e}"
            })

        # 2. Internet Access (https://google.com)
        progress_cb(40.0)
        time.sleep(0.2)
        try:
            req = urllib.request.Request("https://google.com", headers={'User-Agent': 'Mozilla/5.0'})
            start_http = time.time()
            with urllib.request.urlopen(req, timeout=3.0) as response:
                response.read(100) # read minimal bytes
            http_rtt = (time.time() - start_http) * 1000.0
            results.append({
                "name": "Acceso a Internet (google.com)",
                "status": "PASS",
                "value": f"{http_rtt:.1f} ms",
                "notes": "Acceso HTTP completo exitoso"
            })
        except Exception as e:
            results.append({
                "name": "Acceso a Internet (google.com)",
                "status": "FAIL",
                "value": "Caído",
                "notes": f"No se pudo resolver o acceder a google.com: {e}"
            })

        # 3. Router WAN1 Status
        progress_cb(55.0)
        time.sleep(0.2)
        wan1_rx = current_payload.get("wan1_rx", 0)
        wan1_tx = current_payload.get("wan1_tx", 0)
        if wan1_rx > 0 or wan1_tx > 0:
            results.append({
                "name": "Estado Router WAN1 (Claro)",
                "status": "PASS",
                "value": "Conectado",
                "notes": f"Tráfico activo Rx: {wan1_rx/1000:.1f} Kbps | Tx: {wan1_tx/1000:.1f} Kbps"
            })
        else:
            # If speed is 0, check if we're in mock mode and simulate WAN1 drop
            results.append({
                "name": "Estado Router WAN1 (Claro)",
                "status": "WARN",
                "value": "Inactivo / Sin Tráfico",
                "notes": "Línea conectada pero no registra tráfico"
            })

        # 4. Router WAN2 Status
        progress_cb(70.0)
        time.sleep(0.2)
        wan2_rx = current_payload.get("wan2_rx", 0)
        wan2_tx = current_payload.get("wan2_tx", 0)
        if wan2_rx > 0 or wan2_tx > 0:
            results.append({
                "name": "Estado Router WAN2 (Movistar)",
                "status": "PASS",
                "value": "Conectado",
                "notes": f"Tráfico activo Rx: {wan2_rx/1000:.1f} Kbps | Tx: {wan2_tx/1000:.1f} Kbps"
            })
        else:
            results.append({
                "name": "Estado Router WAN2 (Movistar)",
                "status": "WARN",
                "value": "Inactivo / Sin Tráfico",
                "notes": "Línea conectada pero no registra tráfico"
            })

        # 5. Hardware Checks: CPU load
        progress_cb(80.0)
        time.sleep(0.2)
        cpu = current_payload.get("cpu_load", 0)
        if cpu < 80:
            results.append({
                "name": "Uso de CPU",
                "status": "PASS",
                "value": f"{cpu}%",
                "notes": "Nivel de carga de procesador saludable"
            })
        elif cpu < 95:
            results.append({
                "name": "Uso de CPU",
                "status": "WARN",
                "value": f"{cpu}%",
                "notes": "CPU con carga moderada superior a 80%"
            })
        else:
            results.append({
                "name": "Uso de CPU",
                "status": "FAIL",
                "value": f"{cpu}%",
                "notes": "Sobrecarga de CPU crítica superior al 95%"
            })

        # 6. Hardware Checks: RAM usage
        free_mem = current_payload.get("free_memory", 0)
        total_mem = current_payload.get("total_memory", 1024)
        ram_pct = 0.0
        if total_mem > 0:
            ram_pct = ((total_mem - free_mem) / total_mem) * 100.0
            
        if ram_pct < 85:
            results.append({
                "name": "Uso de RAM",
                "status": "PASS",
                "value": f"{ram_pct:.1f}%",
                "notes": f"RAM libre disponible: {free_mem / 1_000_000:.1f} MB"
            })
        else:
            results.append({
                "name": "Uso de RAM",
                "status": "WARN",
                "value": f"{ram_pct:.1f}%",
                "notes": "RAM utilizada por encima del 85% de capacidad"
            })

        # 7. Hardware Checks: Temperature
        progress_cb(90.0)
        time.sleep(0.2)
        temp = current_payload.get("temperature", 0)
        if temp < 75:
            results.append({
                "name": "Temperatura Hardware",
                "status": "PASS",
                "value": f"{temp}°C",
                "notes": "Temperatura interna del chasis normal"
            })
        else:
            results.append({
                "name": "Temperatura Hardware",
                "status": "FAIL",
                "value": f"{temp}°C",
                "notes": "Sobrecalentamiento del equipo detectado (>75°C)"
            })

        # 8. Interfaces link status
        iface_errors = current_payload.get("interface_errors", {})
        if not iface_errors:
            results.append({
                "name": "Estado de Interfaces Físicas",
                "status": "PASS",
                "value": "Saludable",
                "notes": "No se registran errores de alineación, CRC o tramas en puertos Ethernet"
            })
        else:
            errs_str = ", ".join([f"{k}: {v} err" for k, v in iface_errors.items()])
            results.append({
                "name": "Estado de Interfaces Físicas",
                "status": "WARN",
                "value": "Errores Registrados",
                "notes": f"Errores en interfaces físicas detectados: {errs_str}"
            })

        progress_cb(95.0)
        
        # Calculate final state of diagnostics
        final_state = "GREEN"
        has_fail = any(r["status"] == "FAIL" for r in results)
        has_warn = any(r["status"] == "WARN" for r in results)
        if has_fail:
            final_state = "RED"
        elif has_warn:
            final_state = "YELLOW"
            
        # Generate the report HTML
        report_path = self.generate_html_report(results, current_payload, final_state)
        
        progress_cb(100.0)
        return results, report_path, final_state

    def generate_html_report(self, results: List[Dict[str, Any]], payload: Dict[str, Any], final_state: str) -> str:
        # Create reports folder
        os.makedirs("reports", exist_ok=True)
        
        now = datetime.datetime.now()
        filename = f"health_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
        report_path = os.path.join("reports", filename)
        
        # Read the Styles.css content
        styles_css_content = ""
        try:
            # Look in the same directory as this script
            styles_path = os.path.join(os.path.dirname(__file__), "Styles.css")
            if os.path.exists(styles_path):
                with open(styles_path, "r", encoding="utf-8") as f:
                    styles_css_content = f.read()
        except Exception as e:
            logging.warning(f"Could not load Styles.css: {e}")
            
        # If Styles.css wasn't found or read, provide a fallback with the main variables
        if not styles_css_content:
            styles_css_content = """
            :root {
                --brand-blue: #58a6ff;
                --brand-green: #3fb950;
                --brand-red: #f85149;
                --brand-warn: #d29922;
                --bg-body: #010409;
                --bg-card: #0d1117;
                --border-card: #30363d;
                --text-main: #ffffff;
                --text-muted: #8b949e;
                --chart-grid: rgba(255, 255, 255, 0.05);
            }
            [data-theme="light"] {
                --bg-body: #f0f2f5;
                --bg-card: #ffffff;
                --border-card: #d0d7de;
                --text-main: #1f2328;
                --text-muted: #656d76;
                --chart-grid: #ebf0f4;
                --brand-blue: #0969da;
                --brand-green: #1a7f37;
                --brand-red: #d1242f;
            }
            """

        # Current theme selection from settings config
        current_theme = self.settings.get("theme", {}).get("current_theme", "dark")
        
        state_colors = {
            "GREEN": {"bg": "rgba(63, 185, 80, 0.1)", "text": "var(--brand-green)", "label": "SISTEMA SALUDABLE / OPERATIVO", "border": "var(--brand-green)"},
            "YELLOW": {"bg": "rgba(210, 153, 34, 0.1)", "text": "var(--brand-warn)", "label": "SISTEMA EN ADVERTENCIA / DEGRADADO", "border": "var(--brand-warn)"},
            "RED": {"bg": "rgba(248, 81, 73, 0.1)", "text": "var(--brand-red)", "label": "ERROR CRÍTICO / INCIDENTE DE RED", "border": "var(--brand-red)"}
        }
        
        state_info = state_colors.get(final_state, state_colors["GREEN"])
        
        # Convert values
        free_mem = payload.get("free_memory", 0)
        total_mem = payload.get("total_memory", 1)
        used_mem = total_mem - free_mem
        mem_pct = (used_mem / total_mem) * 100 if total_mem > 0 else 0
        
        # VPN details formatting
        vpn_prof_detail = payload.get("vpn_profiles_detail", {})
        vpn_details_html = ""
        if vpn_prof_detail:
            for k, v in vpn_prof_detail.items():
                vpn_details_html += f"<div class='vpn-item'><span>{k}</span><strong>{v} túneles activos</strong></div>"
        else:
            vpn_details_html = "<div class='vpn-item' style='justify-content: center; font-style: italic; color: var(--text-muted);'>No hay sesiones VPN activas</div>"
            
        # Results table HTML rows
        results_rows_html = ""
        for r in results:
            badge_color = ""
            if r["status"] == "PASS":
                badge_color = "background-color: rgba(63, 185, 80, 0.15); color: var(--brand-green); border: 1px solid var(--brand-green);"
            elif r["status"] == "WARN":
                badge_color = "background-color: rgba(210, 153, 34, 0.15); color: var(--brand-warn); border: 1px solid var(--brand-warn);"
            else: # FAIL
                badge_color = "background-color: rgba(248, 81, 73, 0.15); color: var(--brand-red); border: 1px solid var(--brand-red);"
                
            results_rows_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid var(--border-card); font-weight: 500;">{r['name']}</td>
                <td style="padding: 12px; border-bottom: 1px solid var(--border-card);">
                    <span style="padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; {badge_color}">{r['status']}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid var(--border-card); font-family: monospace; font-weight: bold; color: var(--text-main);">{r['value']}</td>
                <td style="padding: 12px; border-bottom: 1px solid var(--border-card); color: var(--text-muted); font-size: 0.85rem;">{r['notes']}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="es" data-theme="{current_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REN Monitor - Reporte de Salud del Sistema</title>
    <!-- Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Styles.css Injected Core */
        {styles_css_content}
        
        /* Report Specific Layout Overrides */
        body {{
            background-color: var(--bg-body);
            color: var(--text-main);
            padding: 40px 20px;
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s, color 0.3s;
        }}
        .report-container {{
            max-width: 960px;
            margin: 0 auto;
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            overflow: hidden;
        }}
        .report-header {{
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border-card);
            padding: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .report-header h1 {{
            margin: 0;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }}
        .report-header p {{
            margin: 5px 0 0 0;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        .badge-status {{
            border-left: 6px solid {state_info['border']};
            background-color: {state_info['bg']};
            color: {state_info['text']};
            padding: 18px 24px;
            font-size: 1.1rem;
            font-weight: 800;
            margin: 25px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section {{
            padding: 0 25px 25px 25px;
        }}
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-card);
            padding-bottom: 8px;
            margin-bottom: 20px;
            color: var(--text-main);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            margin-top: 10px;
        }}
        th {{
            background-color: rgba(128,128,128,0.03);
            padding: 12px;
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            font-weight: 700;
            border-bottom: 2px solid var(--border-card);
        }}
        .footer {{
            background-color: rgba(128,128,128,0.02);
            padding: 20px;
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-card);
        }}
        .btn-theme-toggle {{
            background: transparent;
            border: 1px solid var(--border-card);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .btn-theme-toggle:hover {{
            border-color: var(--brand-blue);
            background-color: rgba(128, 128, 128, 0.1);
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <div>
                <h1>REN ENTERPRISE MONITOR</h1>
                <p>Reporte de Diagnóstico de Salud de Red & Hardware</p>
            </div>
            <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                <button class="btn-theme-toggle" onclick="toggleTheme()">☀️/🌙 Cambiar Tema</button>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">{now.strftime('%d/%m/%Y %H:%M:%S')}</div>
            </div>
        </div>

        <div class="badge-status">
            <span>{final_state == "GREEN" and "✓" or final_state == "YELLOW" and "⚠" or "✖"}</span>
            <span>{state_info['label']}</span>
        </div>

        <div class="section">
            <div class="section-title">Resultados de Verificación Operativa</div>
            <table>
                <thead>
                    <tr>
                        <th>Prueba</th>
                        <th>Estado</th>
                        <th>Valor</th>
                        <th>Detalles / Observaciones</th>
                    </tr>
                </thead>
                <tbody>
                    {results_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Métricas de Telemetría (Resumen)</div>
            <div class="grid">
                <div class="card">
                    <div class="card-label">Uso de CPU del Router</div>
                    <div class="metric-value">{payload.get('cpu_load', 0)}<span class="metric-unit">%</span></div>
                    <div class="sub-metric">Carga activa del procesador</div>
                </div>
                <div class="card">
                    <div class="card-label">Uso de RAM del Router</div>
                    <div class="metric-value">{mem_pct:.1f}<span class="metric-unit">%</span></div>
                    <div class="sub-metric">Libre: {(free_mem / 1_000_000):.1f} MB / {(total_mem / 1_000_000):.1f} MB</div>
                </div>
                <div class="card">
                    <div class="card-label">Tráfico WAN 1 (Claro)</div>
                    <div class="metric-value">{(payload.get('wan1_rx', 0)/1_000_000):.2f}<span class="metric-unit">Mbps Rx</span></div>
                    <div class="sub-metric">Subida TX: {(payload.get('wan1_tx', 0)/1_000_000):.2f} Mbps</div>
                </div>
                <div class="card">
                    <div class="card-label">Tráfico WAN 2 (Movistar)</div>
                    <div class="metric-value">{(payload.get('wan2_rx', 0)/1_000_000):.2f}<span class="metric-unit">Mbps Rx</span></div>
                    <div class="sub-metric">Subida TX: {(payload.get('wan2_tx', 0)/1_000_000):.2f} Mbps</div>
                </div>
                <div class="card">
                    <div class="card-label">Latencia de Red Externa</div>
                    <div class="metric-value">{payload.get('ping_avg_ms', 0)}<span class="metric-unit">ms</span></div>
                    <div class="sub-metric">Pérdida de paquetes: {payload.get('ping_loss_percent', 0)}%</div>
                </div>
                <div class="card">
                    <div class="card-label">Salud del Hardware</div>
                    <div class="metric-value">{payload.get('temperature', 0)}<span class="metric-unit">°C</span></div>
                    <div class="sub-metric">Voltaje de alimentación: {payload.get('voltage', 0)}V</div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 15px;">
                <div class="card-label" style="margin-bottom: 8px;">Distribución de Perfiles VPN Activos ({payload.get('vpn_count', 0)} total)</div>
                <div class="vpn-list" style="height: auto; overflow: visible;">
                    {vpn_details_html}
                </div>
            </div>
        </div>

        <div class="footer">
            Reporte de diagnóstico generado por REN Enterprise Monitor v2.2. Copyright &copy; {now.year} REN Consultores.
        </div>
    </div>
    
    <script>
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
        }}
    </script>
</body>
</html>
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logging.info(f"HTML diagnostic report generated at {report_path}")
        return report_path
