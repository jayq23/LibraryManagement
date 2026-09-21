"""Embedded database assistant screen."""

import customtkinter as ctk
from ai_agent.agent import LibraryAgent
from managers.fine_manager import FineManager
from managers.report_manager import ReportManager


class ChatbotView(ctk.CTkFrame):
	"""A local assistant that answers common library questions from PostgreSQL."""

	def __init__(self, master):
		super().__init__(master, fg_color="transparent")
		self.agent = LibraryAgent()
		ctk.CTkLabel(self, text="OFFLINE LIBRARY ASSISTANT  ·  PostgreSQL data", text_color="#2A9D9A", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(0, 8))
		self.history = ctk.CTkTextbox(self, fg_color="#1B252E", border_color="#303D47", border_width=1, text_color="#E8EDF0", corner_radius=10, wrap="word", padx=16, pady=14)
		self.history.pack(fill="both", expand=True)
		self.history._textbox.configure(state="disabled")
		self.history._textbox.tag_config("speaker", foreground="#2A9D9A", font=ctk.CTkFont(size=11, weight="bold"))
		self.history._textbox.tag_config("message", foreground="#E8EDF0", font=ctk.CTkFont(size=13))
		composer = ctk.CTkFrame(self, fg_color="transparent")
		composer.pack(fill="x", pady=(12, 0))
		self.entry = ctk.CTkEntry(composer, placeholder_text="Ask about books, availability, or members...", height=40, corner_radius=9)
		self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
		ctk.CTkButton(composer, text="Send", command=lambda: self.submit(self.entry.get()), height=40, width=84, corner_radius=8, fg_color="#2A9D9A", hover_color="#21817F").pack(side="right")
		self.entry.bind("<Return>", lambda _: self.submit(self.entry.get()))
		self.write("Assistant", "Hi! Ask me to search books, check availability, check a member, or reserve a book.")

	def write(self, speaker: str, message: str) -> None:
		self.history._textbox.configure(state="normal")
		self.history._textbox.insert("end", f"{speaker}\n", "speaker")
		self.history._textbox.insert("end", f"{message}\n\n", "message")
		self.history._textbox.configure(state="disabled")
		self.history._textbox.see("end")

	def submit(self, prompt: str) -> None:
		prompt = prompt.strip()
		if not prompt:
			return
		self.entry.delete(0, "end")
		self.write("You", prompt)
		try:
			response = self.answer(prompt)
		except Exception as error:
			response = f"I could not complete that request: {error}"
		self.write("Assistant", response)

	def answer(self, prompt: str) -> str:
		agent = getattr(self, "agent", None) or LibraryAgent()
		return agent.answer(prompt)
