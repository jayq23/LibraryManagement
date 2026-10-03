"""Conversation state and message history manager for GUI Chatbot."""

import logging
import threading

from ai_agent.agent import GroqAgent
from ai_agent.receipts import ReceiptRequest, pop_receipts

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20  # only the most recent messages are sent to the model


class Chatbot:
    def __init__(self):
        # Raises ValueError if the API key is missing. Catch this in the GUI.
        self.agent = GroqAgent()
        self.history: list[dict] = []
        self._lock = threading.Lock()

    def _recent_messages(self) -> list[dict]:
        """Last N messages, always starting on a user message."""
        recent = self.history[-MAX_HISTORY_MESSAGES:]
        while recent and recent[0]["role"] != "user":
            recent = recent[1:]
        return recent

    def ask(self, prompt: str) -> str:
        """Accepts user prompt, updates history, calls Groq Agent, and returns response.

        Safe to call from a worker thread. Blocks until the reply is ready.
        """
        user_message = (prompt or "").strip()
        if not user_message:
            return "Please type a message."

        if not self._lock.acquire(blocking=False):
            return "Still working on your previous message. Please wait a moment."

        try:
            self.history.append({"role": "user", "content": user_message})

            try:
                response = self.agent.generate_response(self._recent_messages())
            except Exception:
                logger.exception("AI request failed")
                self.history.pop()  # don't leave an unanswered user message behind
                return "Sorry, the assistant is unavailable right now. Please try again."

            self.history.append({"role": "assistant", "content": response})
            return response
        finally:
            self._lock.release()

    def pop_receipts(self) -> list[ReceiptRequest]:
        """Receipts queued by tools (reservation/collection). Call on the GUI thread after ask()."""
        return pop_receipts()

    def get_history(self) -> list[dict]:
        """Returns current message history."""
        return self.history

    def clear_history(self) -> None:
        """Clears memory state."""
        self.history.clear()