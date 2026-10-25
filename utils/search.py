import re
import unicodedata

SEARCH_STOPWORDS = {"a", "an", "of", "the"}


def normalize_search_text(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
    return " ".join(text.casefold().split())


def search_terms(value) -> list[str]:
    terms = normalize_search_text(value).split()
    meaningful_terms = [term for term in terms if term not in SEARCH_STOPWORDS]
    return meaningful_terms or terms


def matches_search(value, query) -> bool:
    haystack = normalize_search_text(value)
    return all(term in haystack for term in search_terms(query))
