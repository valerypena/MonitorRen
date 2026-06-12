import customtkinter as ctk
from typing import Dict, Any, Callable
from themes.theme_manager import ThemeManager

class ThemeController:
    def __init__(self):
        self.theme_manager = ThemeManager()
        
    def register_view(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        """
        Views register their update callbacks here.
        Whenever the theme changes, this callback runs to update view styling.
        """
        self.theme_manager.register_callback(callback)

    def remove_view(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        self.theme_manager.remove_callback(callback)

    def set_light(self) -> None:
        ctk.set_appearance_mode("light")
        self.theme_manager.set_light_theme()

    def set_dark(self) -> None:
        ctk.set_appearance_mode("dark")
        self.theme_manager.set_dark_theme()

    def toggle(self) -> None:
        current = self.theme_manager.current_theme_name
        if current == "dark":
            self.set_light()
        else:
            self.set_dark()
            
    def apply_current_theme(self) -> None:
        """
        Sets ctk appearance mode to the saved config theme.
        """
        theme_name = self.theme_manager.current_theme_name
        ctk.set_appearance_mode(theme_name)
