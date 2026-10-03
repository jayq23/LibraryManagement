"""Borrow and return transaction screen."""

from datetime import date, timedelta
from decimal import Decimal

import customtkinter as ctk

from managers.book_manager import BookManager
from managers.member_manager import MemberManager
from managers.transaction_manager import TransactionManager
from models.invoice import Invoice
from utils.helpers import enable_mousewheel
from utils.receipt_modal import ReceiptModal


class BorrowReturnView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Checkout Form
        form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        form.pack(fill="x", pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=2)
        form.grid_columnconfigure(2, weight=1)
        
        self.member_entry = ctk.CTkComboBox(form, values=["Loading members..."], height=34, corner_radius=7)
        self.member_entry.grid(row=0, column=0, sticky="ew", padx=(10, 3), pady=10)
        
        self.book_entry = ctk.CTkComboBox(form, values=["Loading available books..."], height=34, corner_radius=7)
        self.book_entry.grid(row=0, column=1, sticky="ew", padx=3, pady=10)
        
        self.return_date_entry = ctk.CTkEntry(form, placeholder_text="Return date (YYYY-MM-DD)", height=34, corner_radius=7)
        self.return_date_entry.grid(row=0, column=2, sticky="ew", padx=3, pady=10)
        self.return_date_entry.insert(0, (date.today() + timedelta(days=14)).isoformat())
        
        ctk.CTkButton(
            form, 
            text="Checkout", 
            command=self.checkout, 
            width=90, 
            height=34, 
            corner_radius=7, 
            fg_color="#2A9D9A", 
            hover_color="#21817F"
        ).grid(row=0, column=3, padx=(3, 10), pady=10)
        
        self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
        self.status.pack(anchor="w", pady=(0, 6))
        
        # Search Bar
        search_container = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        search_container.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(search_container, text="Search by member ID:", text_color="#E8EDF0").pack(side="left", padx=(14, 6), pady=10)
        
        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="Enter member ID", height=34, corner_radius=7)
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
        
        # Active Loans Scrollable List
        rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        rows.pack(fill="both", expand=True, pady=(14, 0))
        self.rows = rows
        
        enable_mousewheel(self.rows)
        self.refresh()

    def refresh_options(self):
        members = MemberManager().list_members()
        member_values = [f"{member['member_id']} - {member['name']}" for member in members if member["active"]]
        
        books = [book for book in BookManager().list_books() if book["available_copies"] > 0]
        self.book_lookup = {book["title"]: book["isbn"] for book in books}
        book_values = [book["title"] for book in books]
        
        self.member_entry.configure(values=member_values or ["No active members"])
        self.book_entry.configure(values=book_values or ["No available books"])
        
        if member_values:
            self.member_entry.set(member_values[0])
        if book_values:
            self.book_entry.set(book_values[0])

    def on_search(self):
        query = self.search_entry.get().strip()
        self.refresh(member_id_filter=query if query else None)

    def checkout(self):
        try:
            member_id = self.member_entry.get().split(" - ", 1)[0].strip()
            book_title = self.book_entry.get().strip()
            isbn = self.book_lookup.get(book_title)
            return_date = date.fromisoformat(self.return_date_entry.get().strip())
            
            if not member_id.startswith("M") or not isbn:
                raise ValueError("Select an active member and available book")

            # 1. Fetch book details for price calculation
            books = BookManager().list_books()
            selected_book = next((b for b in books if b["isbn"] == isbn), None)
            book_price = Decimal(str(selected_book.get("price", "0.00"))) if selected_book else Decimal("0.00")

            # 2. Database borrow transaction
            loan_id = TransactionManager().borrow(member_id, isbn, return_date)

            self.status.configure(text=f"Checkout recorded. Loan ID: #{loan_id}", text_color="#2A9D9A")
            self.refresh()

            # 3. Instantiate Invoice Model with actual book price
            borrow_invoice = Invoice(
                invoice_id=f"BORROW-{loan_id:05d}",
                member_id=member_id,
                amount=book_price,
                paid=True
            )

            # 4. Trigger Receipt Modal
            title_preview = book_title[:20] + "..." if len(book_title) > 20 else book_title
            ReceiptModal(
                master=self,
                transaction_title=f"Borrow Slip ({title_preview})",
                invoice=borrow_invoice
            )

        except Exception as error:
            self.status.configure(text=f"Unable to checkout: {error}", text_color="#D17A67")

    def refresh(self, member_id_filter: str = None):
        self.refresh_options()
        for widget in self.rows.winfo_children():
            widget.destroy()
            
        try:
            loans = TransactionManager().active_loans()
            if member_id_filter:
                loans = [loan for loan in loans if loan.get("member_id") == member_id_filter]
                
            for loan in loans:
                row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
                row.pack(fill="x", pady=4)
                row.grid_columnconfigure(0, weight=1)
                
                ctk.CTkLabel(
                    row, 
                    text=loan["title"], 
                    text_color="#E8EDF0", 
                    font=ctk.CTkFont(size=13, weight="bold"), 
                    anchor="w"
                ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))
                
                ctk.CTkLabel(
                    row, 
                    text=f"Loan #{loan['id']}  ·  {loan['name']}  ·  due {loan['due_date']}", 
                    text_color="#A6B1B8", 
                    anchor="w"
                ).grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))
                
                ctk.CTkButton(
                    row, 
                    text="Return", 
                    command=lambda loan_id=loan["id"]: self.return_book(loan_id), 
                    width=64, 
                    height=26, 
                    corner_radius=6, 
                    fg_color="transparent", 
                    border_width=1, 
                    border_color="#59636A", 
                    hover_color="#344650"
                ).grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=8)
                
            if not loans:
                msg = "No loans found matching member ID." if member_id_filter else "No active loans."
                ctk.CTkLabel(self.rows, text=msg, text_color="#A6B1B8").pack(anchor="w", pady=16)
        except Exception as error:
            self.status.configure(text=f"Unable to load loans: {error}", text_color="#D17A67")

    def return_book(self, loan_id: int):
        try:
            result = TransactionManager().return_book(loan_id)
            days_late = result.get("days_late", 0)
            fine_amount = result.get("fine_amount", 0.0)

            if fine_amount > 0:
                self.status.configure(
                    text=f"Return recorded. {days_late} day(s) late — fine issued.",
                    text_color="#D17A67"
                )

                return_invoice = Invoice(
                    invoice_id=f"RETURN-{loan_id:05d}",
                    member_id=result.get("member_id", ""),
                    amount=Decimal(str(fine_amount)),
                    paid=False
                )

                title_preview = f"Late Return ({days_late} day{'s' if days_late != 1 else ''} late)"
                ReceiptModal(
                    master=self,
                    transaction_title=title_preview,
                    invoice=return_invoice
                )
            else:
                self.status.configure(text="Return recorded. No fine — returned on time.", text_color="#2A9D9A")

            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to return book: {error}", text_color="#D17A67")