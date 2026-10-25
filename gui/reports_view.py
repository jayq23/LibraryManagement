# Reports screen with smooth refresh and scrollable, paginated fines list.

from decimal import Decimal, InvalidOperation

import customtkinter as ctk

from managers.report_manager import ReportManager
from managers.fine_manager import FineManager
from utils.helpers import enable_mousewheel
from utils.pager import Pager


# Handle format peso.
def format_peso(amount) -> str:
    try:
        return f"₱{Decimal(str(amount if amount is not None else 0)):,.2f}"
    except (InvalidOperation, ValueError):
        return f"₱{amount}"


class ReportsView(ctk.CTkFrame):
    PAGE_SIZE = 10  # Fine rows built per page.

    # Initialize the component.
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self._fines: list[dict] = []

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

        # Page controls (packed before the list so they always stay visible at the bottom).
        self.pager = Pager(fines_card, on_change=self._render_fines, page_size=self.PAGE_SIZE)
        self.pager.pack(side="bottom", fill="x", padx=12, pady=(0, 10))

        # Scrollable area para sa Fines para hindi lumagpas sa screen
        self.fines_rows = ctk.CTkScrollableFrame(fines_card, fg_color="transparent")
        self.fines_rows.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.pager.scroll_target = self.fines_rows
        enable_mousewheel(self.fines_rows)

        self.refresh()

    # Clear the fine rows currently on screen.
    def _clear_fines(self):
        for widget in self.fines_rows.winfo_children():
            widget.destroy()

    # Refresh refresh.
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

        # 2. Reload the unpaid fines, then draw the current page
        try:
            self._fines = FineManager().list_unpaid()
        except Exception as error:
            self._fines = []
            self._clear_fines()
            ctk.CTkLabel(self.fines_rows, text=f"Unable to load fines: {error}", text_color="#D17A67").pack(anchor="w", padx=12, pady=12)
            return

        self._render_fines()

    # Draw only the current page of unpaid fines.
    def _render_fines(self):
        self._clear_fines()

        try:
            for fine in self.pager.slice(self._fines):
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

            if not self._fines:
                ctk.CTkLabel(self.fines_rows, text="No unpaid fines at this time.", text_color="#A6B1B8").pack(anchor="w", padx=12, pady=12)

        except Exception as error:
            ctk.CTkLabel(self.fines_rows, text=f"Unable to load fines: {error}", text_color="#D17A67").pack(anchor="w", padx=12, pady=12)

    # Handle pay fine.
    def pay_fine(self, fine_id: int):
        try:
            FineManager().pay(fine_id)
            self.status.configure(text="Fine marked as paid.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to process payment: {error}", text_color="#D17A67")
