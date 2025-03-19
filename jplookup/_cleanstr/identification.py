"""
Filename: jplookup._cleanstr.identification.py
Author: TravisGK
Date: 2025-03-15

Description: This file defines functions for
             identifying and finding Japanese text.

Version: 1.0
License: MIT
"""

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
    """Returns the matching pronunciation dictionary or None."""
    return next(
        (
            v
            for k, v in pronunciation_bank.items()
            if kana_matches(k, transcription["kana"])
        ),
        None,
    )
