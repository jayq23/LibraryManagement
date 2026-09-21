"""Reservation management screen."""

import customtkinter as ctk

from managers.book_manager import BookManager
from managers.member_manager import MemberManager
from managers.transaction_manager import TransactionManager


class ReservationView(ctk.CTkFrame):
	def __init__(self, master):
		super().__init__(master, fg_color="transparent")
		form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		form.pack(fill="x", pady=(0, 12))
		form.grid_columnconfigure(0, weight=1)
		form.grid_columnconfigure(1, weight=2)
		self.member_entry = ctk.CTkComboBox(form, values=["Loading members..."], height=34, corner_radius=7)
		self.member_entry.grid(row=0, column=0, sticky="ew", padx=(10, 3), pady=10)
		self.book_entry = ctk.CTkComboBox(form, values=["Loading books..."], height=34, corner_radius=7)
		self.book_entry.grid(row=0, column=1, sticky="ew", padx=3, pady=10)
		ctk.CTkButton(form, text="Reserve book", command=self.reserve, width=105, height=34, corner_radius=7, fg_color="#2A9D9A", hover_color="#21817F").grid(row=0, column=2, padx=(3, 10), pady=10)
		self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
		self.status.pack(anchor="w", pady=(0, 6))
		self.rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		self.rows.pack(fill="both", expand=True)
		self.refresh_options()
		self.refresh()

	def refresh_options(self):
		members = [member for member in MemberManager().list_members() if member["active"]]
		books = BookManager().list_books()
		member_values = [f"{member['member_id']} - {member['name']}" for member in members]
		book_values = [f"{book['isbn']} - {book['title']}" for book in books]
		self.member_entry.configure(values=member_values or ["No active members"])
		self.book_entry.configure(values=book_values or ["No books"])
		if member_values:
			self.member_entry.set(member_values[0])
		if book_values:
			self.book_entry.set(book_values[0])

	def reserve(self):
		try:
			member_id = self.member_entry.get().split(" - ", 1)[0]
			isbn = self.book_entry.get().split(" - ", 1)[0]
			reservation_id = TransactionManager().reserve(member_id, isbn)
			self.status.configure(text=f"Reservation #{reservation_id} created.", text_color="#2A9D9A")
			self.refresh()
		except Exception as error:
			self.status.configure(text=f"Unable to reserve book: {error}", text_color="#D17A67")

	def refresh(self):
		self.refresh_options()
		for widget in self.rows.winfo_children():
			widget.destroy()
		try:
			reservations = TransactionManager().list_reservations()
			for reservation in reservations:
				row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
				row.pack(fill="x", pady=4)
				row.grid_columnconfigure(0, weight=1)
				ctk.CTkLabel(row, text=reservation["title"], text_color="#E8EDF0", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))
				status = reservation["status"].title()
				ctk.CTkLabel(row, text=f"{reservation['name']}  ·  {reservation['isbn']}  ·  {status}  ·  {reservation['created_on']}", text_color="#2A9D9A" if reservation["status"] == "collected" else "#A6B1B8", anchor="w").grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))
				if reservation["status"] == "active":
					actions = ctk.CTkFrame(row, fg_color="transparent")
					actions.grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=6)
					ctk.CTkButton(actions, text="Collected", command=lambda reservation_id=reservation["id"]: self.collect(reservation_id), width=78, height=26, corner_radius=6, fg_color="#2A9D9A", hover_color="#21817F").pack(pady=(0, 3))
					ctk.CTkButton(actions, text="Cancel", command=lambda reservation_id=reservation["id"]: self.cancel(reservation_id), width=78, height=24, corner_radius=6, fg_color="transparent", border_width=1, border_color="#59636A", hover_color="#4A3030").pack()
			if not reservations:
				ctk.CTkLabel(self.rows, text="No active reservations.", text_color="#A6B1B8").pack(anchor="w", padx=14, pady=14)
		except Exception as error:
			self.status.configure(text=f"Unable to load reservations: {error}", text_color="#D17A67")

	def cancel(self, reservation_id: int):
		TransactionManager().cancel_reservation(reservation_id)
		self.status.configure(text="Reservation cancelled.", text_color="#2A9D9A")
		self.refresh()

	def collect(self, reservation_id: int):
		TransactionManager().collect_reservation(reservation_id)
		self.status.configure(text="Reservation marked as collected.", text_color="#2A9D9A")
		self.refresh()