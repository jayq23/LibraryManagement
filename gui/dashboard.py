"""Dashboard screen."""

from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from gui.book_catalog_view import BookCatalogView
from gui.borrow_return_view import BorrowReturnView
from gui.category_view import CategoryView
from gui.chatbot_window import ChatbotView
from gui.member_view import MemberView
from gui.reports_view import ReportsView
from gui.reservation_view import ReservationView
from managers.report_manager import ReportManager


class Dashboard(ctk.CTkToplevel):
	def __init__(self, login_window: ctk.CTk, user) -> None:
		super().__init__(login_window)
		self.login_window = login_window
		self.title("Viva La Vida")
		self.geometry("1040x680")
		self.minsize(820, 560)
		self.configure(fg_color="#111820")
		self.protocol("WM_DELETE_WINDOW", self.close)
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(0, weight=1)
		self.user = user
		self.username = user.username
		self.nav_buttons = {}
		self.active_panel = "Dashboard"
		self.active_view = None
		self.refresh_job = None
		self.metric_labels = {}
		self.chart_canvas = None
		self.chart_data = []

		# Sidebar
		sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#18232D")
		sidebar.grid(row=0, column=0, sticky="nsew")
		sidebar.pack_propagate(False)

		brand = ctk.CTkFrame(sidebar, fg_color="transparent")
		brand.pack(fill="x", padx=18, pady=(24, 28))

		logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
		img = Image.open(logo_path)
		self.logo = ctk.CTkImage(light_image=img, dark_image=img, size=(46, 46))
		ctk.CTkLabel(brand, image=self.logo, text="").pack(side="left", padx=(0, 11))
		brand_text = ctk.CTkFrame(brand, fg_color="transparent")
		brand_text.pack(side="left", fill="x", expand=True)
		ctk.CTkLabel(
			brand_text, text="VIVA LA VIDA", text_color="#E8EDF0",
			font=ctk.CTkFont(size=15, weight="bold")
		).pack(anchor="w")
		ctk.CTkLabel(
			brand_text, text="LIBRARY DESK", text_color="#7F909A",
			font=ctk.CTkFont(size=9, weight="bold")
		).pack(anchor="w", pady=(2, 0))
		ctk.CTkFrame(sidebar, height=1, fg_color="#2B3943").pack(fill="x", padx=18, pady=(0, 18))

		for panel_name in ("Dashboard", "Members", "Books", "Categories", "Borrow / Return", "Reservations", "Reports", "Assistant"):
			button = ctk.CTkButton(
				sidebar, text=panel_name, anchor="w",
				command=lambda name=panel_name: self.show_panel(name),
				height=42, corner_radius=7, fg_color="transparent",
				hover_color="#253540", text_color="#C5D0D6",
			)
			button.pack(fill="x", padx=14, pady=3)
			self.nav_buttons[panel_name] = button

		ctk.CTkButton(
			sidebar, text="Sign out", anchor="center", command=self.close,
			height=42, corner_radius=7, fg_color="#253540", hover_color="#2A9D9A",
		).pack(side="bottom", fill="x", padx=14, pady=22)

		# Main content
		content = ctk.CTkFrame(self, fg_color="#111820", corner_radius=0)
		content.grid(row=0, column=1, sticky="nsew", padx=42, pady=36)
		content.grid_columnconfigure(0, weight=1)
		content.grid_rowconfigure(0, weight=1)

		self.page_content = ctk.CTkFrame(content, fg_color="transparent")
		self.page_content.grid(row=0, column=0, sticky="nsew")
		self.page_content.grid_columnconfigure(0, weight=1)
		self.page_content.grid_rowconfigure(2, weight=1)
		self.page_content.grid_rowconfigure(3, weight=0)

		self.show_panel("Dashboard")
		self.refresh_job = self.after(5000, self.refresh_live_data)

	def greeting(self) -> str:
		hour = datetime.now().hour
		if hour < 12:
			return "Good morning"
		if hour < 18:
			return "Good afternoon"
		return "Good evening"

	def show_panel(self, panel_name: str) -> None:
		self.active_panel = panel_name
		self.active_view = None
		self.page_content.grid_rowconfigure(2, weight=1)
		self.page_content.grid_rowconfigure(3, weight=1 if panel_name == "Dashboard" else 0)
		for name, button in self.nav_buttons.items():
			button.configure(
				fg_color="#2A9D9A" if name == panel_name else "transparent",
				text_color="#FFFFFF" if name == panel_name else "#C5D0D6",
			)
		for widget in self.page_content.winfo_children():
			widget.destroy()

		title = f"{self.greeting()}, {self.username}" if panel_name == "Dashboard" else panel_name
		subtitle = "Your library at a glance" if panel_name == "Dashboard" else "Keep your collection moving"

		ctk.CTkLabel(
			self.page_content, text=title, text_color="#E8EDF0",
			font=ctk.CTkFont(size=30, weight="bold"),
		).grid(row=0, column=0, sticky="w")
		ctk.CTkLabel(
			self.page_content, text=subtitle, text_color="#9AA7B0",
		).grid(row=1, column=0, sticky="w", pady=(4, 0))

		if panel_name == "Dashboard":
			try:
				metrics = ReportManager().summary()
			except Exception as error:
				ctk.CTkLabel(
					self.page_content, text=f"Unable to load summary: {error}",
					text_color="#D17A67",
				).grid(row=2, column=0, sticky="nw", pady=(28, 0))
				return

			metric_grid = ctk.CTkFrame(self.page_content, fg_color="transparent")
			metric_grid.grid(row=2, column=0, sticky="new", pady=(28, 0))
			for index in range(4):
				metric_grid.grid_columnconfigure(index, weight=1)

			cards = (
				("Total books", "total_books", "#2A9D9A"),
				("Active loans", "active_loans", "#2A9D9A"),
				("Overdue", "overdue", "#D17A67"),
				("Members", "members", "#2A9D9A"),
			)
			for index, (label, key, accent) in enumerate(cards):
				card = ctk.CTkFrame(metric_grid, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
				card.grid(
					row=0, column=index, sticky="nsew",
					padx=(0 if index == 0 else 7, 7 if index < 3 else 0),
				)
				ctk.CTkLabel(
					card, text=label.upper(), text_color="#9AA7B0",
					font=ctk.CTkFont(size=10, weight="bold"),
				).pack(anchor="w", padx=16, pady=(16, 7))
				value_label = ctk.CTkLabel(
					card, text=str(metrics[key]), text_color=accent,
					font=ctk.CTkFont(size=30, weight="bold"),
				)
				value_label.pack(anchor="w", padx=16, pady=(0, 16))
				self.metric_labels[key] = value_label

			self.add_activity_chart()


		elif panel_name == "Books":
			self.active_view = BookCatalogView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Categories":
			self.active_view = CategoryView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Members":
			self.active_view = MemberView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Borrow / Return":
			self.active_view = BorrowReturnView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Reports":
			self.active_view = ReportsView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Reservations":
			self.active_view = ReservationView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		elif panel_name == "Assistant":
			self.active_view = ChatbotView(self.page_content)
			self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
		else:
			ctk.CTkLabel(
				self.page_content,
				text=f"{panel_name} content will appear here.",
				text_color="#9AA7B0",
			).grid(row=2, column=0, sticky="nw", pady=24)

	def refresh_live_data(self):
		if not self.winfo_exists():
			return
		if self.active_panel == "Dashboard":
			self.refresh_dashboard_data()
		self.refresh_job = self.after(5000, self.refresh_live_data)

	def refresh_dashboard_data(self):
		try:
			metrics = ReportManager().summary()
			for key, label in self.metric_labels.items():
				label.configure(text=str(metrics[key]))
			if self.chart_canvas is not None:
				self.chart_data = ReportManager().monthly_activity()
				self.draw_activity_chart()
		except Exception:
			return

	def add_activity_chart(self):
		panel = ctk.CTkFrame(self.page_content, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		panel.grid(row=3, column=0, sticky="nsew", pady=(24, 0))
		ctk.CTkLabel(panel, text="Loans and fines over time", text_color="#E8EDF0", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=16, pady=(12, 0))
		ctk.CTkLabel(panel, text="Monthly activity", text_color="#9AA7B0").pack(anchor="w", padx=16, pady=(2, 4))
		legend = ctk.CTkFrame(panel, fg_color="transparent")
		legend.pack(anchor="w", padx=16)
		ctk.CTkLabel(legend, text="■ Loans", text_color="#7B78B8").pack(side="left", padx=(0, 14))
		ctk.CTkLabel(legend, text="━ Fines", text_color="#2A9D9A").pack(side="left")
		canvas = ctk.CTkCanvas(panel, height=210, bg="#1B252E", highlightthickness=0)
		canvas.pack(fill="both", expand=True, padx=12, pady=(4, 12))
		self.chart_canvas = canvas
		try:
			self.chart_data = ReportManager().monthly_activity()
		except Exception as error:
			ctk.CTkLabel(panel, text=f"Unable to load chart: {error}", text_color="#D17A67").pack(anchor="w", padx=16, pady=10)
			return

		canvas.bind("<Configure>", lambda _event: self.draw_activity_chart())
		canvas.after_idle(self.draw_activity_chart)

	def draw_activity_chart(self):
		canvas = self.chart_canvas
		data = self.chart_data
		if canvas is None or not canvas.winfo_exists() or not data:
			return
		canvas.delete("all")
		width = max(canvas.winfo_width(), 500)
		height = max(canvas.winfo_height(), 180)
		left, right, top, bottom = 46, 18, 12, 32
		plot_width = width - left - right
		plot_height = height - top - bottom
		max_loans = max([int(row["loans"]) for row in data] + [1])
		max_fines = max([float(row["fines"]) for row in data] + [1.0])
		for tick in range(4):
			y = top + plot_height - (plot_height * tick / 3)
			canvas.create_line(left, y, width - right, y, fill="#303D47")
			canvas.create_text(left - 8, y, text=str(round(max_loans * tick / 3)), fill="#7F909A", anchor="e", font=("Helvetica", 9))
		step = plot_width / max(len(data), 1)
		points = []
		for index, row in enumerate(data):
			x = left + step * (index + 0.5)
			bar_height = plot_height * int(row["loans"]) / max_loans
			canvas.create_rectangle(x - 16, top + plot_height - bar_height, x + 16, top + plot_height, fill="#7B78B8", outline="")
			canvas.create_text(x, top + plot_height + 15, text=row["label"], fill="#9AA7B0", font=("Helvetica", 9))
			line_y = top + plot_height - (plot_height * float(row["fines"]) / max_fines)
			points.extend((x, line_y))
			canvas.create_text(x, top + plot_height - bar_height - 8, text=str(row["loans"]), fill="#E8EDF0", font=("Helvetica", 9))
		if len(points) >= 4:
			canvas.create_line(*points, fill="#2A9D9A", width=2, smooth=True)
			for index in range(0, len(points), 2):
				canvas.create_oval(points[index] - 3, points[index + 1] - 3, points[index] + 3, points[index + 1] + 3, fill="#2A9D9A", outline="#1B252E")

	def close(self) -> None:
		if self.refresh_job is not None:
			self.after_cancel(self.refresh_job)
		self.destroy()
		self.login_window.destroy()