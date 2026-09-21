"""Category management screen."""

import customtkinter as ctk

from managers.category_manager import CategoryManager
from utils.helpers import enable_mousewheel


class CategoryView(ctk.CTkFrame):
	def __init__(self, master):
		super().__init__(master, fg_color="transparent")
		form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		form.pack(fill="x", pady=(0, 12))
		form.grid_columnconfigure(0, weight=1)
		form.grid_columnconfigure(1, weight=2)
		self.name_entry = ctk.CTkEntry(form, placeholder_text="Category name", height=34, corner_radius=7)
		self.name_entry.grid(row=0, column=0, sticky="ew", padx=(10, 3), pady=10)
		self.description_entry = ctk.CTkEntry(form, placeholder_text="Description", height=34, corner_radius=7)
		self.description_entry.grid(row=0, column=1, sticky="ew", padx=3, pady=10)
		ctk.CTkButton(form, text="Add category", command=self.add_category, width=105, height=34, corner_radius=7, fg_color="#2A9D9A", hover_color="#21817F").grid(row=0, column=2, padx=(3, 10), pady=10)
		self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
		self.status.pack(anchor="w", pady=(0, 6))
		self.rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
		self.rows.pack(fill="both", expand=True)
		enable_mousewheel(self.rows)
		self.refresh()

	def refresh(self):
		for widget in self.rows.winfo_children():
			widget.destroy()
		try:
			for category in CategoryManager().list_categories():
				row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
				row.pack(fill="x", pady=4)
				row.grid_columnconfigure(0, weight=1)
				ctk.CTkLabel(row, text=category["name"], text_color="#E8EDF0", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))
				ctk.CTkLabel(row, text=f"{category['description']}  ·  {category['book_count']} title(s)", text_color="#A6B1B8", anchor="w").grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))
				ctk.CTkButton(row, text="View titles", command=lambda category_id=category["id"], target=row: self.toggle_books(category_id, target), width=82, height=26, corner_radius=6, fg_color="#2A9D9A", hover_color="#21817F").grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=8)
		except Exception as error:
			self.status.configure(text=f"Unable to load categories: {error}", text_color="#D17A67")

	def toggle_books(self, category_id: int, row):
		for child in row.winfo_children():
			if getattr(child, "category_detail", False):
				child.destroy()
				return
		detail = ctk.CTkFrame(row, fg_color="#1B252E", corner_radius=6)
		detail.category_detail = True
		detail.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))
		books = CategoryManager().books_in_category(category_id)
		if not books:
			ctk.CTkLabel(detail, text="No books assigned to this category.", text_color="#A6B1B8").pack(anchor="w", padx=10, pady=8)
		for book in books:
			ctk.CTkLabel(detail, text=f"{book['title']}  ·  {book['author']}  ·  {book['available_copies']} available", text_color="#E8EDF0", anchor="w").pack(fill="x", padx=10, pady=4)

	def add_category(self):
		try:
			CategoryManager().add_category(self.name_entry.get(), self.description_entry.get())
			self.name_entry.delete(0, "end")
			self.description_entry.delete(0, "end")
			self.status.configure(text="Category added.", text_color="#2A9D9A")
			self.refresh()
		except Exception as error:
			self.status.configure(text=f"Unable to add category: {error}", text_color="#D17A67")
