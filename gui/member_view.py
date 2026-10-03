"""Member management screen."""

import customtkinter as ctk

from managers.member_manager import MemberManager
from utils.helpers import enable_mousewheel


class MemberView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # --- Add Member Form ---
        form = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        form.pack(fill="x", pady=(0, 12))

        self.member_inputs = {}
        for index, label in enumerate(("Member ID", "Name", "Email")):
            form.grid_columnconfigure(index, weight=1)
            entry = ctk.CTkEntry(form, placeholder_text=label, height=34, corner_radius=7)
            entry.grid(row=0, column=index, sticky="ew", padx=(10 if index == 0 else 3, 3), pady=10)
            self.member_inputs[label] = entry

        # Configure column 3 for button balance
        form.grid_columnconfigure(3, weight=0)

        ctk.CTkButton(
            form, 
            text="Add member", 
            command=self.add_member, 
            width=100, 
            height=34, 
            corner_radius=7, 
            fg_color="#2A9D9A", 
            hover_color="#21817F"
        ).grid(row=0, column=3, padx=(3, 10), pady=10)

        search_container = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        search_container.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(search_container, text="Search members:", text_color="#E8EDF0").pack(side="left", padx=(14, 6), pady=10)

        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="Enter member ID, name, or email", height=34, corner_radius=7)
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

        # Permanent Status Label
        self.status = ctk.CTkLabel(self, text="", text_color="#9AA7B0")
        self.status.pack(anchor="w", pady=(0, 6))

        # --- Member List ---
        self.rows = ctk.CTkScrollableFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        self.rows.pack(fill="both", expand=True)

        enable_mousewheel(self.rows)
        self.refresh()

    def add_member(self):
        try:
            MemberManager().add_member(*(entry.get().strip() for entry in self.member_inputs.values()))
            for entry in self.member_inputs.values():
                entry.delete(0, "end")
            self.refresh()
            self.status.configure(text="Member added successfully.", text_color="#2A9D9A")
        except Exception as error:
            self.status.configure(text=f"Unable to add member: {error}", text_color="#D17A67")

    def on_search(self):
        self.refresh(self.search_entry.get().strip())

    def refresh(self, query: str | None = None):
        for widget in self.rows.winfo_children():
            widget.destroy()

        try:
            members = MemberManager().list_members()
            query = self.search_entry.get().strip() if query is None else query
            if query:
                members = [
                    member for member in members
                    if all(
                        term in " ".join(
                            str(member.get(key) or "")
                            for key in ("member_id", "name", "email", "active")
                        ).lower()
                        for term in query.lower().split()
                    )
                ]
            for member in members:
                is_active = member["active"]
                state_text = "Active" if is_active else "Inactive"
                
                row = ctk.CTkFrame(self.rows, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=7)
                row.pack(fill="x", pady=4)
                row.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    row, 
                    text=member["name"], 
                    text_color="#E8EDF0", 
                    font=ctk.CTkFont(size=13, weight="bold"), 
                    anchor="w"
                ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(8, 1))

                ctk.CTkLabel(
                    row, 
                    text=f"{member['member_id']}  ·  {member['email']}  ·  {state_text}", 
                    text_color="#A6B1B8" if is_active else "#6C7A84", 
                    anchor="w"
                ).grid(row=1, column=0, sticky="ew", padx=(14, 8), pady=(0, 8))

                # Safe Color Values (Bawal ang "transparent" sa hover_color sa macOS)
                btn_text = "Deactivate" if is_active else "Inactive"
                btn_hover = "#4A3030" if is_active else "#202D37"
                
                ctk.CTkButton(
                    row, 
                    text=btn_text, 
                    command=lambda member_id=member["member_id"]: self.deactivate(member_id), 
                    width=84, 
                    height=26, 
                    corner_radius=6, 
                    fg_color="transparent", 
                    border_width=1, 
                    border_color="#59636A" if is_active else "#3A444C", 
                    hover_color=btn_hover,
                    state="normal" if is_active else "disabled"
                ).grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=8)

            if not members:
                message = f"No members match '{query}'." if query else "No members found."
                ctk.CTkLabel(self.rows, text=message, text_color="#A6B1B8").pack(anchor="w", pady=16)

            self.status.configure(text=f"{len(members)} total members registered.", text_color="#9AA7B0")
        except Exception as error:
            self.status.configure(text=f"Unable to load members: {error}", text_color="#D17A67")

    def deactivate(self, member_id: str):
        try:
            MemberManager().deactivate(member_id)
            self.refresh()
            self.status.configure(text=f"Member {member_id} deactivated successfully.", text_color="#2A9D9A")
        except Exception as error:
            self.status.configure(text=f"Unable to deactivate member: {error}", text_color="#D17A67")