import json
import os
from typing import Dict, Any, Callable, List
from themes.light_theme import THEME as LIGHT_THEME
from themes.dark_theme import THEME as DARK_THEME

class ThemeManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")
        self.current_theme_name = "dark"
        self.callbacks: List[Callable[[str, Dict[str, str]], None]] = []
        self.load_from_config()

    def load_from_config(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.current_theme_name = config.get("theme", {}).get("current_theme", "dark")
            except Exception as e:
                print(f"[ThemeManager] Error loading config: {e}")

    def save_to_config(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                if "theme" not in config:
                    config["theme"] = {}
                config["theme"]["current_theme"] = self.current_theme_name
                
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                print(f"[ThemeManager] Error saving config: {e}")

    @property
    def colors(self) -> Dict[str, str]:
        return LIGHT_THEME if self.current_theme_name == "light" else DARK_THEME

    def get_color(self, key: str) -> str:
        return self.colors.get(key, "#000000")

    def register_callback(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            # Call immediately to apply initial theme
            try:
                callback(self.current_theme_name, self.colors)
            except Exception as e:
                print(f"[ThemeManager] Callback error on registration: {e}")

    def remove_callback(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def set_light_theme(self) -> None:
        if self.current_theme_name != "light":
            self.current_theme_name = "light"
            self.save_to_config()
            self._notify()

    def set_dark_theme(self) -> None:
        if self.current_theme_name != "dark":
            self.current_theme_name = "dark"
            self.save_to_config()
            self._notify()

    def toggle_theme(self) -> None:
        if self.current_theme_name == "dark":
            self.set_light_theme()
        else:
            self.set_dark_theme()

    def _notify(self) -> None:
        theme_name = self.current_theme_name
        colors = self.colors
        for callback in self.callbacks:
            try:
                callback(theme_name, colors)
            except Exception as e:
                print(f"[ThemeManager] Callback error: {e}")
