"""Offline agent orchestration and authorized tool routing."""

import re
from datetime import date
from difflib import get_close_matches

from ai_agent.tools.availability_tool import check_availability
from ai_agent.tools.book_search_tool import search_books
from ai_agent.tools.member_status_tool import member_status
from ai_agent.tools.reservation_tool import reserve_book
from managers.fine_manager import FineManager
from managers.report_manager import ReportManager
from managers.transaction_manager import TransactionManager
from managers.book_manager import BookManager
from managers.member_manager import MemberManager


class LibraryAgent:
	"""Deterministic offline agent restricted to approved library operations."""

	def answer(self, prompt: str) -> str:
		clean_prompt = prompt.strip()
		lower_prompt = clean_prompt.lower()
		words = lower_prompt.split()
		for index, word in enumerate(words):
			match = get_close_matches(word, ("how", "many", "members", "customers", "status", "name", "about"), n=1, cutoff=0.82)
			if match:
				words[index] = match[0]
		lower_prompt = " ".join(words)
		parts = clean_prompt.split(maxsplit=1)
		command = parts[0].lower() if parts else ""
		argument = parts[1].strip() if len(parts) > 1 else ""
		if command in {"add", "register", "create"} and "member" in lower_prompt:
			match = re.match(r"(?:add|register|create) member\s+(M\d{3,})\s+(.+?)\s+([\w.+-]+@[\w.-]+)$", clean_prompt, re.IGNORECASE)
			if not match:
				return "Use: add member MEMBER_ID FULL NAME EMAIL"
			member_id, name, email = match.groups()
			MemberManager().add_member(member_id.upper(), name.strip(), email)
			return f"Member {member_id.upper()} ({name.strip()}) added."
		if command in {"accept", "collect", "claim"} and "reservation" in lower_prompt:
			reservation_id = re.search(r"\b\d+\b", argument)
			if not reservation_id:
				return "Use: accept reservation RESERVATION_ID"
			TransactionManager().collect_reservation(int(reservation_id.group()))
			return f"Reservation #{reservation_id.group()} marked as collected."
		if command in {"return", "returned"}:
			loan_id = re.search(r"\b\d+\b", argument)
			if not loan_id:
				return "Use: return LOAN_ID"
			TransactionManager().return_book(int(loan_id.group()))
			return f"Loan #{loan_id.group()} returned."
		if command in {"pay", "paid"} and "fine" in lower_prompt:
			fine_id = re.search(r"\b\d+\b", argument)
			if not fine_id:
				return "Use: pay fine FINE_ID"
			FineManager().pay(int(fine_id.group()))
			return f"Fine #{fine_id.group()} marked as paid."
		if command in {"restock", "addcopies", "add-copies"}:
			match = re.match(r"(?:restock|addcopies|add-copies)\s+(\d+)\s+(.+)", clean_prompt, re.IGNORECASE)
			if not match:
				return "Use: restock QUANTITY BOOK_TITLE"
			quantity, book_query = match.groups()
			books = BookManager().search(book_query)
			if not books:
				return "Book not found."
			BookManager().add_copies(books[0]["isbn"], int(quantity))
			return f"Added {quantity} cop(y/ies) to {books[0]['title']}."

		if command in {"help", "hello", "hi"}:
			return "Offline commands: search books, availability, member status, unpaid fines, library totals, active loans, reservations, borrow, and reserve."
		if any(phrase in lower_prompt for phrase in ("unpaid fine", "unpaid fines", "who owes", "overdue fine")):
			fines = FineManager().list_unpaid()
			return "\n".join(f"{fine['name']}: ${fine['amount']} ({fine['reason']})" for fine in fines) or "There are no unpaid fines."
		if any(phrase in lower_prompt for phrase in ("how many members", "how many customers", "library totals", "system totals")):
			summary = ReportManager().summary()
			return f"The library has {summary['members']} active members, {summary['total_books']} books, {summary['active_loans']} active loans, and {summary['overdue']} overdue loans."
		if any(phrase in lower_prompt for phrase in ("active loans", "current loans", "who borrowed")):
			loans = TransactionManager().active_loans()
			return "\n".join(f"{loan['name']} has {loan['title']} (due {loan['due_date']})." for loan in loans) or "There are no active loans."
		if any(phrase in lower_prompt for phrase in ("reservations", "reserved books", "who reserved")):
			reservations = TransactionManager().list_reservations("active")
			return "\n".join(f"{reservation['name']} reserved {reservation['title']}." for reservation in reservations) or "There are no active reservations."
		if lower_prompt.startswith(("is ", "how many copies", "check availability")):
			isbn = re.search(r"\b\d{10,13}\b", clean_prompt)
			if isbn:
				return f"{isbn.group()}: {check_availability(isbn.group())} copies available."
		member_id = re.search(r"\bM\d{3,}\b", clean_prompt, re.IGNORECASE)
		if member_id and ("member" in lower_prompt or "status" in lower_prompt or "loan" in lower_prompt or "fine" in lower_prompt or "about" in lower_prompt or "name" in lower_prompt):
			data = member_status(member_id.group().upper())
			if any(phrase in lower_prompt for phrase in ("what is the name", "what's the name", "who is", "how about")):
				return f"{member_id.group().upper()} is {data['member']['name']}."
			return f"{data['member']['name']} has {len(data['loans'])} active loan(s) and {len(data['fines'])} unpaid fine(s)."
		if command in {"search", "find"}:
			query = re.sub(r"^(for|books?)\s+", "", argument, flags=re.IGNORECASE)
			books = search_books(query)
			return "\n".join(f"{book['title']} by {book['author']} ({book['isbn']}) - {book['available_copies']} available" for book in books) or "No matching books found."
		if command in {"borrow", "checkout", "check-out"}:
			parts = argument.split()
			if len(parts) < 2:
				return "Use: borrow MEMBER_ID ISBN [YYYY-MM-DD]"
			member_id, isbn = parts[:2]
			due_date = date.fromisoformat(parts[2]) if len(parts) > 2 else None
			return f"Checkout #{TransactionManager().borrow(member_id.upper(), isbn, due_date)} recorded."
		if command in {"availability", "available"}:
			return f"{argument}: {check_availability(argument)} copies available."
		if command in {"status", "member"}:
			data = member_status(argument)
			return f"{data['member']['name']} has {len(data['loans'])} active loan(s) and {len(data['fines'])} unpaid fine(s)."
		if command == "reserve":
			reserve_parts = argument.split(maxsplit=1)
			if len(reserve_parts) != 2:
				return "Use: reserve MEMBER_ID BOOK_TITLE_OR_ISBN"
			member_id, book_query = reserve_parts
			if book_query.isdigit():
				isbn = book_query
			else:
				books = BookManager().search(book_query)
				if not books:
					return "Book not found."
				isbn = books[0]["isbn"]
			return f"Reservation #{reserve_book(member_id.upper(), isbn)} created."
		return "I did not recognize that. Type help to see available commands."
