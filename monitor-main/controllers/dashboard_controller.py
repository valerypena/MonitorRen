import os
import json
import logging
from typing import Dict, Any, Callable, Optional, List
from models.network_model import NetworkModel
from models.router_model import RouterModel
from models.system_model import SystemModel
from models.diagnostics_model import DiagnosticsModel
from services.monitoring_service import MonitoringService
from controllers.theme_controller import ThemeController
from controllers.diagnostics_controller import DiagnosticsController
from controllers.network_controller import NetworkController

class DashboardController:
    def __init__(self, settings_path: str):
        self.settings_path = settings_path
        self.settings = self._load_settings()
        
        # Models
        self.network_model = NetworkModel(max_history_len=60)
        self.router_model = RouterModel()
        self.system_model = SystemModel()
        self.diagnostics_model = DiagnosticsModel()
        
        # Sub-controllers
        self.theme_controller = ThemeController()
        
        # Callback to update the dashboard views
        self.view_update_callback: Optional[Callable[[], None]] = None
        
        # Start background monitoring service
        self.monitoring_service = MonitoringService(
            self.settings, 
            self._handle_telemetry_update
        )
        
        # Instantiate remaining controllers using services
        self.diagnostics_controller = DiagnosticsController(
            self.diagnostics_model, 
            self.settings
        )
        self.network_controller = NetworkController(
            self.network_model, 
            self.monitoring_service.mk_service
        )
        
        # Cache of the latest payload received
        self.latest_payload: Dict[str, Any] = {}

    def _load_settings(self) -> Dict[str, Any]:
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to read settings from {self.settings_path}: {e}")
        
        # Default fallback settings
        return {
            "mikrotik": {"host": "10.24.0.1", "username": "admin", "password": ""},
            "database": {"host": "localhost", "user": "root", "password": "", "database": "ren_monitor"},
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email_user": "",
                "email_password": "",
                "alert_recipient": "",
                "cooldown": 300
            },
            "theme": {"current_theme": "dark"}
        }

    def save_settings(self, new_settings: Dict[str, Any]) -> None:
        self.settings = new_settings
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            logging.info(f"Settings saved successfully to {self.settings_path}")
            
            # Update running services
            self.monitoring_service.update_settings(self.settings)
            self.diagnostics_controller.settings = self.settings
            self.diagnostics_controller.diagnostic_service.settings = self.settings
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def start_monitoring(self) -> None:
        self.monitoring_service.start()

    def stop_monitoring(self) -> None:
        self.monitoring_service.stop()

    def set_view_update_callback(self, callback: Callable[[], None]) -> None:
        self.view_update_callback = callback

    def _handle_telemetry_update(self, payload: Dict[str, Any]) -> None:
        self.latest_payload = payload
        
        # Update models
        self.network_model.update_from_payload(payload)
        self.router_model.update_from_payload(payload)
        self.system_model.update_from_payload(payload)
        
        # Fetch active alerts from database to display in the UI (if database configuration is set)
        db_cfg = self.settings.get("database")
        if db_cfg and not self.monitoring_service.mk_service.is_mock:
            try:
                import pymysql
                conn = pymysql.connect(
                    host=db_cfg['host'],
                    user=db_cfg['user'],
                    password=db_cfg['password'],
                    database=db_cfg['database'],
                    timeout=2
                )
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM system_alerts WHERE resolved_at IS NULL ORDER BY created_at DESC LIMIT 15")
                    alerts = cursor.fetchall()
                    self.system_model.update_alerts_list(alerts)
                conn.close()
            except Exception:
                # Fallback to local mock alert generation if database connection fails
                self._generate_mock_alerts()
        else:
            self._generate_mock_alerts()

        # Update view
        if self.view_update_callback:
            try:
                self.view_update_callback()
            except Exception as e:
                logging.error(f"Error executing view update callback: {e}")

    def _generate_mock_alerts(self) -> None:
        # Generate realistic active warning items if no DB connection
        alerts = []
        if self.router_model.cpu_load >= 80:
            alerts.append({
                "alert_type": "high_cpu",
                "severity": "warning",
                "message": f"Carga de CPU elevada: {self.router_model.cpu_load}%",
                "created_at": "Reciente"
            })
        if self.system_model.ping_loss_percent > 10:
            alerts.append({
                "alert_type": "packet_loss",
                "severity": "critical",
                "message": f"Pérdida de paquetes alta: {self.system_model.ping_loss_percent}%",
                "created_at": "Reciente"
            })
        if self.router_model.temperature >= 75:
            alerts.append({
                "alert_type": "high_temp",
                "severity": "critical",
                "message": f"Temperatura sobrecalentada: {self.router_model.temperature}°C",
                "created_at": "Reciente"
            })
        # If WAN speeds are 0, WAN is offline
        if (self.network_model.wan1_rx + self.network_model.wan1_tx) == 0:
            alerts.append({
                "alert_type": "wan1_down",
                "severity": "critical",
                "message": "WAN1 (Claro) sin tráfico / caída detectada",
                "created_at": "Reciente"
            })
        if (self.network_model.wan2_rx + self.network_model.wan2_tx) == 0:
            alerts.append({
                "alert_type": "wan2_down",
                "severity": "warning",
                "message": "WAN2 (Movistar) sin tráfico / inactiva",
                "created_at": "Reciente"
            })
            
        self.system_model.update_alerts_list(alerts)
