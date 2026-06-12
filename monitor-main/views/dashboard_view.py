import os
import time
import datetime
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from typing import Dict, Any, List, Optional
from controllers.dashboard_controller import DashboardController
from views.cards_view import MetricCard, SystemHealthCard, WANCard
from views.charts_view import ChartsView
from views.alerts_view import AlertsView
from views.settings_view import SettingsView

class DashboardView(ctk.CTk):
    def __init__(self, controller: DashboardController):
        super().__init__()
        self.controller = controller
        self.theme_controller = controller.theme_controller
        
        # Configure Main Window
        self.title("REN Enterprise Monitor")
        self.geometry("1100x820")
        self.minsize(1000, 750)
        
        # Register for theme changes
        self.theme_controller.apply_current_theme()
        
        # Layout: Main Grid (Left content, Right settings sidebar)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) # Sidebar column (width 0 initially)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Main Scrollable Dashboard
        
        # Load assets
        self.logo_image: Optional[ctk.CTkImage] = None
        self._load_logo()
        
        # Build UI Components
        self._build_header()
        self._build_main_dashboard()
        self._build_sidebar()
        
        # Register updates callback in controller
        self.controller.set_view_update_callback(self.refresh_view)
        
        # Apply theme callback to the main window
        self.theme_controller.register_view(self.apply_theme)
        
        # Binding closing event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # First-run UI update
        self.refresh_view()

    def _load_logo(self) -> None:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", "logo.png")
        if os.path.exists(logo_path):
            try:
                # CustomTkinter CTkImage
                img = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
            except Exception as e:
                print(f"[DashboardView] Error loading logo image: {e}")

    def _build_header(self) -> None:
        colors = self.theme_controller.theme_manager.colors
        
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, border_width=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(1, weight=1)
        self.header.grid_rowconfigure(0, weight=1)
        
        # Logo and Title Left
        self.brand_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.brand_frame.grid(row=0, column=0, padx=16, sticky="w")
        
        if self.logo_image:
            self.logo_lbl = ctk.CTkLabel(self.brand_frame, image=self.logo_image, text="")
            self.logo_lbl.pack(side="left", padx=(0, 10))
            
        self.title_lbl = ctk.CTkLabel(
            self.brand_frame, 
            text="REN ENTERPRISE MONITOR", 
            font=("Inter", 15, "bold")
        )
        self.title_lbl.pack(side="left")
        
        self.subtitle_lbl = ctk.CTkLabel(
            self.brand_frame, 
            text=" | Infraestructura de Red", 
            font=("Inter", 11),
            text_color="#8B949E"
        )
        self.subtitle_lbl.pack(side="left")
        
        # Controls & Status Right
        self.controls_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.controls_frame.grid(row=0, column=2, padx=16, sticky="e")
        
        self.uptime_lbl = ctk.CTkLabel(
            self.controls_frame, 
            text="Uptime: --", 
            font=("Inter", 11)
        )
        self.uptime_lbl.pack(side="left", padx=10)
        
        self.diag_btn = ctk.CTkButton(
            self.controls_frame,
            text="Run Diagnostics",
            width=120,
            height=28,
            font=("Inter", 11, "bold"),
            command=self._on_run_diagnostics
        )
        self.diag_btn.pack(side="left", padx=6)
        
        self.theme_btn = ctk.CTkButton(
            self.controls_frame,
            text="🌙",
            width=28,
            height=28,
            font=("Inter", 14),
            command=self._on_toggle_theme
        )
        self.theme_btn.pack(side="left", padx=6)
        
        self.settings_btn = ctk.CTkButton(
            self.controls_frame,
            text="⚙️",
            width=28,
            height=28,
            font=("Inter", 14),
            command=self._on_toggle_settings
        )
        self.settings_btn.pack(side="left", padx=6)
        
        # Status Badge
        self.status_badge = ctk.CTkFrame(self.controls_frame, corner_radius=100, height=22, fg_color="transparent")
        self.status_badge.pack(side="left", padx=(10, 0))
        
        self.status_dot = ctk.CTkLabel(
            self.status_badge, 
            text="●", 
            font=("Inter", 12),
            text_color="#3FB950"
        )
        self.status_dot.pack(side="left", padx=(8, 4))
        
        self.status_txt = ctk.CTkLabel(
            self.status_badge, 
            text="SISTEMA ONLINE", 
            font=("Inter", 10, "bold"),
            text_color="#3FB950"
        )
        self.status_txt.pack(side="left", padx=(0, 8))

    def _build_main_dashboard(self) -> None:
        self.scroll_container = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.scroll_container.grid(row=1, column=0, sticky="nsew")
        self.scroll_container.grid_columnconfigure(0, weight=1)
        
        # --- 1. KPI CARDS GRID ---
        self.kpis_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.kpis_frame.pack(fill="x", padx=16, pady=(16, 8))
        
        # 4 Equal columns for top cards
        self.kpis_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")
        self.kpis_frame.grid_rowconfigure(0, weight=1)
        
        self.health_card = SystemHealthCard(self.kpis_frame, self.theme_controller)
        self.health_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        
        self.hw_card = MetricCard(
            self.kpis_frame, "CPU & Memoria", "0%", "RouterOS | Libre: 0MB", self.theme_controller
        )
        self.hw_card.grid(row=0, column=1, padx=8, sticky="nsew")
        
        self.ping_card = MetricCard(
            self.kpis_frame, "Latencia & Pérdida", "0 ms | 0%", "GW: 0 ms | DNS: 0 ms", self.theme_controller
        )
        self.ping_card.grid(row=0, column=2, padx=8, sticky="nsew")
        
        self.security_card = MetricCard(
            self.kpis_frame, "Seguridad & Hardware", "0 blq", "Temp: 0°C | Volt: 0V", self.theme_controller
        )
        self.security_card.grid(row=0, column=3, padx=(8, 0), sticky="nsew")
        
        # --- 2. WAN PORTS GRID ---
        self.wan_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.wan_frame.pack(fill="x", padx=16, pady=8)
        self.wan_frame.grid_columnconfigure((0, 1), weight=1, uniform="wan")
        
        self.wan1_card = WANCard(self.wan_frame, "Claro Fiber (v_2689)", "brand_red", self.theme_controller)
        self.wan1_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        
        self.wan2_card = WANCard(self.wan_frame, "Movistar Main (WAN2)", "brand_blue", self.theme_controller)
        self.wan2_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        
        # --- 3. ALERTS & STATS PANELS (3 columns widget) ---
        self.alerts_view = AlertsView(
            self.scroll_container, 
            self.controller.system_model, 
            self.controller.network_model, 
            self.theme_controller
        )
        self.alerts_view.pack(fill="x", padx=16, pady=8)
        
        # --- 4. REAL-TIME TRAFFIC CHART ---
        self.chart_card = ctk.CTkFrame(self.scroll_container, corner_radius=12, border_width=2)
        self.chart_card.pack(fill="x", padx=16, pady=8)
        
        # Header inside chart card
        self.chart_lbl = ctk.CTkLabel(
            self.chart_card, 
            text="ANÁLISIS DE TRÁFICO EN TIEMPO REAL (RX)", 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        self.chart_lbl.pack(fill="x", padx=16, pady=(12, 4))
        
        self.charts_view = ChartsView(self.chart_card, self.controller.network_model, self.theme_controller)
        self.charts_view.pack(fill="x", padx=12, pady=(0, 12))
        
        # --- 5. LOG TERMINAL ---
        self.log_card = ctk.CTkFrame(self.scroll_container, corner_radius=12, border_width=2, height=140)
        self.log_card.pack(fill="x", padx=16, pady=(8, 16))
        self.log_card.pack_propagate(False)
        
        self.log_lbl = ctk.CTkLabel(
            self.log_card, 
            text="LOG DE EVENTOS DEL SISTEMA (ROUTEROS)", 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        self.log_lbl.pack(fill="x", padx=16, pady=(12, 4))
        
        self.log_textbox = ctk.CTkTextbox(
            self.log_card, 
            font=("JetBrains Mono", 10),
            state="disabled",
            fg_color="#010409",
            text_color="#7EE787"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_sidebar(self) -> None:
        # Configuration Sidebar frame (hidden by default, column 1)
        self.sidebar_frame = ctk.CTkFrame(self, width=0, corner_radius=0, border_width=0)
        self.sidebar_frame.grid(row=1, column=1, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        
        # Title inside sidebar
        self.sidebar_title = ctk.CTkLabel(
            self.sidebar_frame, 
            text="AJUSTES DE MONITOR", 
            font=("Inter", 12, "bold")
        )
        self.sidebar_title.pack(fill="x", padx=16, pady=(20, 8))
        
        # Embedded Settings Form
        self.settings_view = SettingsView(
            self.sidebar_frame, 
            self.controller.settings, 
            self._on_save_settings, 
            self.theme_controller
        )
        self.settings_view.pack(fill="both", expand=True, pady=10)
        
        # Is settings drawer open
        self.settings_open = False

    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        self.configure(fg_color=colors.get("bg_body", "#010409"))
        
        self.header.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=colors.get("border_card", "#30363D")
        )
        self.title_lbl.configure(text_color=colors.get("text_main", "#FFFFFF"))
        self.uptime_lbl.configure(text_color=colors.get("text_muted", "#8B949E"))
        
        # Diagnostics button color
        brand = colors.get("brand_blue", "#58A6FF")
        self.diag_btn.configure(
            fg_color=brand,
            hover_color=colors.get("border_card_hover", "#3B82F6"),
            text_color="#FFFFFF"
        )
        self.theme_btn.configure(
            fg_color=colors.get("bg_body", "#010409"),
            border_color=colors.get("border_card", "#30363D"),
            hover_color=colors.get("border_card_hover", "#58A6FF"),
            text_color=colors.get("text_main", "#FFFFFF")
        )
        self.theme_btn.configure(text="☀️" if theme_name == "light" else "🌙")
        
        self.settings_btn.configure(
            fg_color=colors.get("bg_body", "#010409"),
            border_color=colors.get("border_card", "#30363D"),
            hover_color=colors.get("border_card_hover", "#58A6FF"),
            text_color=colors.get("text_main", "#FFFFFF")
        )
        
        # Sidebar formatting
        self.sidebar_frame.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=colors.get("border_card", "#30363D")
        )
        self.sidebar_title.configure(text_color=colors.get("text_main", "#FFFFFF"))
        
        # Main containers
        self.chart_card.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=colors.get("border_card", "#30363D")
        )
        self.chart_lbl.configure(text_color=colors.get("text_muted", "#8B949E"))
        
        self.log_card.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=colors.get("border_card", "#30363D")
        )
        self.log_lbl.configure(text_color=colors.get("text_muted", "#8B949E"))
        
        # Log terminal text box styling
        self.log_textbox.configure(
            fg_color="#010409" if theme_name == "dark" else "#F9FAFB",
            text_color="#7EE787" if theme_name == "dark" else "#1A7F37",
            border_color=colors.get("border_card", "#30363D")
        )

    def refresh_view(self) -> None:
        """
        Pulls current states from Models and updates the UI components.
        """
        # Models References
        net = self.controller.network_model
        router = self.controller.router_model
        sys_m = self.controller.system_model
        
        # 1. Update Uptime and general status
        self.uptime_lbl.configure(text=f"Uptime: {router.uptime}")
        
        colors = self.theme_controller.theme_manager.colors
        if sys_m.health_state == "GREEN":
            self.status_dot.configure(text_color=colors.get("brand_green", "#3FB950"))
            self.status_txt.configure(text="SISTEMA ONLINE", text_color=colors.get("brand_green", "#3FB950"))
            self.status_badge.configure(border_color=colors.get("brand_green", "#3FB950"), border_width=1)
        elif sys_m.health_state == "YELLOW":
            self.status_dot.configure(text_color=colors.get("brand_warn", "#D29922"))
            self.status_txt.configure(text="SISTEMA DEGRADADO", text_color=colors.get("brand_warn", "#D29922"))
            self.status_badge.configure(border_color=colors.get("brand_warn", "#D29922"), border_width=1)
        else: # RED
            self.status_dot.configure(text_color=colors.get("brand_red", "#F85149"))
            self.status_txt.configure(text="ERROR CRITICO", text_color=colors.get("brand_red", "#F85149"))
            self.status_badge.configure(border_color=colors.get("brand_red", "#F85149"), border_width=1)

        # 2. Update System Health Card
        self.health_card.update_health(sys_m.health_state, sys_m.health_description)
        
        # 3. Update Hardware KPI Card
        ram_pct = router.ram_usage_percent
        self.hw_card.update_values(
            f"{router.cpu_load}%", 
            f"RAM: {ram_pct:.0f}% | Libre: {router.free_memory // 1_000_000}MB"
        )
        
        # 4. Update Latency KPI Card
        self.ping_card.update_values(
            f"{sys_m.ping_avg_ms:.0f} ms | {sys_m.ping_loss_percent}% loss",
            f"GW: {sys_m.gateway_ping:.1f} ms | DNS: 8.8.8.8"
        )
        
        # 5. Update Security KPI Card
        temp_val = router.temperature
        self.security_card.update_values(
            f"{sys_m.firewall_drops_total} blq",
            f"Temp: {temp_val}°C | Volt: {router.voltage:.1f}V"
        )
        
        # 6. Update WAN Cards
        # Max capacity assumed 100Mbps (100,000,000 bps)
        self.wan1_card.update_traffic(net.wan1_rx, net.wan1_tx, 100_000_000.0)
        self.wan2_card.update_traffic(net.wan2_rx, net.wan2_tx, 100_000_000.0)
        
        # 7. Redraw Matplotlib chart
        self.charts_view.update_chart()
        
        # 8. Update Alerts Lists (active alerts list, vpn, top interfaces)
        self.alerts_view.update_data()
        
        # 9. Update event logs terminal
        self._update_log_terminal()

    def _update_log_terminal(self) -> None:
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        
        logs = self.controller.system_model.recent_logs
        if not logs:
            self.log_textbox.insert(tk.END, "Monitoreo de eventos RouterOS activo... sin novedades.")
        else:
            for l in logs:
                self.log_textbox.insert(tk.END, f"{l}\n")
                
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see(tk.END)

    def _on_toggle_theme(self) -> None:
        self.theme_controller.toggle()

    def _on_toggle_settings(self) -> None:
        if self.settings_open:
            # Hide sidebar (collapse width to 0)
            self.sidebar_frame.configure(width=0)
            self.grid_columnconfigure(1, weight=0)
            self.settings_open = False
        else:
            # Show sidebar (expand width to 320)
            self.sidebar_frame.configure(width=320)
            self.grid_columnconfigure(1, weight=0)
            self.settings_open = True

    def _on_save_settings(self, new_settings: Dict[str, Any]) -> None:
        self.controller.save_settings(new_settings)
        # Hide sidebar on success
        self._on_toggle_settings()
        # Pop success box
        tk.messagebox.showinfo("Configuración", "Los ajustes se guardaron y aplicaron correctamente.")

    def _on_run_diagnostics(self) -> None:
        # Change diagnostics button to show progress
        self.diag_btn.configure(state="disabled", text="Diagnosing...")
        
        results_popup = tk.Toplevel(self)
        results_popup.title("Ejecutando Diagnóstico de Sistema")
        results_popup.geometry("500x380")
        results_popup.transient(self)
        results_popup.grab_set()
        
        # Popup Styling depending on theme
        colors = self.theme_controller.theme_manager.colors
        theme_name = self.theme_controller.theme_manager.current_theme_name
        results_popup.configure(bg=colors.get("bg_card", "#0D1117"))
        
        title_lbl = ctk.CTkLabel(
            results_popup,
            text="DIAGNÓSTICO OPERATIVO EN CURSO",
            font=("Inter", 12, "bold"),
            text_color=colors.get("brand_blue", "#58A6FF")
        )
        title_lbl.pack(pady=(16, 8))
        
        # Progress bar
        prog_bar = ctk.CTkProgressBar(results_popup, width=400)
        prog_bar.set(0.0)
        prog_bar.pack(pady=10)
        
        prog_val_lbl = ctk.CTkLabel(
            results_popup,
            text="Iniciando comprobaciones...",
            font=("Inter", 11),
            text_color=colors.get("text_muted", "#8B949E")
        )
        prog_val_lbl.pack(pady=(0, 10))
        
        # Results text container
        res_box = ctk.CTkTextbox(
            results_popup,
            width=440,
            height=200,
            font=("JetBrains Mono", 9),
            state="disabled",
            fg_color="#010409" if theme_name == "dark" else "#F9FAFB",
            text_color="#FFFFFF" if theme_name == "dark" else "#1F2328"
        )
        res_box.pack(padx=16, pady=10)
        
        def update_progress_ui(prog: float):
            # Scale 0-100 to 0.0-1.0
            prog_bar.set(prog / 100.0)
            prog_val_lbl.configure(text=f"Progreso: {prog:.0f}%")
            results_popup.update_idletasks()
            
        def on_item_added(item: Dict[str, Any]):
            res_box.configure(state="normal")
            status = item["status"]
            icon = "[✓]" if status == "PASS" else "[!]" if status == "WARN" else "[X]"
            res_box.insert(tk.END, f"{icon} {item['name']}: {item['value']}\n    ({item['notes']})\n\n")
            res_box.configure(state="disabled")
            res_box.see(tk.END)
            results_popup.update_idletasks()

        def on_diagnostics_complete(report_path: str):
            # Re-enable button in main window
            self.diag_btn.configure(state="normal", text="Run Diagnostics")
            
            prog_val_lbl.configure(text="Diagnóstico Completado con Éxito")
            
            # Add close button to popup
            close_btn = ctk.CTkButton(
                results_popup,
                text="Cerrar & Ver Reporte",
                font=("Inter", 11, "bold"),
                fg_color=colors.get("brand_blue", "#58A6FF"),
                command=lambda: [results_popup.destroy(), self._open_html_report(report_path)]
            )
            close_btn.pack(pady=12)
            
        # Trigger execution in background via Controller
        self.controller.diagnostics_controller.run_diagnostics(
            self.controller.latest_payload,
            update_progress_ui,
            on_item_added,
            on_diagnostics_complete
        )

    def _open_html_report(self, report_path: str) -> None:
        # Open in web browser
        import webbrowser
        abs_path = os.path.abspath(report_path)
        webbrowser.open(f"file:///{abs_path}")

    def _on_closing(self) -> None:
        self.controller.stop_monitoring()
        self.destroy()
