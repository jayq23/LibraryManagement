# Conversation state and message history manager for GUI Chatbot.

import logging
import re
import threading

from ai_agent.agent import GroqAgent
from ai_agent.receipts import ReceiptRequest, pop_receipts
from ai_agent import tools

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20  # only the most recent messages are sent to the model
MEMBER_LIST_PATTERN = re.compile(r"\b(?P<status>inactive|active)\s+members?\b", re.IGNORECASE)


class Chatbot:
    # Initialize the component.
    def __init__(self):
        # Raises ValueError if the API key is missing. Catch this in the GUI.
        self.agent = GroqAgent()
        self.history: list[dict] = []
        self._lock = threading.Lock()

    # Handle recent messages.
    def _recent_messages(self) -> list[dict]:
        recent = self.history[-MAX_HISTORY_MESSAGES:]
        while recent and recent[0]["role"] != "user":
            recent = recent[1:]
        return recent

    # Handle ask.
    def ask(self, prompt: str) -> str:
        user_message = (prompt or "").strip()
        if not user_message:
            return "Please type a message."

        if not self._lock.acquire(blocking=False):
            return "Still working on your previous message. Please wait a moment."

        try:
            self.history.append({"role": "user", "content": user_message})

            try:
                response = self._direct_member_list_response(user_message)
                if response is None:
                    response = self.agent.generate_response(self._recent_messages())
            except Exception:
                logger.exception("AI request failed")
                self.history.pop()  # don't leave an unanswered user message behind
                return "Sorry, the assistant is unavailable right now. Please try again."

            self.history.append({"role": "assistant", "content": response})
            return response
        finally:
            self._lock.release()

    @staticmethod
    def _direct_member_list_response(prompt: str) -> str | None:
        match = MEMBER_LIST_PATTERN.search(prompt)
        if not match:
            return None

        if match.group("status").lower() == "inactive":
            return tools.list_inactive_members()
        return tools.list_active_members()

    # Handle pop receipts.
    def pop_receipts(self) -> list[ReceiptRequest]:
        return pop_receipts()

    # Retrieve get history.
    def get_history(self) -> list[dict]:
        return self.history

    # Clear clear history.
    def clear_history(self) -> None:
        self.history.clear()