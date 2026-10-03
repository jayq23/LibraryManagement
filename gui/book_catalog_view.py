"""Book catalog screen."""

import customtkinter as ctk

from managers.book_manager import BookManager
from managers.category_manager import CategoryManager
from utils.helpers import enable_mousewheel


class BookCatalogView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.category_map = {}  # Dictionary mapping Name -> ID

        # --- Add Book Form ---
        form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        form.pack(fill="x", pady=(0, 12))

        fields = [
            ("ISBN", "ISBN"),
            ("Title", "Title"),
            ("Author", "Author"),
            ("Shelf", "Shelf / location"),
            ("Copies", "Copies"),
            ("Price", "Price"),
        ]

        self.inputs = {}
        for index, (label, placeholder) in enumerate(fields):
            form.grid_columnconfigure(index, weight=1)
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=34, corner_radius=7)
            entry.grid(row=0, column=index, sticky="ew", padx=(10 if index == 0 else 3, 3), pady=10)
            self.inputs[label] = entry

        form.grid_columnconfigure(6, weight=1)
        form.grid_columnconfigure(7, weight=1)

        self.category_entry = ctk.CTkComboBox(form, values=["No category"], height=34, corner_radius=7)
        self.category_entry.grid(row=0, column=6, sticky="ew", padx=3, pady=10)

        ctk.CTkButton(
            form, 
            text="Add title", 
            command=self.add_book, 
            width=92, 
            height=34, 
            corner_radius=7, 
            fg_color="#2A9D9A", 
            hover_color="#21817F"
        ).grid(row=0, column=7, padx=(3, 10), pady=10)

        self.refresh_categories()

        # --- Restock Form ---
        restock_form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        restock_form.pack(fill="x", pady=(0, 12))

        self.restock_entry = ctk.CTkComboBox(restock_form, values=["Loading books..."], height=34, corner_radius=7)
        self.restock_entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)

        self.quantity_entry = ctk.CTkEntry(restock_form, placeholder_text="Copies to add", width=130, height=34, corner_radius=7)
        self.quantity_entry.pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            restock_form, 
            text="Add copies", 
            command=self.add_copies, 
            width=100, 
            height=34, 
            corner_radius=7, 
            fg_color="#253540", 
            hover_color="#344650"
        ).pack(side="left", padx=(3, 10), pady=10)

        search_container = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        search_container.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(search_container, text="Search books:", text_color="#E8EDF0").pack(side="left", padx=(14, 6), pady=10)

        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="Enter ISBN, title, author, or shelf", height=34, corner_radius=7)
        self.search_entry.pack(side="left", padx=(0, 6), pady=10, expand=True, fill="x")

        ctk.CTkButton(
            search_container,
            text="Search",
            command=self.on_search,
            width=82,
            height=34,
            corner_radius=7,
            fg_color="#2A9D9A",
            hover_color="#21817F"
        ).pack(side="left", padx=(0, 10), pady=10)

        # Status Label
        self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
        self.status.pack(anchor="w", pady=(4, 14))

        # --- Catalog List ---
        self.rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        self.rows.pack(fill="both", expand=True)

        enable_mousewheel(self.rows)
        self.refresh()

    def refresh_restock_books(self):
        books = BookManager().list_books()
        values = [f"{book['isbn']} - {book['title']}" for book in books]
        self.restock_entry.configure(values=values or ["No books"])
        self.restock_entry.set(values[0] if values else "No books")

    def refresh_categories(self):
        categories = CategoryManager().list_categories()
        # Mapping Category Name -> Category ID (Clean UI without showing ID numbers)
        self.category_map = {cat["name"]: cat.get("category_id") or cat.get("id") for cat in categories}
        cat_names = list(self.category_map.keys())

        self.category_entry.configure(values=cat_names or ["No category"])
        self.category_entry.set(cat_names[0] if cat_names else "No category")

    def on_search(self):
        self.refresh(self.search_entry.get().strip())

    def refresh(self, query: str | None = None):
        for widget in self.rows.winfo_children():
            widget.destroy()

        try:
            self.refresh_restock_books()
            self.refresh_categories()
            books = BookManager().list_books()
            query = self.search_entry.get().strip() if query is None else query
            if query:
                books = [
                    book for book in books
                    if all(
                        term in " ".join(
                            str(book.get(key) or "")
                            for key in ("isbn", "title", "author", "shelf_location", "category_name")
                        ).lower()
                        for term in query.lower().split()
                    )
                ]

            for book in books:
                row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
                row.pack(fill="x", pady=4)
                row.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    row, 
                    text=book["title"], 
                    text_color="#E8EDF0", 
                    font=ctk.CTkFont(size=13, weight="bold"), 
                    anchor="w"
                ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))

                category = book.get("category_name") or "Uncategorized"
                ctk.CTkLabel(
                    row, 
                    text=f"{book['author']}  ·  ISBN {book['isbn']}  ·  Shelf {book['shelf_location'] or 'Not assigned'}  ·  {category}  ·  ₱{book['price']}  ·  {book['available_copies']} available", 
                    text_color="#A6B1B8", 
                    anchor="w"
                ).grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))

                ctk.CTkButton(
                    row, 
                    text="Delete", 
                    command=lambda isbn=book["isbn"]: self.delete_book(isbn), 
                    width=64, 
                    height=26, 
                    corner_radius=6, 
                    fg_color="transparent", 
                    border_width=1, 
                    border_color="#59636A", 
                    hover_color="#4A3030"
                ).grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=8)

            if not books:
                message = f"No books match '{query}'." if query else "No titles found in catalog."
                ctk.CTkLabel(self.rows, text=message, text_color="#A6B1B8").pack(anchor="w", pady=16)

            self.status.configure(text=f"{len(books)} titles available in catalog.", text_color="#9AA7B0")
        except Exception as error:
            self.status.configure(text=f"Unable to load catalog: {error}", text_color="#D17A67")

    def add_book(self):
        try:
            selected_cat_name = self.category_entry.get()
            category_id = self.category_map.get(selected_cat_name)

            BookManager().add_book(
                self.inputs["ISBN"].get().strip(), 
                self.inputs["Title"].get().strip(), 
                self.inputs["Author"].get().strip(), 
                self.inputs["Shelf"].get().strip(), 
                int(self.inputs["Copies"].get() or "1"), 
                category_id, 
                float(self.inputs["Price"].get() or "0")
            )
            for entry in self.inputs.values():
                entry.delete(0, "end")
            self.refresh()
            self.status.configure(text="New book added to catalog.", text_color="#2A9D9A")
        except Exception as error:
            self.status.configure(text=f"Unable to add title: {error}", text_color="#D17A67")

    def delete_book(self, isbn: str):
        try:
            BookManager().delete_book(isbn)
            self.refresh()
            self.status.configure(text="Book removed successfully.", text_color="#2A9D9A")
        except Exception as error:
            err_msg = str(error).lower()
            if "foreign key constraint" in err_msg or "loans_isbn_fkey" in err_msg:
                self.status.configure(
                    text="Cannot delete title: This book has existing borrowing or loan records.", 
                    text_color="#D17A67"
                )
            else:
                self.status.configure(text=f"Unable to delete title: {error}", text_color="#D17A67")

    def add_copies(self):
        try:
            isbn = self.restock_entry.get().split(" - ", 1)[0].strip()
            BookManager().add_copies(isbn, int(self.quantity_entry.get() or "0"))
            self.quantity_entry.delete(0, "end")
            self.status.configure(text="Copies added to inventory.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to add copies: {error}", text_color="#D17A67")