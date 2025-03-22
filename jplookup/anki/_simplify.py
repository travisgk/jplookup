"""
Filename: jplookup.anki._simplify.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines helper functions that help
             the anki module break the outputs of jplookup.scrape(...)
             down into a much simpler format to display.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.identification import is_kanji, is_katakana


_TAG_PRIORITIES = [
    (
        "ipa",
        "pitch-accent",
        "kana",
    ),
    (
        "pitch-accent",
        "kana",
    ),
    (
        "ipa",
        "kana",
    ),
    ("kana",),
]


def search_for_pronunciation(pronunciations: list, tag_priority_i: int = 0):
    """
    Returns the first pronunciation dictionary with all the tags
    specified in <_TAG_PRIORITIES[tag_priority_i]>.

    If no pronunciation was found, and there's a further tuple to
    check again in <_TAG_PRIORITIES>, then this function
    runs recursively for that next tuple.
    """
    keys = _TAG_PRIORITIES[tag_priority_i]
    for p in pronunciations:
        if all(p.get(k) is not None for k in keys):
            return p

    if tag_priority_i < len(_TAG_PRIORITIES) - 1:
        return search_for_pronunciation(pronunciations, tag_priority_i + 1)

    return None


def _join_word_data(word_dicts: list) -> dict:
    """
    Returns a dictionary composed out of
    all the contents of each <word_dict>.
    """

    result = {
        "term": word_dicts[0][1]["term"],
        "pronunciation": word_dicts[0][1]["pronunciation"],
    }
    if word_dicts[0][1].get("counter"):
        result["counter"] = word_dicts[0][1]["counter"]

    # Adds the Definitions of every dictionary.
    definitions = []
    for part_of_speech, part_data in word_dicts:
        definitions.extend(part_data["definitions"])
        if result.get("counter") is None and part_data.get("counter"):
            result["counter"] = part_data["counter"]

    result["definitions"] = definitions

    # Adds the Usage Notes of every dictionary.
    usage_notes_str = ""
    for part_of_speech, part_data in word_dicts:
        usage_notes = part_data.get("usage-notes")
        if usage_notes:
            if len(usage_notes_str) > 0:
                usage_notes_str += "<br><br>"
            usage_notes_str += usage_notes

    if len(usage_notes_str) > 0:
        result["usage-notes"] = usage_notes_str

    return result


def combine_like_terms(card_parts: list) -> dict:
    """
    Returns the list of Part-of-Speech dicts
    combined into one single Etymology dict.
    """

    # Finds the most frequently occurring term.
    term_bank = {}
    for part_of_speech, part_data in card_parts:
        term = part_data["term"]
        if term_bank.get(term):
            term_bank[term].append((part_of_speech, part_data))
        else:
            term_bank[term] = [(part_of_speech, part_data)]

    best_term = list(term_bank.keys())[0]
    if len(term_bank) > 1:
        best_count = 0
        for term, parts_list in reversed(list(term_bank.items())):
            if len(parts_list) > best_count:
                best_term = term
                best_count = len(parts_list)

    new_card_parts = term_bank[best_term]

    # Determines each unique Part of Speech.
    unique_part_names = []
    for part_of_speech, part_data in new_card_parts:
        if part_of_speech not in unique_part_names:
            unique_part_names.append(part_of_speech)

    # Takes the parts selected by the best term
    # and sorts them into groups by the unique part names.
    sorted_parts = []
    for unique_part_name in unique_part_names:
        sorted_parts.append([])
        for part_of_speech, part_data in new_card_parts:
            if part_of_speech == unique_part_name:
                sorted_parts[-1].append((part_of_speech, part_data))

    # Each list of sorted parts is collapsed into a single dictionary.
    result_parts = {
        part_name: _join_word_data(parts)
        for part_name, parts in zip(
            unique_part_names,
            sorted_parts,
        )
    }

    # Removes the individualized attributes since
    # they're all the same; they're going to be moved
    # to a more global scope in the <result>.
    pronunciation = result_parts[unique_part_names[0]]["pronunciation"]
    kanji = result_parts[unique_part_names[0]]["term"]
    counter = result_parts[unique_part_names[0]].get("counter")
    for unique_part_name in unique_part_names:
        del result_parts[unique_part_name]["term"]
        del result_parts[unique_part_name]["pronunciation"]
        if counter:
            del result_parts[unique_part_name]["counter"]

    # Moves the pronunciation attributes to a more global scope in the dict.
    result = {}
    for key, value in pronunciation.items():
        if key not in ["furigana", "furigana-by-index"]:
            result[key] = value

    # Sets "kanji" to the term if it has diff chars from the kana.
    if kanji != result.get("kana"):  # and any(is_kanji(k) for k in kanji):
        if any(is_kanji(k) for k in kanji):
            result["kanji"] = kanji
            if pronunciation.get("furigana"):
                result["furigana"] = pronunciation["furigana"]
            elif pronunciation.get("furigana-by-index"):
                result["furigana-by-index"] = pronunciation["furigana-by-index"]
        elif all(is_katakana(k) for k in kanji):
            result["kana"] = kanji

    # For HTML generation.
    result["parts-of-speech"] = result_parts

    # Sets the usage notes.
    usage_notes_str = ""
    for unique_part_name in unique_part_names:
        usage_notes = result_parts[unique_part_name].get("usage-notes")
        if usage_notes:
            if len(usage_notes_str) > 0:
                usage_notes_str += "<br>"
            usage_notes_str += usage_notes

    result["usage-notes"] = usage_notes_str
    result["counter"] = counter

    return result
