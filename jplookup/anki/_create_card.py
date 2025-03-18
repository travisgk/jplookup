"""
Filename: jplookup.anki._create_card.py
Author: TravisGK
Date: 2025-03-16

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
from ._field_str import *
from ._simplify import *


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
    kana_bank = {}
    for etym_term, etym_data in scrape_output[0].items():
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
                    if kana_bank.get(kana):
                        kana_bank[kana].append((part_of_speech, word_data))
                    else:
                        kana_bank[kana] = [
                            (part_of_speech, word_data),
                        ]

    if len(kana_bank.keys()) == 0:
        return None

    best_kana = list(kana_bank.keys())[0]
    if len(kana_bank) > 1:
        best_count = 0
        for kana, parts_list in kana_bank.items():
            if len(parts_list) > best_count:
                best_kana = kana
                best_count = len(parts_list)

    # Selects the list of Parts-of-Speech dicts to use.
    card_parts = kana_bank[best_kana]
    card_parts = combine_like_terms(card_parts)

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
