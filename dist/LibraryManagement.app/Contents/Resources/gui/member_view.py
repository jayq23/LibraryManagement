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

        # Permanent Status Label (Prevents creating multiple error labels)
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
            self.status.configure(text="Member added successfully.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to add member: {error}", text_color="#D17A67")

    def refresh(self):
        for widget in self.rows.winfo_children():
            widget.destroy()

        try:
            members = MemberManager().list_members()
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

                # Button states update based on active status
                btn_text = "Deactivate" if is_active else "Inactive"
                btn_color = "#4A3030" if is_active else "transparent"
                
                ctk.CTkButton(
                    row, 
                    text=btn_text, 
                    command=lambda member_id=member["member_id"]: self.deactivate(member_id), 
                    width=84, 
                    height=26, 
                    corner_radius=6, 
                    fg_color="transparent", 
                    border_width=1, 
                    border_color="#59636A", 
                    hover_color=btn_color,
                    state="normal" if is_active else "disabled"
                ).grid(row=0, rowspan=2, column=1, padx=(4, 10), pady=8)

            if not members:
                ctk.CTkLabel(self.rows, text="No members found.", text_color="#A6B1B8").pack(anchor="w", pady=16)

            self.status.configure(text=f"{len(members)} total members registered.", text_color="#9AA7B0")
        except Exception as error:
            self.status.configure(text=f"Unable to load members: {error}", text_color="#D17A67")

    def deactivate(self, member_id: str):
        try:
            MemberManager().deactivate(member_id)
            self.status.configure(text="Member deactivated.", text_color="#2A9D9A")
            self.refresh()
        except Exception as error:
            self.status.configure(text=f"Unable to deactivate member: {error}", text_color="#D17A67")