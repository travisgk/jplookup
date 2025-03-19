"""
Filename: jplookup._cleanstr.removal.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines functions for 
             removing specific parts of HTML.

Version: 1.0
License: MIT
"""

import re
from bs4 import BeautifulSoup


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
