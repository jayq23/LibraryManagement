"""Reports screen."""

import customtkinter as ctk

from managers.report_manager import ReportManager
from managers.fine_manager import FineManager


class ReportsView(ctk.CTkFrame):
	def __init__(self, master):
		super().__init__(master, fg_color="transparent")
		panel = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		panel.pack(fill="x", pady=(14, 0))
		try:
			for label, value in ReportManager().summary().items():
				row = ctk.CTkFrame(panel, fg_color="transparent")
				row.pack(fill="x", padx=18, pady=8)
				ctk.CTkLabel(row, text=label.replace("_", " ").title(), text_color="#A6B1B8", anchor="w").pack(side="left")
				ctk.CTkLabel(row, text=str(value), text_color="#2A9D9A", font=ctk.CTkFont(size=16, weight="bold")).pack(side="right")
		except Exception as error:
			ctk.CTkLabel(panel, text=f"Unable to load reports: {error}", text_color="#D17A67").pack(anchor="w", padx=18, pady=16)
		fines = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		fines.pack(fill="both", expand=True, pady=(14, 0))
		ctk.CTkLabel(fines, text="Unpaid fines", text_color="#E8EDF0", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=18, pady=(14, 6))
		try:
			for fine in FineManager().list_unpaid():
				row = ctk.CTkFrame(fines, fg_color="#202D37", corner_radius=7)
				row.pack(fill="x", padx=12, pady=4)
				ctk.CTkLabel(row, text=f"{fine['name']}  ·  {fine['amount']}  ·  {fine['reason']}", text_color="#A6B1B8").pack(side="left", padx=12, pady=8)
				ctk.CTkButton(row, text="Mark paid", command=lambda fine_id=fine["id"]: self.pay_fine(fine_id), width=82, height=26, corner_radius=6, fg_color="#2A9D9A", hover_color="#21817F").pack(side="right", padx=10, pady=6)
		except Exception as error:
			ctk.CTkLabel(fines, text=f"Unable to load fines: {error}", text_color="#D17A67").pack(anchor="w", padx=18, pady=12)

	def pay_fine(self, fine_id: int):
		FineManager().pay(fine_id)
		dashboard = self.winfo_toplevel()
		self.destroy()
		if hasattr(dashboard, "show_panel"):
			dashboard.show_panel("Reports")
