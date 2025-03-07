import random
import re
from bs4 import BeautifulSoup


# Text identification/search functions.
def is_kanji(char) -> bool:
    """Returns True if the given char is a Kanji."""
    return "\u4e00" <= char <= "\u9fff"


def is_hiragana(char) -> bool:
    return "\u3040" <= char <= "\u309f"


def is_katakana(char) -> bool:
    return "\u30a0" <= char <= "\u30ff"


def is_kana(char) -> bool:
    """Returns True if the given char is hiragana/katakana."""
    return is_hiragana(char) or is_katakana(char)


def is_japanese_char(char) -> bool:
    """Returns True if the given char is a kanji or kana character."""
    return is_kanji(char) or is_kana(char)


def percent_japanese(text: str):
    """
    Returns a value from 0.0 to 1.0 indicating
    how many of the characters are Japanese.
    """
    num_jp = 0
    for c in text:
        if is_japanese_char(c):
            num_jp += 1
    return num_jp / len(text) if len(text) > 0 else 0


# Text removal functions.
def remove_text_in_brackets(text: str) -> str:
    """Returns text with any text in [..] removed."""
    return re.sub(r"\[.*?\]", "", text)


def shorten_html(html: str) -> str:
    """
    Returns the HTML text chopped down
    so that BeautifulSoup can parse it much more quickly.
    """
    DIV_TAG = '<div class="mw-heading mw-heading2">'

    jp_header_index = html.find('id="Japanese">Japanese</h')
    if jp_header_index >= 0:
        a = html.rfind(DIV_TAG, 0, jp_header_index)
        if a >= 0:
            b = html.find(DIV_TAG, a + 1)
            if b >= 0:
                html = (
                    "<!DOCTYPE html>\n<html>\n<body>\n" + html[a:b] + "</body>\n</html>"
                )

    return html


def remove_tags(html: str, omissions: list = []) -> str:
    """Returns the given text with all HTML tags removed."""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if tag.name not in omissions:
            tag.unwrap()

    return str(soup)


def remove_further_pronunciations(html: str) -> str:
    KEY = ">Further pronunciations</div>"
    soup = BeautifulSoup(html, "html.parser")

    further_ps = soup.find_all("div", class_="NavFrame")
    for p in further_ps:
        if KEY in str(p):
            p.decompose()

    return str(soup)


def remove_unwanted_html(html: str) -> str:
    """Returns text with <ul> tags and pesky <span> tags removed."""
    soup = BeautifulSoup(html, "html.parser")

    TAGS = ["ul", "cite"]

    for tag in TAGS:
        for obj in soup.find_all(tag):
            obj.decompose()

    for obj in soup.find_all("span", class_="HQToggle"):
        obj.decompose()

    for obj in soup.find_all("span", class_="None"):
        obj.decompose()

    for obj in soup.find_all("table", class_="wikitable kanji-table"):
        obj.decompose()

    return str(soup)


def remove_alternative_spellings(data):
    """Recursively removes all 'alternative-spellings' keys from nested dictionaries and lists."""
    if isinstance(data, dict):
        # Remove the key if it exists
        data.pop("alternative-spellings", None)
        # Recur for each value in the dictionary
        for key, value in data.items():
            data[key] = remove_alternative_spellings(value)
    elif isinstance(data, list):
        # Recur for each element in the list
        data = [remove_alternative_spellings(item) for item in data]
    return data


# Extraction functions.
def extract_tag_contents(html: str, tag: str) -> list:
    """
    Returns all text contained inside
    the specified tag types (parents tags only).
    """
    soup = BeautifulSoup(html, "html.parser")
    return [str(t) for t in soup.find_all(tag) if t.find_parent(tag) is None]


def separate_term_and_furigana(word: str):
    """
    Returns a string and a list, with the string
    containing the Japanese text outside parentheses
    and the list containing tuples of the furigana,
    with the index of each element corresponding to
    the aforementioned returned string. (str, list).
    """
    term = ""
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
            term += c

    furi = [tuple(f) for f in furi]
    return term, furi


def extract_japanese(subline: str) -> list:
    """
    Returns a list of every individual japanese phrase
    contained in the given text.
    """
    in_jp = False
    terms = [
        "",
    ]
    for i, c in enumerate(subline):
        if is_japanese_char(c):
            terms[-1] += c
            in_jp = True

        elif in_jp:  # not a jp char
            terms.append("")
            in_jp = False

    terms = [t for t in terms if len(t) > 0]
    return terms


# Miscellaneous functions.
def random_hex(length: int) -> str:
    """Returns a random string of hex characters."""
    return "".join(random.choices("0123456789abcdef", k=length))
