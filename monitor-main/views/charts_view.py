import customtkinter as ctk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from typing import Dict, Any, List
from models.network_model import NetworkModel

class ChartsView(ctk.CTkFrame):
    def __init__(self, parent: Any, model: NetworkModel, theme_controller: Any):
        super().__init__(parent, fg_color="transparent")
        self.model = model
        self.theme_controller = theme_controller
        
        # Configure Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create matplotlib figure & axes
        self.fig, self.ax = plt.subplots(figsize=(6, 2.8), dpi=100)
        self.fig.tight_layout(pad=1.5)
        
        # Create Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        # Register for theme updates
        self.theme_controller.register_view(self.apply_theme)
        
    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        bg_card = colors.get("bg_card", "#0D1117")
        text_main = colors.get("text_main", "#FFFFFF")
        text_muted = colors.get("text_muted", "#8B949E")
        grid_color = colors.get("chart_grid", "rgba(255,255,255,0.05)")
        
        # Style Figure
        self.fig.patch.set_facecolor(bg_card)
        self.ax.set_facecolor(bg_card)
        
        # Axis label colors
        self.ax.tick_params(colors=text_muted, labelsize=8)
        self.ax.xaxis.label.set_color(text_muted)
        self.ax.yaxis.label.set_color(text_muted)
        
        # Title & spines
        self.ax.title.set_color(text_main)
        for spine in self.ax.spines.values():
            spine.set_color(grid_color)
            
        # Grid lines
        self.ax.grid(True, color=grid_color, linestyle="--", linewidth=0.5)
        
        # Refresh drawing
        self.canvas.draw_idle()

    def update_chart(self) -> None:
        self.ax.clear()
        
        # Get historical data from model
        y1 = list(self.model.history_wan1_rx)
        y2 = list(self.model.history_wan2_rx)
        x = list(range(len(y1)))
        
        colors = self.theme_controller.theme_manager.colors
        brand_red = colors.get("brand_red", "#F85149")
        brand_blue = colors.get("brand_blue", "#58A6FF")
        text_muted = colors.get("text_muted", "#8B949E")
        grid_color = colors.get("chart_grid", "rgba(255, 255, 255, 0.05)")
        
        # Re-apply theme configuration that clear() wiped out
        self.ax.set_facecolor(colors.get("bg_card", "#0D1117"))
        self.ax.tick_params(colors=text_muted, labelsize=8)
        self.ax.grid(True, color=grid_color, linestyle="--", linewidth=0.5)
        
        for spine in self.ax.spines.values():
            spine.set_color(grid_color)
            
        # Plot lines
        if y1:
            self.ax.plot(x, y1, color=brand_red, label="WAN1 Claro (Kbps)", linewidth=1.5)
        if y2:
            self.ax.plot(x, y2, color=brand_blue, label="WAN2 Movistar (Kbps)", linewidth=1.5)
            
        # Legend and Labels
        self.ax.legend(loc="upper left", facecolor=colors.get("bg_card", "#0D1117"), edgecolor=grid_color, fontsize=8, labelcolor=colors.get("text_main", "#FFFFFF"))
        self.ax.set_ylabel("Velocidad (Kbps)", fontsize=8, color=text_muted)
        self.ax.set_xlabel("Tiempo (segundos)", fontsize=8, color=text_muted)
        
        # Redraw
        self.canvas.draw_idle()

    def destroy(self):
        # Deregister callback to prevent memory leaks
        self.theme_controller.remove_view(self.apply_theme)
        super().destroy()
