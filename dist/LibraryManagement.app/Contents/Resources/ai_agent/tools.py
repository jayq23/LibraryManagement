"""Tool functions the AI agent is authorized to call."""

from managers.book_manager import BookManager
from managers.category_manager import CategoryManager
from managers.member_manager import MemberManager
from managers.transaction_manager import TransactionManager


def get_book_info(keyword: str) -> str:
    """Searches for books by title, author, or ISBN and returns details including shelf location and copies."""
    try:
        books = BookManager().list_books()
        kw = keyword.lower().strip()
        matched = [
            b for b in books
            if kw in b.get("title", "").lower()
            or kw in b.get("author", "").lower()
            or kw in b.get("isbn", "").lower()
        ]

        if not matched:
            return f"No books found matching '{keyword}'."

        results = []
        for book in matched:
            results.append(
                f"Title: {book.get('title')} | Author: {book.get('author')} | "
                f"ISBN: {book.get('isbn')} | Category: {book.get('category', 'N/A')} | "
                f"Shelf Location: {book.get('shelf', 'General Section')} | "
                f"Available Copies: {book.get('available_copies', 0)}/{book.get('total_copies', 0)} | "
                f"Price: ₱{book.get('price', '0.00')}"
            )
        return "\n".join(results)
    except Exception as error:
        return f"Error fetching book details: {error}"


def check_member_status(member_id: str) -> str:
    """Fetches active loans, reservations, and member details for a given member ID."""
    try:
        members = MemberManager().list_members()
        member = next((m for m in members if m.get("member_id") == member_id.strip().upper()), None)

        if not member:
            return f"Member with ID '{member_id}' was not found."

        status_str = "Active" if member.get("active") else "Inactive"
        output = [f"Member Details: {member.get('name')} (ID: {member.get('member_id')}) - Status: {status_str}"]

        # Active loans check
        loans = TransactionManager().active_loans()
        member_loans = [l for l in loans if l.get("member_id") == member_id.strip().upper()]

        if member_loans:
            output.append("\nActive Loans:")
            for loan in member_loans:
                output.append(f"- Loan #{loan.get('id')}: '{loan.get('title')}' (Due: {loan.get('due_date')})")
        else:
            output.append("\nNo active loans currently borrowed.")

        # Reservations check
        reservations = TransactionManager().list_reservations()
        member_res = [r for r in reservations if r.get("member_id") == member_id.strip().upper() and r.get("status") == "active"]

        if member_res:
            output.append("\nActive Reservations:")
            for res in member_res:
                output.append(f"- Res #{res.get('id')}: '{res.get('title')}' (Created: {res.get('created_on')})")

        return "\n".join(output)
    except Exception as error:
        return f"Error checking member status: {error}"


def check_library_summary() -> str:
    """Returns total summary metrics of the library."""
    try:
        from managers.report_manager import ReportManager
        stats = ReportManager().summary()
        return (
            f"Library Summary Overview:\n"
            f"- Total Catalog Books: {stats.get('total_books', 0)}\n"
            f"- Active Borrowed Loans: {stats.get('active_loans', 0)}\n"
            f"- Overdue Books: {stats.get('overdue', 0)}\n"
            f"- Registered Members: {stats.get('members', 0)}"
        )
    except Exception as error:
        return f"Error loading summary metrics: {error}"


def add_member(name: str, email: str, member_id: str | None = None) -> str:
    """Registers a new member. Auto-generates the next member ID (e.g. M007) if not provided."""
    try:
        name = name.strip()
        email = email.strip().lower()

        if not name or not email:
            return "Missing required fields — name and email are required."

        manager = MemberManager()
        existing_members = manager.list_members()

        if any(m.get("email", "").lower() == email for m in existing_members):
            return f"A member with email '{email}' already exists."

        # Auto-generate next Member ID kung walang ibinigay na member_id
        if not member_id or not member_id.strip():
            id_numbers = []
            for m in existing_members:
                mid = m.get("member_id", "")
                if mid.startswith("M") and mid[1:].isdigit():
                    id_numbers.append(int(mid[1:]))
            
            next_num = max(id_numbers, default=0) + 1
            member_id = f"M{next_num:03d}"
        else:
            member_id = member_id.strip().upper()
            if any(m.get("member_id") == member_id for m in existing_members):
                return f"A member with ID '{member_id}' already exists."

        manager.add_member(member_id=member_id, name=name, email=email)
        return f"Member '{name}' (ID: {member_id}) was successfully registered!"

    except Exception as error:
        return f"Error adding member: {error}"


def reserve_book(member_id: str, isbn_or_title: str) -> str:
    """Reserves a book for a member using their member ID and the book's title or ISBN."""
    try:
        member_id = member_id.strip().upper()
        books = BookManager().list_books()
        kw = isbn_or_title.strip().lower()
        
        target_book = next(
            (b for b in books if kw == b.get("isbn", "").lower() or kw in b.get("title", "").lower()), 
            None
        )
        
        if not target_book:
            return f"Book '{isbn_or_title}' was not found in the catalog."
            
        res_id = TransactionManager().reserve(member_id, target_book["isbn"])
        return f"Successfully reserved '{target_book['title']}' for Member {member_id}. Reservation ID: #{res_id}."
    except Exception as error:
        return f"Unable to reserve book: {error}"


def list_categories() -> str:
    """Returns a list of all active book categories in the library."""
    try:
        categories = CategoryManager().list_categories()
        if not categories:
            return "No book categories found."
        
        names = [c["name"] for c in categories]
        return "Library Book Categories:\n" + "\n".join([f"- {name}" for name in names])
    except Exception as error:
        return f"Error listing categories: {error}"