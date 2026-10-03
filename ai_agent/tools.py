"""Tool functions the AI agent is authorized to call."""

import logging
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from ai_agent.receipts import queue_receipt
from managers.book_manager import BookManager
from managers.category_manager import CategoryManager
from managers.member_manager import MemberManager
from managers.report_manager import ReportManager
from managers.transaction_manager import TransactionManager

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BORROW_DAYS = 14  # same default loan period as the Borrow / Return panel


def _text(value) -> str:
    """None-safe string conversion."""
    return str(value or "")


def _norm_id(member_id: str) -> str:
    return _text(member_id).strip().upper()


def _unexpected(action: str, error: Exception) -> str:
    """Logs the real error and returns a friendly message for the model/user."""
    logger.error("Tool failure while %s", action, exc_info=error)
    return f"Something went wrong while {action}. Please try again or use the GUI panel."


def _price(book: dict | None) -> Decimal:
    """Book price as Decimal, 0.00 if missing or invalid."""
    try:
        return Decimal(str((book or {}).get("price") or "0.00"))
    except InvalidOperation:
        return Decimal("0.00")


def get_book_info(keyword: str) -> str:
    """Searches for books by title, author, or ISBN and returns details including shelf location and copies."""
    try:
        kw = _text(keyword).strip().lower()
        if not kw:
            return "Please provide a title, author, or ISBN to search for."

        matched = [
            b for b in BookManager().list_books()
            if kw in _text(b.get("title")).lower()
            or kw in _text(b.get("author")).lower()
            or kw in _text(b.get("isbn")).lower()
        ]

        if not matched:
            return f"No books found matching '{keyword}'."

        results = []
        for book in matched:
            results.append(
                f"Title: {book.get('title')} | Author: {book.get('author')} | "
                f"ISBN: {book.get('isbn')} | Category: {book.get('category') or 'N/A'} | "
                f"Shelf Location: {book.get('shelf') or 'General Section'} | "
                f"Available Copies: {book.get('available_copies', 0)}/{book.get('total_copies', 0)} | "
                f"Price: ₱{book.get('price') or '0.00'}"
            )
        return "\n".join(results)
    except Exception as error:
        return _unexpected("fetching book details", error)


def check_member_status(member_id: str) -> str:
    """Fetches active loans, reservations, and member details for a given member ID."""
    try:
        member_id = _norm_id(member_id)
        member = MemberManager().get_member(member_id)

        if not member:
            return f"Member with ID '{member_id}' was not found."

        status_str = "Active" if member["active"] else "Inactive"
        output = [f"Member Details: {member['name']} (ID: {member['member_id']}) - Status: {status_str}"]

        transactions = TransactionManager()

        loans = [l for l in transactions.active_loans() if l.get("member_id") == member_id]
        if loans:
            output.append("\nActive Loans:")
            for loan in loans:
                output.append(f"- Loan #{loan.get('id')}: '{loan.get('title')}' (Due: {loan.get('due_date')})")
        else:
            output.append("\nNo active loans currently borrowed.")

        reservations = [
            r for r in transactions.list_reservations()
            if r.get("member_id") == member_id and r.get("status") == "active"
        ]
        if reservations:
            output.append("\nActive Reservations:")
            for res in reservations:
                output.append(f"- Res #{res.get('id')}: '{res.get('title')}' (Created: {res.get('created_on')})")
        else:
            output.append("\nNo active reservations.")

        return "\n".join(output)
    except Exception as error:
        return _unexpected("checking member status", error)


def list_active_members() -> str:
    """Lists all active registered library members."""
    try:
        members = MemberManager().list_members()
        active_list = [m for m in members if m.get("active")]

        if not active_list:
            return "There are currently no active registered members."

        lines = [f"- {m['member_id']} - {m['name']} ({m['email']})" for m in active_list]
        return "Active Library Members:\n" + "\n".join(lines)
    except Exception as error:
        return _unexpected("retrieving active members", error)


def check_library_summary() -> str:
    """Returns total summary metrics of the library."""
    try:
        stats = ReportManager().summary()
        return (
            f"Library Summary Overview:\n"
            f"- Total Catalog Books: {stats.get('total_books', 0)}\n"
            f"- Active Borrowed Loans: {stats.get('active_loans', 0)}\n"
            f"- Overdue Books: {stats.get('overdue', 0)}\n"
            f"- Registered Members: {stats.get('members', 0)}"
        )
    except Exception as error:
        return _unexpected("loading summary metrics", error)


def add_member(name: str, email: str) -> str:
    """Registers a new member. The member ID (e.g. M007) is generated automatically."""
    try:
        name = _text(name).strip()
        email = _text(email).strip().lower()

        if not name or not email:
            return "Missing required fields: name and email are required."
        if not EMAIL_PATTERN.match(email):
            return f"'{email}' is not a valid email address."

        member_id = MemberManager().add_member(member_id=None, name=name, email=email)
        return f"Member '{name}' (ID: {member_id}) was successfully registered!"
    except ValueError as error:
        return str(error)
    except Exception as error:
        return _unexpected("adding the member", error)


def borrow_book(member_id: str, isbn_or_title: str) -> str:
    """Creates a new borrow transaction (loan) for a member using member ID and book ISBN/title."""
    try:
        member_id = _norm_id(member_id)
        member = MemberManager().get_member(member_id)
        if not member:
            return f"Member with ID '{member_id}' was not found."
        if not member["active"]:
            return f"Member {member_id} is inactive and cannot borrow books."

        kw = _text(isbn_or_title).strip().lower()
        if not kw:
            return "Please provide a book title or ISBN."

        books = BookManager().list_books()
        exact = [b for b in books if kw == _text(b.get("isbn")).lower()]
        matches = exact or [b for b in books if kw in _text(b.get("title")).lower()]

        if not matches:
            return f"Book '{isbn_or_title}' was not found in the catalog."
        if len(matches) > 1:
            return f"Multiple books matched '{isbn_or_title}'. Please provide the exact ISBN."

        book = matches[0]
        due = date.today() + timedelta(days=BORROW_DAYS)
        loan_id = TransactionManager().borrow(member_id, book["isbn"], due)
        return (
            f"Successfully processed loan for Member {member_id}. "
            f"Book: '{book['title']}' (Loan ID: #{loan_id}). Due: {due:%b} {due.day}, {due.year}."
        )
    except ValueError as error:
        return f"Unable to process loan: {error}"
    except Exception as error:
        return _unexpected("processing book borrow", error)


def reserve_book(member_id: str, isbn_or_title: str) -> str:
    """Reserves a book for a member using their member ID and the book's title or ISBN."""
    try:
        member_id = _norm_id(member_id)
        member = MemberManager().get_member(member_id)
        if not member:
            return f"Member with ID '{member_id}' was not found."
        if not member["active"]:
            return f"Member {member_id} is inactive and cannot reserve books."

        kw = _text(isbn_or_title).strip().lower()
        if not kw:
            return "Please provide a book title or ISBN."

        books = BookManager().list_books()
        exact = [b for b in books if kw == _text(b.get("isbn")).lower()]
        matches = exact or [b for b in books if kw in _text(b.get("title")).lower()]

        if not matches:
            return f"Book '{isbn_or_title}' was not found in the catalog."

        if len(matches) > 1:
            listing = "\n".join(
                f"- {b.get('title')} by {b.get('author')} (ISBN: {b.get('isbn')})"
                for b in matches[:10]
            )
            return (
                f"{len(matches)} books match '{isbn_or_title}'. "
                f"Ask the user which one they mean (use the ISBN):\n{listing}"
            )

        book = matches[0]
        res_id = TransactionManager().reserve(member_id, book["isbn"])
        queue_receipt("Book Reservation Slip", "RES", res_id, member_id, _price(book))
        return (
            f"Successfully reserved '{book['title']}' for Member {member_id}. "
            f"Reservation ID: #{res_id}. The reservation slip opens automatically on screen."
        )
    except ValueError as error:
        return f"Unable to reserve book: {error}"
    except Exception as error:
        return _unexpected("reserving the book", error)


def cancel_reservation(reservation_id: int) -> str:
    """Cancels an active reservation using its reservation ID."""
    try:
        TransactionManager().cancel_reservation(reservation_id)
        return f"Reservation #{reservation_id} was successfully canceled."
    except ValueError as error:
        return f"Unable to cancel reservation: {error}"
    except Exception as error:
        return _unexpected("canceling reservation", error)


def collect_reservation(reservation_id: int) -> str:
    """Marks an active reservation as collected."""
    try:
        try:
            res_id = int(reservation_id)
        except (TypeError, ValueError):
            return "Reservation ID must be a number (e.g. 12)."

        manager = TransactionManager()
        reservation = next((r for r in manager.list_reservations() if r.get("id") == res_id), None)

        if not reservation:
            return f"Reservation #{res_id} was not found."
        if reservation.get("status") != "active":
            return f"Reservation #{res_id} is already {reservation.get('status')} and cannot be collected."

        manager.collect_reservation(res_id)
        return f"Reservation #{res_id} for '{reservation.get('title')}' was marked as collected."
    except ValueError as error:
        return f"Unable to collect reservation: {error}"
    except Exception as error:
        return _unexpected("collecting the reservation", error)


def add_book_copies(isbn_or_title: str, quantity: int) -> str:
    """Adds inventory copies to an existing book in the catalog using title or ISBN."""
    try:
        kw = _text(isbn_or_title).strip().lower()
        if not kw:
            return "Please provide a book title or ISBN."
        if quantity <= 0:
            return "Quantity to add must be greater than 0."

        books = BookManager().list_books()
        exact = [b for b in books if kw == _text(b.get("isbn")).lower()]
        matches = exact or [b for b in books if kw in _text(b.get("title")).lower()]

        if not matches:
            return f"Book '{isbn_or_title}' was not found in the catalog."
        if len(matches) > 1:
            return f"Multiple books matched '{isbn_or_title}'. Please provide the exact ISBN."

        book = matches[0]
        BookManager().add_copies(book["isbn"], quantity)
        return f"Successfully added {quantity} copy/copies to '{book['title']}' (ISBN: {book['isbn']})."
    except Exception as error:
        return _unexpected("adding copies to inventory", error)


def return_book(loan_id: int) -> str:
    """Processes the return of a borrowed book using its loan ID."""
    try:
        result = TransactionManager().return_book(loan_id)
        msg = f"Loan #{loan_id} returned successfully."

        # The manager returns a dict like {"days_late": 2, "fine_amount": 20.0, ...}
        if isinstance(result, dict):
            fine = Decimal(str(result.get("fine_amount") or 0))
            days_late = result.get("days_late") or 0
        else:
            fine = Decimal(str(result or 0))
            days_late = 0

        if fine > 0:
            late = f" ({days_late} day(s) late)" if days_late else ""
            msg += f" Late return penalty applied: ₱{fine:,.2f}{late}."
        return msg
    except ValueError as error:
        return f"Unable to process return: {error}"
    except Exception as error:
        return _unexpected("returning the book", error)


def collect_fine(member_id: str, amount: float) -> str:
    """Processes payment for outstanding unpaid fines for a member."""
    try:
        member_id = _norm_id(member_id)
        member = MemberManager().get_member(member_id)
        if not member:
            return f"Member with ID '{member_id}' was not found."
        if amount <= 0:
            return "Payment amount must be greater than 0."

        TransactionManager().pay_fines_for_member(member_id, Decimal(str(amount)))
        return f"Successfully collected fine payment of ₱{amount:.2f} for Member {member_id}."
    except ValueError as error:
        return f"Unable to collect fine: {error}"
    except Exception as error:
        return _unexpected("collecting fine payment", error)


def get_book_reservations(isbn_or_title: str) -> str:
    """Lists members who have an active reservation for a book (by title or ISBN)."""
    try:
        kw = _text(isbn_or_title).strip().lower()
        if not kw:
            return "Please provide a book title or ISBN."

        matched = [
            r for r in TransactionManager().list_reservations()
            if r.get("status") == "active"
            and (kw == _text(r.get("isbn")).lower() or kw in _text(r.get("title")).lower())
        ]

        if not matched:
            return f"No active reservations found for '{isbn_or_title}'."

        names = {m["member_id"]: m["name"] for m in MemberManager().list_members()}
        lines = [
            f"- Res #{r.get('id')}: {names.get(r.get('member_id'), 'Unknown')} "
            f"({r.get('member_id')}) for '{r.get('title')}' (Created: {r.get('created_on')})"
            for r in matched
        ]
        return f"Active reservations for '{isbn_or_title}':\n" + "\n".join(lines)
    except Exception as error:
        return _unexpected("searching reservations", error)


def list_all_active_reservations() -> str:
    """Lists all active book reservations across all members in the entire library system."""
    try:
        reservations = [
            r for r in TransactionManager().list_reservations()
            if r.get("status") == "active"
        ]

        if not reservations:
            return "There are currently no active reservations in the library."

        names = {m["member_id"]: m["name"] for m in MemberManager().list_members()}
        lines = [
            f"- Res #{r.get('id')}: Member {r.get('member_id')} ({names.get(r.get('member_id'), 'Unknown')}) "
            f"reserved '{r.get('title')}' (ISBN: {r.get('isbn')}) on {r.get('created_on')}"
            for r in reservations
        ]
        return "Complete List of Active Reservations:\n" + "\n".join(lines)
    except Exception as error:
        return _unexpected("retrieving all active reservations", error)


def list_categories() -> str:
    """Returns a list of all active book categories in the library."""
    try:
        categories = CategoryManager().list_categories()
        names = [c.get("name") for c in categories if c.get("name")]
        if not names:
            return "No book categories found."
        return "Library Book Categories:\n" + "\n".join(f"- {name}" for name in names)
    except Exception as error:
        return _unexpected("listing categories", error)