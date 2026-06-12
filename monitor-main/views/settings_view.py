import customtkinter as ctk
from typing import Dict, Any, Callable

class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent: Any, initial_settings: Dict[str, Any], on_save_callback: Callable[[Dict[str, Any]], None], theme_controller: Any):
        super().__init__(parent, fg_color="transparent")
        self.initial_settings = initial_settings
        self.on_save = on_save_callback
        self.theme_controller = theme_controller
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        
        row = 0
        
        # Section: Mikrotik Config
        self._add_section_header("Configuración MikroTik", row)
        row += 1
        
        self.host_entry = self._add_entry_row("Dirección IP:", initial_settings.get("mikrotik", {}).get("host", "10.24.0.1"), row)
        row += 1
        self.user_entry = self._add_entry_row("Usuario API:", initial_settings.get("mikrotik", {}).get("username", "admin"), row)
        row += 1
        self.pass_entry = self._add_entry_row("Contraseña:", initial_settings.get("mikrotik", {}).get("password", ""), row, show="*")
        row += 1
        
        # Section: Database Config
        self._add_section_header("Configuración MySQL (Persistencia)", row)
        row += 1
        
        self.db_host_entry = self._add_entry_row("Servidor Host:", initial_settings.get("database", {}).get("host", "localhost"), row)
        row += 1
        self.db_user_entry = self._add_entry_row("Usuario DB:", initial_settings.get("database", {}).get("user", "root"), row)
        row += 1
        self.db_pass_entry = self._add_entry_row("Contraseña:", initial_settings.get("database", {}).get("password", ""), row, show="*")
        row += 1
        self.db_name_entry = self._add_entry_row("Base de Datos:", initial_settings.get("database", {}).get("database", "ren_monitor"), row)
        row += 1
        
        # Section: Email Config
        self._add_section_header("Configuración de Alertas por Correo", row)
        row += 1
        
        self.smtp_entry = self._add_entry_row("Servidor SMTP:", initial_settings.get("email", {}).get("smtp_server", "smtp.gmail.com"), row)
        row += 1
        self.port_entry = self._add_entry_row("Puerto SMTP:", str(initial_settings.get("email", {}).get("smtp_port", 587)), row)
        row += 1
        self.email_user_entry = self._add_entry_row("Correo Emisor:", initial_settings.get("email", {}).get("email_user", ""), row)
        row += 1
        self.email_pass_entry = self._add_entry_row("Contraseña de Aplicación:", initial_settings.get("email", {}).get("email_password", ""), row, show="*")
        row += 1
        self.recipient_entry = self._add_entry_row("Correo Destinatario:", initial_settings.get("email", {}).get("alert_recipient", ""), row)
        row += 1
        self.cooldown_entry = self._add_entry_row("Enfriamiento Alertas (s):", str(initial_settings.get("email", {}).get("cooldown", 300)), row)
        row += 1
        
        # Save Button
        self.save_btn = ctk.CTkButton(
            self, 
            text="Guardar Cambios", 
            font=("Inter", 12, "bold"),
            command=self._save_clicked
        )
        self.save_btn.grid(row=row, column=0, columnspan=2, padx=16, pady=24, sticky="ew")
        
        self.theme_controller.register_view(self.apply_theme)

    def _add_section_header(self, text: str, row: int) -> None:
        lbl = ctk.CTkLabel(
            self, 
            text=text.upper(), 
            font=("Inter", 10, "bold"),
            anchor="w"
        )
        lbl.grid(row=row, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="ew")
        # Save reference for theme changing
        if not hasattr(self, "headers"):
            self.headers = []
        self.headers.append(lbl)

    def _add_entry_row(self, label_text: str, default_val: str, row: int, show: str = "") -> ctk.CTkEntry:
        lbl = ctk.CTkLabel(
            self, 
            text=label_text, 
            font=("Inter", 11),
            anchor="w"
        )
        lbl.grid(row=row, column=0, padx=(16, 8), pady=4, sticky="ew")
        if not hasattr(self, "labels"):
            self.labels = []
        self.labels.append(lbl)
        
        entry = ctk.CTkEntry(
            self, 
            height=28, 
            font=("Inter", 11),
            show=show
        )
        entry.insert(0, default_val)
        entry.grid(row=row, column=1, padx=(8, 16), pady=4, sticky="ew")
        return entry

    def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        text_muted = colors.get("text_muted", "#8B949E")
        text_main = colors.get("text_main", "#FFFFFF")
        brand = colors.get("brand_blue", "#58A6FF")
        
        if hasattr(self, "headers"):
            for h in self.headers:
                h.configure(text_color=brand)
        if hasattr(self, "labels"):
            for l in self.labels:
                l.configure(text_color=text_main)
                
        self.save_btn.configure(
            fg_color=brand,
            hover_color=colors.get("border_card_hover", "#3B82F6"),
            text_color="#FFFFFF"
        )

    def _save_clicked(self) -> None:
        # Construct updated settings dictionary
        new_settings = {
            "mikrotik": {
                "host": self.host_entry.get().strip(),
                "username": self.user_entry.get().strip(),
                "password": self.pass_entry.get()
            },
            "database": {
                "host": self.db_host_entry.get().strip(),
                "user": self.db_user_entry.get().strip(),
                "password": self.db_pass_entry.get(),
                "database": self.db_name_entry.get().strip()
            },
            "email": {
                "smtp_server": self.smtp_entry.get().strip(),
                "smtp_port": int(self.port_entry.get().strip() or "587"),
                "email_user": self.email_user_entry.get().strip(),
                "email_password": self.email_pass_entry.get(),
                "alert_recipient": self.recipient_entry.get().strip(),
                "cooldown": int(self.cooldown_entry.get().strip() or "300")
            },
            "theme": self.initial_settings.get("theme", {"current_theme": "dark"})
        }
        self.on_save(new_settings)

    def destroy(self):
        self.theme_controller.remove_view(self.apply_theme)
        super().destroy()
