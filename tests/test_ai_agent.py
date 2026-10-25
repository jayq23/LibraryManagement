from ai_agent import agent, tools
from ai_agent.chatbot import Chatbot
from utils.search import matches_search, normalize_search_text


def test_list_inactive_members_returns_inactive_members(monkeypatch):
    class FakeMemberManager:
        def list_members(self):
            return [
                {"member_id": "M002", "name": "Inactive Reader", "email": "inactive@example.com", "active": False},
                {"member_id": "M001", "name": "Active Reader", "email": "active@example.com", "active": True},
            ]

    monkeypatch.setattr(tools, "MemberManager", FakeMemberManager)

    result = tools.list_inactive_members()

    assert result == (
        "Inactive Library Members:\n"
        "- M002 - Inactive Reader (inactive@example.com)"
    )


def test_list_inactive_members_handles_empty_result(monkeypatch):
    class FakeMemberManager:
        def list_members(self):
            return []

    monkeypatch.setattr(tools, "MemberManager", FakeMemberManager)

    assert tools.list_inactive_members() == "There are currently no inactive registered members."


def test_book_info_uses_manager_field_names(monkeypatch):
    class FakeBookManager:
        def list_books(self):
            return [
                {
                    "title": "The Hobbit",
                    "author": "J.R.R. Tolkien",
                    "isbn": "9780001",
                    "category_name": "Fantasy",
                    "shelf_location": "A-01",
                    "available_copies": 2,
                    "total_copies": 3,
                    "price": "100.00",
                }
            ]

    monkeypatch.setattr(tools, "BookManager", FakeBookManager)

    result = tools.get_book_info("hobbit")

    assert "Category: Fantasy" in result
    assert "Shelf Location: A-01" in result


def test_ai_book_lookup_is_case_and_article_tolerant(monkeypatch):
    class FakeBookManager:
        def list_books(self):
            return [{"title": "A Archive of Golden Days", "isbn": "9780003"}]

    monkeypatch.setattr(tools, "BookManager", FakeBookManager)

    assert "A Archive of Golden Days" in tools.get_book_info("a archive of the golden days")


def test_add_book_copies_ignores_markdown_markers_in_title(monkeypatch):
    class FakeBookManager:
        def list_books(self):
            return [{"title": "A Archive of the golden days", "isbn": "9780002"}]

        def add_copies(self, isbn, quantity):
            assert isbn == "9780002"
            assert quantity == 10

    monkeypatch.setattr(tools, "BookManager", FakeBookManager)

    result = tools.add_book_copies("**A Archive of the golden days**", 10)

    assert "Successfully added 10 copy/copies" in result


def test_inactive_members_tool_is_registered_and_exposed():
    assert agent.AVAILABLE_TOOLS["list_inactive_members"] is tools.list_inactive_members
    assert any(
        item["function"]["name"] == "list_inactive_members"
        for item in agent.TOOLS_SCHEMA
    )


def test_member_list_requests_use_the_matching_status_tool(monkeypatch):
    monkeypatch.setattr(tools, "list_active_members", lambda: "ACTIVE RESULT")
    monkeypatch.setattr(tools, "list_inactive_members", lambda: "INACTIVE RESULT")

    assert Chatbot._direct_member_list_response("how about active members") == "ACTIVE RESULT"
    assert Chatbot._direct_member_list_response("give me inactive members") == "INACTIVE RESULT"


def test_search_is_case_and_punctuation_tolerant():
    assert normalize_search_text("A Archive of Golden Days") == "a archive of golden days"
    assert matches_search("A Archive of Golden Days", "a archive of the golden days")
    assert matches_search("José Rizal", "jose rizal")
