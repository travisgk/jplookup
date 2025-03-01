import random
import re
from bs4 import BeautifulSoup

# Text identification/search functions.
def is_kanji(char) -> bool:
    """Returns True if the given char is a Kanji."""
    return "\u4e00" <= char <= "\u9fff"


def is_kana(char) -> bool:
    """Returns True if the given char is hiragana/katakana."""
    return ("\u3040" <= char <= "\u309f") or ("\u30a0" <= char <= "\u30ff")


def find_all_indices(text: str, word: str) -> list:
    """Returns the indices of all occurrences of <word> inside <text>."""
    return [match.start() for match in re.finditer(re.escape(word), text)]


# Text removal functions.
def remove_text_in_brackets(text: str) -> str:
    """Returns text with any text in [..] removed."""
    return re.sub(r'\[.*?\]', '', text)


def remove_tags(html: str, omissions: list = []) -> str:
    """Returns the given text with all HTML tags removed."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if tag.name not in omissions:
            tag.unwrap()

    return str(soup)


def remove_unwanted_html(html: str) -> str:
    """Returns text with <ul> tags and pesky <span> tags removed."""
    soup = BeautifulSoup(html, "html.parser")
    
    TAGS = ["ul", "cite"]

    for tag in TAGS:
        for obj in soup.find_all(tag):
            obj.decompose()
    
    for obj in soup.find_all("span"):
        if obj.get("class") in ["HQToggle", "None"]:
            obj.decompose()

    return str(soup)


# Extraction functions.
def extract_tag_contents(html: str, tag: str) -> list:
    """
    Returns all text contained inside 
    the specified tag types (parents tags only).
    """
    soup = BeautifulSoup(html, "html.parser")
    return [str(t) for t in soup.find_all(tag) if t.find_parent(tag) is None]


def decode_furigana(word: str) -> list:
    """
    Returns a list of tuples, with each tuple 
    being the furigana for each kanji.
    """
    furi = []
    inside_furi = False
    for i, c in enumerate(word):
        if not inside_furi and c == "(":
            inside_furi = True
        elif inside_furi and c == ")":
            inside_furi = False
        elif inside_furi:
            furi[-1].append(c)
        else:
            furi.append([])

    return [tuple(f) for f in furi]


# Miscellaneous functions.
def random_hex(length: int) -> str:
    """Returns a random string of hex characters."""
    return ''.join(random.choices('0123456789abcdef', k=length))
