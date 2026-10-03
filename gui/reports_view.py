"""Reports screen with smooth refresh and scrollable fines list."""

from decimal import Decimal, InvalidOperation

import customtkinter as ctk

from managers.report_manager import ReportManager
from managers.fine_manager import FineManager
from utils.helpers import enable_mousewheel


def format_peso(amount) -> str:
    """Formats any numeric value (int, float, Decimal, numeric string) as pesos, e.g. ₱1,250.00."""
    try:
        return f"₱{Decimal(str(amount if amount is not None else 0)):,.2f}"
    except (InvalidOperation, ValueError):
        return f"₱{amount}"


class ReportsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # Top Summary Panel
        self.panel = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        self.panel.pack(fill="x", pady=(0, 12))

        # Status / Feedback Label
        self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
        self.status.pack(anchor="w", pady=(0, 6))

        # Unpaid Fines Container Card
        fines_card = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        fines_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            fines_card,
            text="Unpaid Fines",
            text_color="#E8EDF0",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 6))

        # Scrollable area para sa Fines para hindi lumagpas sa screen
        self.fines_rows = ctk.CTkScrollableFrame(fines_card, fg_color="transparent")
        self.fines_rows.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        enable_mousewheel(self.fines_rows)

        self.refresh()

    def refresh(self):
        # 1. Refresh Summary Stats
        for widget in self.panel.winfo_children():
            widget.destroy()

        try:
            summary_data = ReportManager().summary()
            for label, value in summary_data.items():
                row = ctk.CTkFrame(self.panel, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=6)

                ctk.CTkLabel(
                    row,
                    text=label.replace("_", " ").title(),
                    text_color="#A6B1B8",
                    anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row,
                    text=str(value),
                    text_color="#2A9D9A",
                    font=ctk.CTkFont(size=16, weight="bold")
                ).pack(side="right")
        except Exception as error:
            ctk.CTkLabel(self.panel, text=f"Unable to load summary: {error}", text_color="#D17A67").pack(anchor="w", padx=18, pady=12)

        # 2. Refresh Unpaid Fines List
        for widget in self.fines_rows.winfo_children():
            widget.destroy()

        try:
            unpaid_fines = FineManager().list_unpaid()
            for fine in unpaid_fines:
                row = ctk.CTkFrame(self.fines_rows, fg_color="#202D37", corner_radius=7)
                row.pack(fill="x", pady=4, padx=6)

                amount_str = format_peso(fine["amount"])

                ctk.CTkLabel(
                    row,
                    text=f"{fine['name']}  ·  {amount_str}  ·  {fine['reason']}",
                    text_color="#A6B1B8"
                ).pack(side="left", padx=12, pady=8)

                ctk.CTkButton(
                    row,
                    text="Mark paid",
                    command=lambda fine_id=fine["id"]: self.pay_fine(fine_id),
                    width=82,
                    height=26,
                    corner_radius=6,
                    fg_color="#2A9D9A",
                    hover_color="#21817F"
                ).pack(side="right", padx=10, pady=6)

            if not unpaid_fines:
                ctk.CTkLabel(self.fines_rows, text="No unpaid fines at this time.", text_color="#A6B1B8").pack(anchor="w", padx=12, pady=12)

        except Exception as error:
            ctk.CTkLabel(self.fines_rows, text=f"Unable to load fines: {error}", text_color="#D17A67").pack(anchor="w", padx=12, pady=12)

    def pay_fine(self, fine_id: int):
        try:
            FineManager().pay(fine_id)
            self.status.configure(text="Fine marked as paid.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to process payment: {error}", text_color="#D17A67")