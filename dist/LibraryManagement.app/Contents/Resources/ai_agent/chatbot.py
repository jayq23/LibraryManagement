"""Conversation state and message history manager for GUI Chatbot."""

from ai_agent.agent import GroqAgent


class Chatbot:
    def __init__(self):
        self.agent = GroqAgent()
        self.history: list[dict] = []

    def ask(self, prompt: str) -> str:
        """Accepts user prompt, updates history, calls Groq Agent, and returns response."""
        user_message = prompt.strip()
        if not user_message:
            return "Please type a message."

        # Add user prompt to conversation history
        self.history.append({"role": "user", "content": user_message})

        # Get response from Groq API
        response = self.agent.generate_response(self.history)

        # Add assistant response to history
        self.history.append({"role": "assistant", "content": response})

        return response

    def get_history(self) -> list[dict]:
        """Returns current message history."""
        return self.history

    def clear_history(self) -> None:
        """Clears memory state."""
        self.history.clear()