import customtkinter as ctk
import tkinter as tk
from typing import Dict, Any, List, Optional

class MetricCard(ctk.CTkFrame):
    def __init__(self, parent: Any, label_text: str, value_text: str, sub_text: str = "", theme_controller: Any = None):
        self.theme_controller = theme_controller
        self.normal_border_color = "#30363D"
        self.hover_border_color = "#58A6FF"
        
        super().__init__(
            parent, 
            corner_radius=12, 
            border_width=2,
            fg_color="transparent"
        )
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Label (Top)
        self.label = ctk.CTkLabel(
            self, 
            text=label_text.upper(), 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        self.label.grid(row=0, column=0, padx=16, pady=(14, 2), sticky="ew")
        
        # Metric Value (Middle)
        self.value_label = ctk.CTkLabel(
            self, 
            text=value_text, 
            font=("Inter", 20, "bold"),
            anchor="w"
        )
        self.value_label.grid(row=1, column=0, padx=16, pady=2, sticky="ew")
        
        # Sub-metric (Bottom)
        self.sub_label = ctk.CTkLabel(
            self, 
            text=sub_text, 
            font=("Inter", 11),
            anchor="w"
        )
        self.sub_label.grid(row=2, column=0, padx=16, pady=(2, 14), sticky="sew")
        
        # Hover events bindings recursively to child components so hover triggers anywhere inside card!
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        for child in [self.label, self.value_label, self.sub_label]:
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)
            
        if self.theme_controller:
            self.theme_controller.register_view(self.apply_theme)
            
    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        self.normal_border_color = colors.get("border_card", "#30363D")
        self.hover_border_color = colors.get("border_card_hover", "#58A6FF")
        
        self.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=self.normal_border_color
        )
        
        self.label.configure(text_color=colors.get("text_muted", "#8B949E"))
        self.value_label.configure(text_color=colors.get("text_main", "#FFFFFF"))
        self.sub_label.configure(text_color=colors.get("text_muted", "#8B949E"))

    def _on_enter(self, event: Any) -> None:
        self.configure(border_color=self.hover_border_color)

    def _on_leave(self, event: Any) -> None:
        self.configure(border_color=self.normal_border_color)

    def update_values(self, value: str, sub_value: str = "") -> None:
        self.value_label.configure(text=value)
        if sub_value:
            self.sub_label.configure(text=sub_value)


class SystemHealthCard(ctk.CTkFrame):
    def __init__(self, parent: Any, theme_controller: Any):
        self.theme_controller = theme_controller
        self.normal_border_color = "#30363D"
        self.hover_border_color = "#58A6FF"
        
        super().__init__(
            parent, 
            corner_radius=12, 
            border_width=2,
            fg_color="transparent"
        )
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Label
        self.label = ctk.CTkLabel(
            self, 
            text="SALUD DEL SISTEMA", 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        self.label.grid(row=0, column=0, padx=16, pady=(14, 2), sticky="ew")
        
        # Indicator Badge (Horizontal Flow: Status Icon + Status Text)
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, padx=16, pady=2, sticky="ew")
        
        self.icon_label = ctk.CTkLabel(
            self.status_frame,
            text="✓",
            font=("Inter", 22, "bold"),
            width=20
        )
        self.icon_label.pack(side="left", padx=(0, 8))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Sistema Operativo",
            font=("Inter", 16, "bold"),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # Detail Text
        self.detail_label = ctk.CTkLabel(
            self,
            text="Todos los servicios e interfaces operan con normalidad.",
            font=("Inter", 11),
            anchor="w",
            wraplength=200
        )
        self.detail_label.grid(row=2, column=0, padx=16, pady=(2, 14), sticky="sew")
        
        # Bind hover states
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        for child in [self.label, self.status_frame, self.icon_label, self.status_label, self.detail_label]:
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)
            
        if self.theme_controller:
            self.theme_controller.register_view(self.apply_theme)

    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        self.normal_border_color = colors.get("border_card", "#30363D")
        self.hover_border_color = colors.get("border_card_hover", "#58A6FF")
        
        self.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=self.normal_border_color
        )
        
        self.label.configure(text_color=colors.get("text_muted", "#8B949E"))
        self.detail_label.configure(text_color=colors.get("text_muted", "#8B949E"))

    def _on_enter(self, event: Any) -> None:
        self.configure(border_color=self.hover_border_color)

    def _on_leave(self, event: Any) -> None:
        self.configure(border_color=self.normal_border_color)

    def update_health(self, state: str, description: str) -> None:
        """
        state should be: "GREEN", "YELLOW", "RED"
        """
        colors = self.theme_controller.theme_manager.colors
        
        if state == "GREEN":
            icon = "✓"
            text_color = colors.get("brand_green", "#3FB950")
            detail = "Todos los servicios e interfaces operan con normalidad."
        elif state == "YELLOW":
            icon = "⚠"
            text_color = colors.get("brand_warn", "#D29922")
            detail = "Monitoreo detecta degradaciones parciales en el sistema."
        else: # RED
            icon = "✖"
            text_color = colors.get("brand_red", "#F85149")
            detail = "Caída de servicio o pérdida de enlace crítica registrada."
            
        self.icon_label.configure(text=icon, text_color=text_color)
        self.status_label.configure(text=description, text_color=text_color)
        self.detail_label.configure(text=detail)


class WANCard(ctk.CTkFrame):
    def __init__(self, parent: Any, title: str, accent_color_key: str, theme_controller: Any):
        self.theme_controller = theme_controller
        self.accent_color_key = accent_color_key
        self.normal_border_color = "#30363D"
        self.hover_border_color = "#58A6FF"
        
        super().__init__(
            parent, 
            corner_radius=12, 
            border_width=2,
            fg_color="transparent"
        )
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        
        # Details Panel (Left Column)
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=0, rowspan=3, padx=(16, 8), pady=14, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        self.details_frame.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(
            self.details_frame, 
            text=title.upper(), 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, pady=(0, 2), sticky="ew")
        
        self.rx_label = ctk.CTkLabel(
            self.details_frame, 
            text="0 Kbps", 
            font=("Inter", 20, "bold"),
            anchor="w"
        )
        self.rx_label.grid(row=1, column=0, pady=2, sticky="ew")
        
        self.tx_label = ctk.CTkLabel(
            self.details_frame, 
            text="TX: 0 Kbps", 
            font=("Inter", 11),
            anchor="w"
        )
        self.tx_label.grid(row=2, column=0, pady=(2, 0), sticky="sew")
        
        # Circular Bar representation (Right Column, using custom canvas)
        self.canvas_width = 80
        self.canvas_height = 80
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=self.canvas_height,
            bd=0,
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=1, rowspan=3, padx=(8, 16), pady=14, sticky="center")
        
        # Hover events bindings recursively
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        for child in [self.details_frame, self.title_label, self.rx_label, self.tx_label]:
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)
            
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        
        if self.theme_controller:
            self.theme_controller.register_view(self.apply_theme)

    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        self.normal_border_color = colors.get("border_card", "#30363D")
        self.hover_border_color = colors.get("border_card_hover", "#58A6FF")
        
        self.configure(
            fg_color=colors.get("bg_card", "#0D1117"),
            border_color=self.normal_border_color
        )
        
        accent_color = colors.get(self.accent_color_key, "#58A6FF")
        self.title_label.configure(text_color=accent_color)
        self.rx_label.configure(text_color=colors.get("text_main", "#FFFFFF"))
        self.tx_label.configure(text_color=colors.get("text_muted", "#8B949E"))
        
        self.canvas.configure(
            bg=colors.get("bg_card", "#0D1117"),
            highlightbackground=colors.get("bg_card", "#0D1117")
        )
        self.draw_ring(0.0) # Redraw ring background on theme change

    def _on_enter(self, event: Any) -> None:
        self.configure(border_color=self.hover_border_color)

    def _on_leave(self, event: Any) -> None:
        self.configure(border_color=self.normal_border_color)

    def draw_ring(self, pct: float) -> None:
        self.canvas.delete("all")
        
        colors = self.theme_controller.theme_manager.colors
        bg_card = colors.get("bg_card", "#0D1117")
        accent = colors.get(self.accent_color_key, "#58A6FF")
        
        # Dimensions
        pad = 6
        x0 = pad
        y0 = pad
        x1 = self.canvas_width - pad
        y1 = self.canvas_height - pad
        
        # Draw background ring arc
        self.canvas.create_arc(
            x0, y0, x1, y1,
            start=0, extent=359,
            style="slice",
            outline=colors.get("chart_grid", "rgba(255,255,255,0.05)"),
            width=5
        )
        
        # Draw dynamic value ring arc (from top: 90 degrees)
        angle = min(359.9, max(0.0, pct * 360.0))
        if angle > 0:
            self.canvas.create_arc(
                x0, y0, x1, y1,
                start=90, extent=-angle,
                style="arc",
                outline=accent,
                width=5
            )
            
        # Draw inner text
        self.canvas.create_text(
            self.canvas_width // 2,
            self.canvas_height // 2,
            text=f"{pct*100:.0f}%",
            fill=colors.get("text_main", "#FFFFFF"),
            font=("Inter", 10, "bold")
        )

    def update_traffic(self, rx_bps: float, tx_bps: float, max_capacity_bps: float = 100_000_000.0) -> None:
        """
        Updates text displays and the visual progress ring.
        max_capacity_bps sets the 100% mark (default 100 Mbps).
        """
        rx_kbps = rx_bps / 1000.0
        tx_kbps = tx_bps / 1000.0
        
        # Display appropriate units
        if rx_kbps > 1000:
            self.rx_label.configure(text=f"{rx_kbps/1000.0:.2f} Mbps")
        else:
            self.rx_label.configure(text=f"{rx_kbps:.1f} Kbps")
            
        if tx_kbps > 1000:
            self.tx_label.configure(text=f"TX: {tx_kbps/1000.0:.2f} Mbps")
        else:
            self.tx_label.configure(text=f"TX: {tx_kbps:.1f} Kbps")
            
        # Calculate percentage utilization
        pct = rx_bps / max_capacity_bps
        self.draw_ring(min(1.0, max(0.0, pct)))
