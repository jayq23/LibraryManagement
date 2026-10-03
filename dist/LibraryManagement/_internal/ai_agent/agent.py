"""Groq Agent Wrapper with Tool / Function Calling support."""

import json
from groq import Groq
from config import GROQ_API_KEY
from ai_agent.prompts import SYSTEM_PROMPT
from ai_agent.tools import (
    get_book_info, 
    check_member_status, 
    check_library_summary, 
    add_member,
    reserve_book,
    list_categories
)

# Map function names to their Python execution handlers
AVAILABLE_TOOLS = {
    "get_book_info": get_book_info,
    "check_member_status": check_member_status,
    "check_library_summary": check_library_summary,
    "add_member": add_member,
    "reserve_book": reserve_book,
    "list_categories": list_categories,
}

# Groq Function Calling Schema Definitions
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
                        "description": "The title, author, or ISBN keyword to search for."
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
                        "description": "The member ID (e.g. M001, M005)."
                    }
                },
                "required": ["member_id"],
            },
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
            "name": "add_member",
            "description": "Registers a new library member given a member ID, full name, and email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The member's full name."
                    },
                    "email": {
                        "type": "string",
                        "description": "The member's email address."
                    },
                    "member_id": {
                        "type": "string",
                        "description": "Optional custom member ID (e.g., M007). Omit to automatically generate the next ID."
                    }
                },
                "required": ["name", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_book",
            "description": "Creates a book reservation for a member using their member ID and the book title/ISBN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "Member ID reserving the book (e.g. M001)."
                    },
                    "isbn_or_title": {
                        "type": "string",
                        "description": "Title or ISBN of the book to reserve."
                    }
                },
                "required": ["member_id", "isbn_or_title"],
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

        self.client = Groq(api_key=key)
        self.model = model

    def generate_response(self, messages: list[dict]) -> str:
        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                max_tokens=1024,
            )

            response_message = response.choices[0].message

            if response_message.tool_calls:
                full_messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    if function_name in AVAILABLE_TOOLS:
                        tool_output = AVAILABLE_TOOLS[function_name](**function_args)
                    else:
                        tool_output = "Error: Requested tool function does not exist."

                    full_messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(tool_output),
                    })

                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    max_tokens=1024,
                )
                return second_response.choices[0].message.content or "No response generated."

            return response_message.content or "No response generated."

        except Exception as error:
            return f"Error communicating with AI Assistant: {str(error)}"