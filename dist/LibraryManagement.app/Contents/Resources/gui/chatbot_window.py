"""AI Assistant chat screen with typing indicator and modern UI."""

import threading
import time
import customtkinter as ctk

from ai_agent.chatbot import Chatbot
from utils.helpers import enable_mousewheel


class ChatbotView(ctk.CTkFrame):
    def __init__(self, master, chatbot_instance: Chatbot = None):
        super().__init__(master, fg_color="transparent")

        # Gagamitin ang ipinasang persistent Chatbot instance
        self.chatbot = chatbot_instance or Chatbot()

        # --- Top Header ---
        header = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        header.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(
            header, 
            text="🤖 AI Library Assistant", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color="#E8EDF0"
        ).pack(side="left", padx=16, pady=12)

        # --- Chat Scrollable Area ---
        self.chat_container = ctk.CTkScrollableFrame(
            self, 
            fg_color="#1B252E", 
            border_color="#303D47", 
            border_width=1, 
            corner_radius=10
        )
        self.chat_container.pack(fill="both", expand=True, pady=(0, 12))
        enable_mousewheel(self.chat_container)

        # --- Input Bar ---
        input_container = ctk.CTkFrame(self, fg_color="#1B252E", border_color="#303D47", border_width=1, corner_radius=10)
        input_container.pack(fill="x")
        input_container.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_container, 
            placeholder_text="Ask about books, loans, library stats, or recommendations...", 
            height=40, 
            corner_radius=8,
            border_width=1,
            border_color="#303D47"
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=10)
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(
            input_container, 
            text="Send", 
            command=self.send_message, 
            width=80, 
            height=40, 
            corner_radius=8, 
            fg_color="#2A9D9A", 
            hover_color="#21817F",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.send_button.grid(row=0, column=1, padx=(0, 12), pady=10)

        # Re-render UI chat bubbles base sa persistent memory ng Chatbot
        self._render_conversation_history()

    def _render_conversation_history(self):
        """Re-renders existing chat bubbles from chatbot memory."""
        history = self.chatbot.get_history()
        
        if not history:
            self.add_message_bubble("Hello! How can I help you manage the library today?", is_user=False)
            return

        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            
            # Huwag ipakita ang system o tool-call payload messages sa Chat UI
            if role == "user":
                self.add_message_bubble(content, is_user=True)
            elif role == "assistant" and content:
                self.add_message_bubble(content, is_user=False)

    def refresh(self):
        """Called automatically by Dashboard when switching panels."""
        pass

    def add_message_bubble(self, message: str, is_user: bool = False) -> ctk.CTkFrame:
        """Renders a styled chat bubble in the scrollable view."""
        wrapper = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        wrapper.pack(fill="x", pady=6, padx=10)

        align_side = "e" if is_user else "w"
        bg_color = "#2A9D9A" if is_user else "#202D37"
        text_color = "#FFFFFF" if is_user else "#E8EDF0"
        border_color = "#21817F" if is_user else "#344650"

        bubble = ctk.CTkFrame(
            wrapper, 
            fg_color=bg_color, 
            border_color=border_color, 
            border_width=1, 
            corner_radius=12
        )
        bubble.pack(side="right" if is_user else "left", anchor=align_side)

        label = ctk.CTkLabel(
            bubble, 
            text=message, 
            text_color=text_color, 
            justify="left", 
            wraplength=550, 
            font=ctk.CTkFont(size=13)
        )
        label.pack(padx=14, pady=10)

        self._scroll_to_bottom()
        return wrapper

    def show_typing_indicator(self) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        """Displays an animated typing indicator bubble."""
        wrapper = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        wrapper.pack(fill="x", pady=6, padx=10)

        bubble = ctk.CTkFrame(wrapper, fg_color="#202D37", border_color="#344650", border_width=1, corner_radius=12)
        bubble.pack(side="left", anchor="w")

        indicator_label = ctk.CTkLabel(
            bubble, 
            text="Thinking...", 
            text_color="#9AA7B0", 
            font=ctk.CTkFont(size=12, slant="italic")
        )
        indicator_label.pack(padx=14, pady=8)

        self._scroll_to_bottom()
        return wrapper, indicator_label

    def send_message(self):
        user_text = self.input_entry.get().strip()
        if not user_text:
            return

        self.input_entry.delete(0, "end")
        self.add_message_bubble(user_text, is_user=True)

        self.send_button.configure(state="disabled")
        self.input_entry.configure(state="disabled")

        indicator_wrapper, indicator_label = self.show_typing_indicator()

        threading.Thread(
            target=self._fetch_ai_response, 
            args=(user_text, indicator_wrapper, indicator_label), 
            daemon=True
        ).start()

    def _fetch_ai_response(self, user_text: str, indicator_wrapper: ctk.CTkFrame, indicator_label: ctk.CTkLabel):
        is_thinking = True

        def animate_indicator():
            dots = ["Thinking.", "Thinking..", "Thinking..."]
            idx = 0
            while is_thinking:
                try:
                    indicator_label.configure(text=dots[idx % len(dots)])
                    idx += 1
                    time.sleep(0.35)
                except Exception:
                    break

        anim_thread = threading.Thread(target=animate_indicator, daemon=True)
        anim_thread.start()

        try:
            response = self.chatbot.ask(user_text)
        except Exception as error:
            response = f"Sorry, I encountered an error: {error}"
        finally:
            is_thinking = False

        self.after(0, lambda: self._update_ui_after_response(indicator_wrapper, response))

    def _update_ui_after_response(self, indicator_wrapper: ctk.CTkFrame, response: str):
        indicator_wrapper.destroy()

        self.add_message_bubble(response, is_user=False)

        self.send_button.configure(state="normal")
        self.input_entry.configure(state="normal")
        self.input_entry.focus()

    def _scroll_to_bottom(self):
        """Forces scroll view to auto-scroll to the newest message."""
        self.update_idletasks()
        self.chat_container._parent_canvas.yview_moveto(1.0)