"""
Filename: jplookup._cleanstr._textwork.py
Author: TravisGK
Date: 2025-03-13

Description: This file defines functions for identifying characters,
             removing specific parts of HTML,
             and extracting text from within HTML.

Version: 1.0
License: MIT
"""

import re
from bs4 import BeautifulSoup
import jaconv


# Text identification/search functions.
def is_kanji(char) -> bool:
    """Returns True if the given char is Kanji."""
    return "\u4e00" <= char <= "\u9fff"


def is_hiragana(char) -> bool:
    """Returns True if the given char is hiragana."""
    return "\u3040" <= char <= "\u309f"


def is_katakana(char) -> bool:
    """Returns True if the given char is katakana."""
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
    total = 0
    in_tag = False
    for c in text:
        if c in "()":
            pass
        elif c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag and is_japanese_char(c):
            num_jp += 1
            total += 1
        else:
            total += 1
    return num_jp / total if total > 0 else 0


def kata_matches(p_kata: str, t_kata: str) -> bool:
    """
    Returns True if the katakana match each other,
    with the flexibility that a char in <t_kana> can
    be either イ or ウ and still match with a <p_kana>'s
    corresponding ー.
    """
    if len(p_kata) != len(t_kata):
        return False

    for p, t in zip(p_kata, t_kata):
        if p != t and not (p == "ー" and t in "イウ"):
            return False

    return True


def kana_matches(p_kana: str, t_kana: str) -> bool:
    """
    Returns True if the kana match each other,
    with the flexibility that a char in <t_kana> can
    be either い(イ) or う(ウ) and still match with a <p_kana>'s
    corresponding ー.
    """
    if len(p_kana) != len(t_kana):
        return False

    p_kata = jaconv.hira2kata(p_kana)
    t_kata = jaconv.hira2kata(t_kana)

    return kata_matches(p_kata, t_kata)


def find_pronunciation_match(pronunciation_bank: dict, transcription: dict):
    """
    Returns the pronunciation dictionary in <pronunciation_bank>
    that matches up to the given <transcription> by the kana
    contained in both.

    If there's no match, then None is returned.
    """
    t_kana = transcription["kana"]

    for p_kana, value in pronunciation_bank.items():
        if kana_matches(p_kana, t_kana):
            return value

    return None


# Text removal functions.
def remove_text_in_brackets(text: str) -> str:
    """Returns text with any text in [...] removed."""
    return re.sub(r"\[.*?\]", "", text)


def shorten_html(html: str) -> str:
    """
    Returns the Wiktionary HTML text chopped down
    to only the Japanese section,
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
    """
    Returns the HTML with any 'Further pronunciations' removed entirely.
    """
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
    """
    Recursively removes all 'alternative-spellings'
    keys from nested dictionaries and lists and returns the result.
    """
    if isinstance(data, dict):
        # Removes the key if it exists.
        data.pop("alternative-spellings", None)

        # Runs recursion for each key/value in the dict.
        for key, value in data.items():
            data[key] = remove_alternative_spellings(value)
    elif isinstance(data, list):
        # Runs recursion for each list.
        data = [remove_alternative_spellings(item) for item in data]

    return data


def remove_spaces_jp(text: str) -> str:
    # Match spaces that do NOT follow a Japanese punctuation mark
    return re.sub(r"(?<![。、])\s+", "", text)


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
    uses_furi = False
    for i, c in enumerate(word):
        if not inside_furi and c == "(":
            inside_furi = True
            uses_furi = True
        elif inside_furi and c == ")":
            inside_furi = False
        elif is_japanese_char(c):
            if inside_furi:
                furi[-1].append(c)
            else:
                furi.append([])
                term += c

    # Identifies stretches of pure kanji.
    if uses_furi:
        sorted_kanji = [
            [],
        ]
        sorted_kanji_starts = []
        sorted_furi = [
            [],
        ]
        num_kanji_in_row = 0
        i = 0
        for c, f in zip(term, furi):
            if is_kanji(c):
                if num_kanji_in_row == 0:
                    sorted_kanji.append(
                        [
                            c,
                        ]
                    )
                    sorted_kanji_starts.append(i)
                    sorted_furi.append(
                        [
                            f,
                        ]
                    )
                else:
                    sorted_kanji[-1].append(c)
                    sorted_furi[-1].append(f)
                num_kanji_in_row += 1
            else:
                num_kanji_in_row = 0
            i += 1

        # Sometimes the furigana can be thrown above words incorrectly on Wiktionary;
        # if the program can clearly see furigana are supposed to be distributed
        # over the same number of kanji, then it will do so.
        for k, index, f in zip(sorted_kanji, sorted_kanji_starts, sorted_furi):
            if len(k) > 1:
                joined_furi = "".join(["".join(element) for element in f])

                # Redistributes.
                if len(k) == len(joined_furi):
                    for i, c in enumerate(joined_furi):
                        f_index = index + i
                        furi[f_index] = [
                            joined_furi[i],
                        ]

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


# Replacement functions.
def change_furi_to_kata(text: str, term: str) -> str:
    """
    Returns the given sentence string with any furigana
    for the searched <term> being forced to katakana.

    This is called only if the entry explicitly mentions
    that the term is spelled with katakana instead of hiragana.
    """

    """
    Step 1) Looks for text that matches the term 
            while ignoring text in parentheses.
    """
    matching_indices = []  # indices.

    inside_furi = False
    i = 0
    current_sequence = []  # indices.
    for i, c in enumerate(text):
        if c == "(":
            inside_furi = True
        elif c == ")":
            inside_furi = False
        elif not inside_furi:
            match_index = len(current_sequence)
            if c == term[match_index]:
                current_sequence.append(i)  # saves index.
                if len(current_sequence) == len(term):
                    matching_indices.extend(current_sequence)
                    current_sequence = []  # resets.
            else:
                current_sequence = []  # resets.

    """
    Step 2) Looks for the indices of open parentheses.
            These are checked for uniqueness since multiple
            kanji may share the same furigana statement.
    """
    parens_indices = []
    for i in matching_indices:
        if is_kanji(text[i]):
            open_paren_i = text.find("(", i + 1)
            if len(parens_indices) == 0 or open_paren_i != parens_indices[-1]:
                parens_indices.append(open_paren_i)

    """
    Step 3) Looks for the closing parentheses and replaces
            the furigana with katakana accordingly.
    """
    for i in parens_indices:
        closing_paren_i = text.find(")", i + 1)
        if closing_paren_i >= 0:
            start = i + 1
            kana = text[start:closing_paren_i]
            new_kana = jaconv.hira2kata(kana)
            text = text[:start] + new_kana + text[closing_paren_i:]

    return text
