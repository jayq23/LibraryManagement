"""Groq Agent Wrapper with Tool / Function Calling support."""

import json
import logging

from groq import BadRequestError, Groq

from config import GROQ_API_KEY
from ai_agent.prompts import build_system_prompt
from ai_agent.tools import (
    add_book_copies,
    add_member,
    borrow_book,
    cancel_reservation,
    check_library_summary,
    check_member_status,
    collect_fine,
    collect_reservation,
    get_book_info,
    get_book_reservations,
    list_active_members,
    list_all_active_reservations,
    list_categories,
    reserve_book,
    return_book,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
MAX_TOKENS = 1500
REQUEST_TIMEOUT = 30.0  # seconds

# Map function names to their Python execution handlers
AVAILABLE_TOOLS = {
    "get_book_info": get_book_info,
    "check_member_status": check_member_status,
    "list_active_members": list_active_members,
    "check_library_summary": check_library_summary,
    "get_book_reservations": get_book_reservations,
    "list_all_active_reservations": list_all_active_reservations,
    "add_member": add_member,
    "borrow_book": borrow_book,
    "reserve_book": reserve_book,
    "cancel_reservation": cancel_reservation,
    "collect_reservation": collect_reservation,
    "add_book_copies": add_book_copies,
    "return_book": return_book,
    "collect_fine": collect_fine,
    "list_categories": list_categories,
}

# Tool definitions the model can call
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_book_info",
            "description": "Searches for books by title, author, or ISBN and returns details including shelf location and available copies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The title, author, or ISBN keyword to search for.",
                    }
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_member_status",
            "description": "Fetches active loans, reservations, and member details using a member ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "The member ID (e.g. M001, M005).",
                    }
                },
                "required": ["member_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_active_members",
            "description": "Retrieves the list of all active registered members in the library.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_library_summary",
            "description": "Provides overall statistics such as total books, active loans, overdue counts, and total members.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_book_reservations",
            "description": "Lists which members have an active reservation for a specific book, searched by title or ISBN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "isbn_or_title": {
                        "type": "string",
                        "description": "Title or ISBN of the book.",
                    }
                },
                "required": ["isbn_or_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_active_reservations",
            "description": "Retrieves the complete list of all active book reservations in the library across all members.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_member",
            "description": "Registers a new library member with a full name and email address. The member ID is generated automatically. Only call after the user confirmed the details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The member's full name.",
                    },
                    "email": {
                        "type": "string",
                        "description": "The member's email address.",
                    },
                },
                "required": ["name", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "borrow_book",
            "description": "Creates a new borrow transaction for a member using their member ID and book ISBN or title. Only call after confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "The borrowing member's ID (e.g. M005).",
                    },
                    "isbn_or_title": {
                        "type": "string",
                        "description": "Title or ISBN of the book to borrow.",
                    },
                },
                "required": ["member_id", "isbn_or_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_book",
            "description": "Creates a book reservation for a member using their member ID and the book title/ISBN. Only call after the user confirmed the details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "Member ID reserving the book (e.g. M001).",
                    },
                    "isbn_or_title": {
                        "type": "string",
                        "description": "Title or ISBN of the book to reserve. Prefer the ISBN when known.",
                    },
                },
                "required": ["member_id", "isbn_or_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": "Cancels an active book reservation given its numeric reservation ID. Only call after confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reservation_id": {
                        "type": "integer",
                        "description": "The ID of the reservation to cancel.",
                    }
                },
                "required": ["reservation_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "collect_reservation",
            "description": "Marks an active reservation as collected (the member picked up the book). Needs the numeric reservation ID; find it with get_book_reservations or check_member_status. Only call after the user confirmed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reservation_id": {
                        "type": "integer",
                        "description": "The reservation number, e.g. 12 for Res #12.",
                    }
                },
                "required": ["reservation_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_book_copies",
            "description": "Restocks and adds inventory copies to a book catalog entry using its title or ISBN. Only call after confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "isbn_or_title": {
                        "type": "string",
                        "description": "The book title or ISBN.",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "The number of copies to add.",
                    },
                },
                "required": ["isbn_or_title", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "return_book",
            "description": "Processes the return of a borrowed book using the active loan ID. Only call after confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_id": {
                        "type": "integer",
                        "description": "The loan transaction ID.",
                    }
                },
                "required": ["loan_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "collect_fine",
            "description": "Collects fine payment for a member using their member ID and payment amount. Only call after confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "The member ID (e.g. M001).",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The amount paid in PHP (₱).",
                    },
                },
                "required": ["member_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "Lists all book categories available in the library.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class GroqAgent:
    def __init__(self, model: str = "openai/gpt-oss-120b"):
        key = GROQ_API_KEY
        if not key or key == "your_groq_api_key_here":
            raise ValueError("Groq API key is missing. Please set GROQ_API_KEY in your .env file.")

        self.client = Groq(api_key=key, timeout=REQUEST_TIMEOUT, max_retries=2)
        self.model = model

    def _create(self, messages: list[dict]):
        """Calls the model. Retries once if Groq rejects a malformed tool call."""
        for attempt in range(2):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS,
                )
            except BadRequestError as error:
                if "tool_use_failed" in str(error) and attempt == 0:
                    logger.warning("Model produced a bad tool call, retrying once.")
                    continue
                raise

    @staticmethod
    def _run_tool(call) -> str:
        """Runs one tool call. Errors are returned to the model instead of crashing the reply."""
        handler = AVAILABLE_TOOLS.get(call.function.name)
        if handler is None:
            return f"Error: unknown tool '{call.function.name}'."
        try:
            args = json.loads(call.function.arguments or "{}")
            return str(handler(**args))
        except Exception as error:
            logger.warning("Tool %s failed: %s", call.function.name, error)
            return f"Error running tool: {error}"

    def generate_response(self, messages: list[dict]) -> str:
        """Returns the assistant reply. Raises on API failure; the caller handles it."""
        full_messages = [{"role": "system", "content": build_system_prompt()}] + messages

        for _ in range(MAX_TOOL_ROUNDS):
            response = self._create(full_messages)
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content or "No response generated."

            full_messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            })

            for call in message.tool_calls:
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": self._run_tool(call),
                })

        return "Sorry, I couldn't complete that request. Please try rephrasing it."