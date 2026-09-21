"""Login screen."""

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from gui.dashboard import Dashboard
from managers.auth_manager import AuthManager


class LoginWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Viva La Vida")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(fg_color="#111820")

        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        logo = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(72, 72))
        card = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=12)
        card.pack(expand=True, fill="both", padx=32, pady=32)
        ctk.CTkLabel(card, image=logo, text="").pack(pady=(34, 14))
        ctk.CTkLabel(card, text="Viva La Vida", text_color="#2A9D9A", font=ctk.CTkFont(size=30, weight="bold")).pack()
        ctk.CTkLabel(card, text="Where knowledge thrives.", text_color="#9AA7B0").pack(pady=(0, 28))
        self.username_entry = ctk.CTkEntry(card, placeholder_text="Username", height=42, corner_radius=9)
        self.username_entry.pack(pady=6, padx=34, fill="x")
        self.password_entry = ctk.CTkEntry(card, placeholder_text="Password", show="*", height=42, corner_radius=9)
        self.password_entry.pack(pady=6, padx=34, fill="x")
        self.status_label = ctk.CTkLabel(card, text="", text_color="#D17A67", wraplength=330)
        self.status_label.pack(pady=(8, 0))
        ctk.CTkButton(card, text="Sign in",
                     command=self.login, height=42, 
                     corner_radius=8, fg_color="#2A9D9A",
                     hover_color="#21817F").pack(pady=(0, 0),
                     padx=50,fill="x")
        self.bind("<Return>", lambda _: self.login())

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.status_label.configure(text="Enter both username and password.", text_color="#d9534f")
            return

        try:
            user = AuthManager().authenticate(username, password)
        except Exception as error:
            self.status_label.configure(text="An error occurred while trying to authenticate.", text_color="#d9534f")
            return
        if user is None:
            self.status_label.configure(text="Invalid username or password.", text_color="#d9534f")
            return
        self.withdraw()
        Dashboard(self, user)
