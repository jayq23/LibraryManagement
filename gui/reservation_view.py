"""Reservation management screen."""

import customtkinter as ctk

from managers.book_manager import BookManager
from managers.member_manager import MemberManager
from managers.transaction_manager import TransactionManager
from utils.helpers import enable_mousewheel
from utils.receipt_helpers import get_book_price, show_receipt


class ReservationView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self._member_values: list[str] = []
        self._book_values: list[str] = []
        self._reservations: list[dict] = []
        self._search_job = None

        # --- Reservation Form ---
        form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        form.pack(fill="x", pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=2)

        self.member_entry = ctk.CTkComboBox(form, values=["Loading members..."], height=34, corner_radius=7)
        self.member_entry.grid(row=0, column=0, sticky="ew", padx=(10, 3), pady=10)

        self.book_entry = ctk.CTkComboBox(form, values=["Loading books..."], height=34, corner_radius=7)
        self.book_entry.grid(row=0, column=1, sticky="ew", padx=3, pady=10)

        ctk.CTkButton(
            form,
            text="Reserve book",
            command=self.reserve,
            width=105,
            height=34,
            corner_radius=7,
            fg_color="#2A9D9A",
            hover_color="#21817F",
        ).grid(row=0, column=2, padx=(3, 10), pady=10)

        # Type in the member/book boxes to narrow down the dropdown list
        self._bind_combo_search(self.member_entry, lambda: self._member_values)
        self._bind_combo_search(self.book_entry, lambda: self._book_values)

        # --- Search bar for the reservation list ---
        search_container = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        search_container.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(search_container, text="Search reservations:", text_color="#E8EDF0").pack(side="left", padx=(14, 6), pady=10)

        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Enter title, member, ISBN, or status",
            height=34,
            corner_radius=7,
        )
        self.search_entry.pack(side="left", padx=(0, 6), pady=10, expand=True, fill="x")

        ctk.CTkButton(
            search_container,
            text="Search",
            command=self.on_search,
            width=82,
            height=34,
            corner_radius=7,
            fg_color="#2A9D9A",
            hover_color="#21817F",
        ).pack(side="left", padx=(0, 10), pady=10)

        # Status Label
        self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
        self.status.pack(anchor="w", pady=(0, 6))

        # --- Reservations Scrollable List ---
        self.rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        self.rows.pack(fill="both", expand=True)

        enable_mousewheel(self.rows)

        self.refresh()

    # ------------------------------------------------------------------
    # Member / book pickers
    # ------------------------------------------------------------------
    def _bind_combo_search(self, combo: ctk.CTkComboBox, get_values):
        """Filters the dropdown as the user types. Click the arrow to see the narrowed list."""
        def on_key(event):
            values = get_values()
            if not values:
                return
            if event.keysym == "Return":
                matches = self._filter(values, combo.get())
                if len(matches) == 1:
                    combo.set(matches[0])
                return
            if event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Shift_L", "Shift_R"):
                return
            matches = self._filter(values, combo.get())
            combo.configure(values=matches or ["No matches"])

        try:
            combo._entry.bind("<KeyRelease>", on_key)
        except AttributeError:
            pass  # customtkinter internals changed; combo still works without live filtering

    @staticmethod
    def _filter(values: list[str], typed: str) -> list[str]:
        typed = typed.strip().lower()
        if not typed:
            return values
        return [v for v in values if typed in v.lower()]

    def _resolve(self, combo: ctk.CTkComboBox, values: list[str], label: str) -> str:
        """Accepts an exact choice, or typed text that matches exactly one option."""
        typed = combo.get().strip()
        if typed in values:
            return typed
        matches = self._filter(values, typed)
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValueError(f"No {label} matches '{typed}'.")
        raise ValueError(f"{len(matches)} {label}s match '{typed}'. Pick one from the list.")

    def refresh_options(self):
        try:
            members = [m for m in MemberManager().list_members() if m["active"]]
            books = BookManager().list_books()

            self._member_values = [f"{m['member_id']} - {m['name']}" for m in members]
            self._book_values = [f"{b['isbn']} - {b['title']}" for b in books]

            current_member = self.member_entry.get()
            current_book = self.book_entry.get()

            self.member_entry.configure(values=self._member_values or ["No active members"])
            self.book_entry.configure(values=self._book_values or ["No books"])

            if self._member_values:
                self.member_entry.set(
                    current_member if current_member in self._member_values else self._member_values[0]
                )
            if self._book_values:
                self.book_entry.set(
                    current_book if current_book in self._book_values else self._book_values[0]
                )
        except Exception as error:
            self.status.configure(text=f"Unable to refresh options: {error}", text_color="#D17A67")

    # ------------------------------------------------------------------
    # Reserve / collect / cancel
    # ------------------------------------------------------------------
    def reserve(self):
        try:
            member_val = self._resolve(self.member_entry, self._member_values, "member")
            book_val = self._resolve(self.book_entry, self._book_values, "book")

            member_id = member_val.split(" - ", 1)[0].strip()
            isbn = book_val.split(" - ", 1)[0].strip()

            reservation_id = TransactionManager().reserve(member_id, isbn)
            self.status.configure(text=f"Reservation #{reservation_id} created.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to reserve book: {error}", text_color="#D17A67")
            return

        # Separate try: a receipt problem shouldn't look like a failed reservation
        try:
            show_receipt(
                self, "Book Reservation Slip", "RES", reservation_id, member_id, get_book_price(isbn)
            )
        except Exception as error:
            self.status.configure(
                text=f"Reservation #{reservation_id} created, but unable to show receipt: {error}",
                text_color="#D17A67",
            )

    def collect(self, reservation_id: int):
        try:
            TransactionManager().collect_reservation(reservation_id)
            self.status.configure(text="Reservation marked as collected.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to process collection: {error}", text_color="#D17A67")

    def cancel(self, reservation_id: int):
        try:
            TransactionManager().cancel_reservation(reservation_id)
            self.status.configure(text="Reservation cancelled.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to cancel reservation: {error}", text_color="#D17A67")

    # ------------------------------------------------------------------
    # List + search
    # ------------------------------------------------------------------
    def refresh(self):
        self.refresh_options()
        try:
            self._reservations = TransactionManager().list_reservations()
        except Exception as error:
            self._reservations = []
            self.status.configure(text=f"Unable to load reservations: {error}", text_color="#D17A67")
        self._render()

    def on_search(self):
        self._render()

    @staticmethod
    def _matches(reservation: dict, query: str) -> bool:
        keys = ("title", "name", "isbn", "status", "member_id", "created_on")
        haystack = " ".join(str(reservation.get(k) or "") for k in keys).lower()
        return all(term in haystack for term in query.lower().split())

    def _render(self):
        self._search_job = None
        for widget in self.rows.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip()
        reservations = [r for r in self._reservations if self._matches(r, query)] if query else self._reservations

        for reservation in reservations:
            row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=reservation["title"],
                text_color="#E8EDF0",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))

            status_text = reservation["status"].title()
            status_color = "#2A9D9A" if reservation["status"] == "collected" else "#A6B1B8"

            ctk.CTkLabel(
                row,
                text=f"{reservation['name']}  ·  {reservation['isbn']}  ·  {status_text}  ·  {reservation['created_on']}",
                text_color=status_color,
                anchor="w",
            ).grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))

            if reservation["status"] == "active":
                actions = ctk.CTkFrame(row, fg_color="transparent")
                actions.grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=6)

                ctk.CTkButton(
                    actions,
                    text="Collected",
                    command=lambda res_id=reservation["id"]: self.collect(res_id),
                    width=78,
                    height=26,
                    corner_radius=6,
                    fg_color="#2A9D9A",
                    hover_color="#21817F",
                ).pack(pady=(0, 3))

                ctk.CTkButton(
                    actions,
                    text="Cancel",
                    command=lambda res_id=reservation["id"]: self.cancel(res_id),
                    width=78,
                    height=24,
                    corner_radius=6,
                    fg_color="transparent",
                    border_width=1,
                    border_color="#59636A",
                    hover_color="#4A3030",
                ).pack()

        if not reservations:
            message = f"No reservations match '{query}'." if query else "No reservations found."
            ctk.CTkLabel(self.rows, text=message, text_color="#A6B1B8").pack(anchor="w", padx=14, pady=14)