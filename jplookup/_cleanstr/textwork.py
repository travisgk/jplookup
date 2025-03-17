"""
Filename: jplookup._cleanstr.textwork.py
Author: TravisGK
Date: 2025-03-16

Description: This file defines functions for 
             extracting text from within HTML
             and replacing text.

Version: 1.0
License: MIT
"""

from bs4 import BeautifulSoup
import jaconv
from .identification import is_kanji, is_japanese_char


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


def extract_pronunciation_info(p_str: str):
    """Returns the region, the kana, the pitch-accent and IPA."""
    region, kana, pitch_accent, ipa = None, None, None, None

    # Extracts the region.
    REGIONS = ["Tokyo", "Osaka"]
    for r in REGIONS:
        if p_str.startswith(f"({r})"):
            region = r
            break

    # Extracts the kana.
    found_kana = extract_japanese(p_str)
    if len(found_kana) > 0:
        kana = found_kana[0]

    # Extracts the accent number.
    accent_start_index = p_str.find("– [")
    if accent_start_index >= 0:
        accent_end_index = p_str.find("])", accent_start_index)
        if accent_end_index - accent_start_index == 4:
            pitch_accent = int(p_str[accent_end_index - 1])

    # Extracts the IPA.
    IPA_TERM = "IPA(key):"
    ipa_key_index = p_str.find(IPA_TERM)
    if ipa_key_index >= 0:
        ipa_key_index += len(IPA_TERM)
        ipa_start_index = p_str.find("[", ipa_key_index)
        if ipa_start_index >= 0:
            ipa_end_index = p_str.find("]", ipa_start_index)
            if ipa_end_index >= 0:
                ipa = p_str[ipa_start_index + 1 : ipa_end_index]

    return region, kana, pitch_accent, ipa


def kana_to_moras(kana: str) -> list:
    """
    Returns a list of moras that the given <kana> is broken into.
    """
    SMALL_FOR_DIGRAPH = "ゃゅょャュョァィゥェォ"
    moras = []
    i = 0
    while i < len(kana):
        current = kana[i]
        if (
            i + 1 < len(kana)
            and kana[i + 1] in SMALL_FOR_DIGRAPH
            and current not in SMALL_FOR_DIGRAPH
        ):
            moras.append(current + kana[i + 1])
            i += 2
        else:
            moras.append(current)
            i += 1
    return moras


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
