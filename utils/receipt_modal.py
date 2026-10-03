
import customtkinter as ctk
from models.invoice import Invoice
from managers.fine_manager import FineManager


class ReceiptModal(ctk.CTkToplevel):
    def __init__(self, master, transaction_title: str, invoice: Invoice):
        super().__init__(master)
        
        # Object Properties
        self.transaction_title = transaction_title
        self.invoice = invoice

        self._configure_window()
        self._build_header()
        self._build_details()
        self._build_actions()

    def _configure_window(self):
        self.title("Transaction Receipt")
        self.geometry("380x460")
        self.resizable(False, False)
        self.configure(fg_color="#1B252E")
        self.attributes("-topmost", True)

    def _build_header(self):
        ctk.CTkLabel(
            self, 
            text="LIBRARY DESK RECEIPT", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color="#2A9D9A"
        ).pack(pady=(22, 2))

        ctk.CTkLabel(
            self, 
            text=self.transaction_title.upper(), 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#E8EDF0"
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            self, 
            text=f"Processed: {FineManager.get_ph_now()}", 
            font=ctk.CTkFont(size=11), 
            text_color="#A6B1B8"
        ).pack(pady=(0, 10))

        ctk.CTkFrame(self, height=1, fg_color="#303D47").pack(fill="x", padx=20, pady=5)

    def _build_details(self):
        details_frame = ctk.CTkFrame(self, fg_color="#202D37", corner_radius=8)
        details_frame.pack(fill="both", expand=True, padx=20, pady=12)

        # Gamit ang encapsulated methods mula sa Invoice object
        data = {
            "Invoice ID": self.invoice.invoice_id,
            "Member ID": self.invoice.member_id,
            "Amount": self.invoice.get_formatted_amount(),
            "Status": self.invoice.get_status_label(),
        }

        for key, val in data.items():
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)

            ctk.CTkLabel(
                row, 
                text=f"{key}:", 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="#E8EDF0"
            ).pack(side="left")

            ctk.CTkLabel(
                row, 
                text=str(val), 
                font=ctk.CTkFont(size=12), 
                text_color="#2A9D9A" if key in ["Amount", "Status"] else "#A6B1B8"
            ).pack(side="right")

    def _build_actions(self):
        ctk.CTkButton(
            self, 
            text="Done / Close", 
            command=self.destroy, 
            height=36, 
            corner_radius=7, 
            fg_color="#2A9D9A", 
            hover_color="#21817F",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", padx=20, pady=(0, 20))