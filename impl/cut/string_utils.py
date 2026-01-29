"""String manipulation utilities for testing."""


def reverse_string(s: str) -> str:
    """Reverse a string."""
    return s[::-1]


def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word."""
    return s.title()


def count_words(s: str) -> int:
    """Count the number of words in a string."""
    if not s.strip():
        return 0
    return len(s.split())


def is_palindrome(s: str) -> bool:
    """Check if a string is a palindrome (case-insensitive, ignoring whitespace)."""
    cleaned = ''.join(s.lower().split())
    return cleaned == cleaned[::-1]


def remove_whitespace(s: str) -> str:
    """Remove all whitespace from a string."""
    return ''.join(s.split())


def count_characters(s: str, char: str) -> int:
    """Count occurrences of a specific character in a string."""
    if len(char) != 1:
        raise ValueError("char must be a single character")
    return s.count(char)


def replace_substring(s: str, old: str, new: str) -> str:
    """Replace all occurrences of old substring with new substring."""
    return s.replace(old, new)


def extract_numbers(s: str) -> list:
    """Extract all numbers from a string and return as list of floats."""
    import re
    numbers = re.findall(r'-?\d+\.?\d*', s)
    return [float(n) for n in numbers]


def is_anagram(s1: str, s2: str) -> bool:
    """Check if two strings are anagrams (case-insensitive, ignoring whitespace)."""
    s1_cleaned = ''.join(sorted(s1.lower().replace(' ', '')))
    s2_cleaned = ''.join(sorted(s2.lower().replace(' ', '')))
    return s1_cleaned == s2_cleaned


def truncate(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to max_length, appending suffix if truncated."""
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix
