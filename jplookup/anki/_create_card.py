"""
Filename: jplookup.anki._create_card.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines the primary function to take the
             outputs of a jplookup.scrape(...) call and convert
             it into a simplified dict object which has each key
             represent a field in an Anki card. 
             All the values will be strings, if blank it'll be "".
             These will be:
                 - kana
                 - kanji
                 - definitions
                 - ipa
                 - pretty-kana
                 - pretty-kanji
                 - usage-notes

Version: 1.0
License: MIT
"""

import json
from ._pretty_kanji import create_pretty_kanji
from ._field_str import create_definition_str, create_pretty_kana
from ._simplify import search_for_pronunciation, combine_like_terms


_DESIRED_PARTS = [
    "Noun",
    "Adjective",
    "Adnominal",
    "Verb",
    "Adverb",
    "Proper noun",
    "Interjection",
    "Particle",
    "Conjunction",
    "Phrase",
    "Proverb",
    "Pronoun",
    "Numeral",
]


def dict_to_anki_fields(
    scrape_output: dict,
    include_romanji: bool = False,
) -> dict:
    """
    Returns a dictionary with the fields:
        "kana", "kanji", "definitions", "ipa", "pretty-kana", "pretty-kanji"

    for the given output from jplookup.scrape.
    These fields are used to create Anki cards.
    """

    """
    Step 1) Using a dict, the number of times the best kana transcription
            from each part of speech occurs in all of the parts of speech
            is maintained.
    """
    # An Etymology dict can contain a disproportionate amount
    # of Parts of Speech.
    #
    # Only one Part of Speech per Etymology is allowed in this dict.
    # This is to reduce favoritism when selecting
    # the most frequent occurring kana.
    restricted_kana_bank = {}

    # Holds the data for all parts of speech by their kana.
    kana_bank = {}

    for etym_term, etym_data in scrape_output[0].items():
        part_appended = False
        for part_of_speech, word_data in etym_data.items():
            term = word_data["term"]
            pronunciations = word_data["pronunciations"]

            pronunciation = search_for_pronunciation(pronunciations)
            if pronunciation is not None:

                kana = pronunciation["kana"]
                matched_desired_part = False
                for part in _DESIRED_PARTS:
                    if part_of_speech.startswith(part):
                        part_of_speech = part
                        matched_desired_part = True
                        break

                if word_data.get("pronunciations"):
                    del word_data["pronunciations"]
                word_data["pronunciation"] = pronunciation

                if matched_desired_part:

                    def add_kana(bank: dict):
                        if bank.get(kana):
                            bank[kana].append((part_of_speech, word_data))
                        else:
                            bank[kana] = [(part_of_speech, word_data)]

                    if not part_appended:
                        part_appended = True
                        add_kana(restricted_kana_bank)

                    add_kana(kana_bank)

    if len(kana_bank.keys()) == 0:
        return None

    # Looks for the most popular kana transcription and
    # runs with that as the main pronunciation of the word.
    best_kana = list(restricted_kana_bank.keys())[0]
    if len(restricted_kana_bank) > 1:
        best_count = 0
        for kana, parts_list in list(restricted_kana_bank.items()):
            if len(parts_list) > best_count:
                best_kana = kana
                best_count = len(parts_list)

    # Selects the list of Parts-of-Speech dicts to use.
    best_parts = kana_bank[best_kana]
    term_count = {}
    for word in best_parts:
        term = word[1]["term"]
        if term_count.get(term):
            term_count[term] += 1
        else:
            term_count[term] = 1
    best_term = best_parts[0]
    best_count = 0
    for key, value in term_count.items():
        if value > best_count:
            best_term = key
            best_count = value

    card_parts = [p for p in best_parts if p[1]["term"] == best_term]
    card_parts = combine_like_terms(card_parts)
    if card_parts is None:
        return None

    kanji = card_parts.get("kanji")
    anki_card = {
        "key-term": kanji if kanji else card_parts["kana"],
        "kana": card_parts["kana"],
        "kanji": kanji if kanji else "",
    }

    # Comes up with definitions string.
    def_str = create_definition_str(card_parts, include_romanji=include_romanji)
    anki_card["definitions"] = def_str
    anki_card["ipa"] = card_parts.get("ipa", "")

    # Comes up with pretty kana.
    pretty_kana = create_pretty_kana(
        card_parts["kana"],
        pitch_accent=card_parts.get("pitch-accent", -1),
    )
    anki_card["pretty-kana"] = pretty_kana

    # Comes up with the pretty kanji.
    if card_parts.get("kanji") and len(card_parts["kanji"]) > 0:
        pretty_kanji = create_pretty_kanji(
            card_parts["kanji"],
            pitch_accent=card_parts.get("pitch-accent", -1),
            furigana=card_parts.get("furigana"),
            furigana_by_index=card_parts.get("furigana-by-index"),
        )
    else:
        pretty_kanji = ""
    anki_card["pretty-kanji"] = pretty_kanji

    # Adds the usage notes.
    anki_card["usage-notes"] = (
        card_parts.get("usage-notes", "").strip().replace("\n", "<br>")
    )

    # print(json.dumps(anki_card, indent=4, ensure_ascii=False))
    # print("\n\n\n")
    return anki_card
