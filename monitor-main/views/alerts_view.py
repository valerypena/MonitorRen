import customtkinter as ctk
from typing import Dict, Any, List
from models.system_model import SystemModel
from models.network_model import NetworkModel

class AlertsView(ctk.CTkFrame):
    def __init__(self, parent: Any, system_model: SystemModel, network_model: NetworkModel, theme_controller: Any):
        super().__init__(parent, fg_color="transparent")
        self.system_model = system_model
        self.network_model = network_model
        self.theme_controller = theme_controller
        
        # Configure layout (3 equal columns)
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")
        self.grid_columnconfigure(2, weight=1, uniform="col")
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Active Alerts Frame
        self.alerts_card = ctk.CTkFrame(self, corner_radius=12, border_width=2)
        self.alerts_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self._setup_sub_card(self.alerts_card, "ALERTAS ACTIVAS")
        self.alerts_container = ctk.CTkScrollableFrame(self.alerts_card, fg_color="transparent", height=120)
        self.alerts_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 2. Top Consumers Frame
        self.consumers_card = ctk.CTkFrame(self, corner_radius=12, border_width=2)
        self.consumers_card.grid(row=0, column=1, padx=8, sticky="nsew")
        self._setup_sub_card(self.consumers_card, "TOP CONSUMIDORES RED")
        self.consumers_container = ctk.CTkScrollableFrame(self.consumers_card, fg_color="transparent", height=120)
        self.consumers_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # 3. VPN Protocol distribution Frame
        self.vpn_card = ctk.CTkFrame(self, corner_radius=12, border_width=2)
        self.vpn_card.grid(row=0, column=2, padx=(8, 0), sticky="nsew")
        self._setup_sub_card(self.vpn_card, "SESIONES VPN POR PERFIL")
        self.vpn_container = ctk.CTkScrollableFrame(self.vpn_card, fg_color="transparent", height=120)
        self.vpn_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Subscribe to theme updates
        self.theme_controller.register_view(self.apply_theme)

    def _setup_sub_card(self, card_frame: ctk.CTkFrame, title: str) -> None:
        card_frame.pack_propagate(False)
        lbl = ctk.CTkLabel(
            card_frame, 
            text=title, 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        lbl.pack(fill="x", padx=16, pady=12)
        card_frame.title_label = lbl # reference to edit color later

    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        bg_card = colors.get("bg_card", "#0D1117")
        border = colors.get("border_card", "#30363D")
        text_muted = colors.get("text_muted", "#8B949E")
        
        for card in [self.alerts_card, self.consumers_card, self.vpn_card]:
            card.configure(
                fg_color=bg_card,
                border_color=border
            )
            card.title_label.configure(text_color=text_muted)
            
        self.update_data()

    def update_data(self) -> None:
        colors = self.theme_controller.theme_manager.colors
        
        # 1. Clear & Redraw Alerts
        for widget in self.alerts_container.winfo_children():
            widget.destroy()
            
        alerts = self.system_model.active_alerts
        if not alerts:
            lbl = ctk.CTkLabel(
                self.alerts_container, 
                text="Sin alertas activas.", 
                font=("Inter", 11, "italic"),
                text_color=colors.get("text_muted", "#8B949E")
            )
            lbl.pack(pady=10)
        else:
            for a in alerts:
                # Severity badge colors
                sev = a.get("severity", "warning").lower()
                sev_bg = "#FEF08A" if sev == "warning" else "#FDE8E8"
                sev_fg = "#713F12" if sev == "warning" else "#9B1C1C"
                sev_text = "WARN" if sev == "warning" else "CRIT"
                
                alert_row = ctk.CTkFrame(self.alerts_container, fg_color="transparent")
                alert_row.pack(fill="x", pady=2)
                
                badge = ctk.CTkLabel(
                    alert_row,
                    text=sev_text,
                    font=("Inter", 9, "bold"),
                    text_color=sev_fg,
                    fg_color=sev_bg,
                    corner_radius=4,
                    width=42,
                    height=18
                )
                badge.pack(side="left", padx=(0, 6))
                
                msg_lbl = ctk.CTkLabel(
                    alert_row,
                    text=a.get("message", ""),
                    font=("Inter", 11),
                    text_color=colors.get("text_main", "#FFFFFF"),
                    anchor="w",
                    wraplength=170
                )
                msg_lbl.pack(side="left", fill="x", expand=True)

        # 2. Clear & Redraw Consumers
        for widget in self.consumers_container.winfo_children():
            widget.destroy()
            
        consumers = self.network_model.top_consumers
        if not consumers:
            lbl = ctk.CTkLabel(
                self.consumers_container, 
                text="No hay interfaces de tráfico activas.", 
                font=("Inter", 11, "italic"),
                text_color=colors.get("text_muted", "#8B949E")
            )
            lbl.pack(pady=10)
        else:
            for item in consumers:
                row = ctk.CTkFrame(self.consumers_container, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                name_lbl = ctk.CTkLabel(
                    row,
                    text=item.get("Name", "interface"),
                    font=("Inter", 11, "bold"),
                    text_color=colors.get("text_main", "#FFFFFF"),
                    anchor="w"
                )
                name_lbl.pack(side="left")
                
                # Format speed (e.g. Rx bps)
                rx_val = item.get("Rx", 0)
                if rx_val > 1_000_000:
                    speed_str = f"{rx_val/1_000_000:.1f} Mbps"
                else:
                    speed_str = f"{rx_val/1000:.1f} Kbps"
                    
                val_lbl = ctk.CTkLabel(
                    row,
                    text=speed_str,
                    font=("Inter", 11),
                    text_color=colors.get("brand_blue", "#58A6FF"),
                    anchor="e"
                )
                val_lbl.pack(side="right", fill="x", expand=True)

        # 3. Clear & Redraw VPN Profiles
        for widget in self.vpn_container.winfo_children():
            widget.destroy()
            
        vpn_profiles = self.network_model.vpn_profiles_detail
        if not vpn_profiles:
            lbl = ctk.CTkLabel(
                self.vpn_container, 
                text="No hay sesiones VPN activas.", 
                font=("Inter", 11, "italic"),
                text_color=colors.get("text_muted", "#8B949E")
            )
            lbl.pack(pady=10)
        else:
            for prof, count in vpn_profiles.items():
                row = ctk.CTkFrame(self.vpn_container, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                prof_lbl = ctk.CTkLabel(
                    row,
                    text=prof,
                    font=("Inter", 11),
                    text_color=colors.get("text_main", "#FFFFFF"),
                    anchor="w"
                )
                prof_lbl.pack(side="left")
                
                cnt_lbl = ctk.CTkLabel(
                    row,
                    text=f"{count} túneles",
                    font=("Inter", 11, "bold"),
                    text_color=colors.get("brand_green", "#3FB950"),
                    anchor="e"
                )
                cnt_lbl.pack(side="right", fill="x", expand=True)

    def destroy(self):
        self.theme_controller.remove_view(self.apply_theme)
        super().destroy()
