"""
Filename: jplookup._make_cards.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines a function that can take scraped
             data from jplookup and save a .txt file which
             can be directly imported into Anki.

Version: 1.0
License: MIT
"""

import json
import jplookup.anki


def make_cards(
    in_path: str = "jp-data.json",
    out_path: str = "anki-out.txt",
    debug_terms=None,
    verbose: bool = True,
):
    """
    Takes a .json full of scraped info from jplookup.scrape_all(...)
    then saves a .txt file that can be loaded into Anki.
    """

    FIELD_KEYS = [
        "key-term",
        "kana",
        "kanji",
        "definitions",
        "ipa",
        "pretty-kana",
        "pretty-kanji",
        "usage-notes",
        "counter",
    ]

    # loads the .json with the written jplookup info.
    with open(in_path, "r", encoding="utf-8") as jp_data:
        word_info = json.load(jp_data)

    with open(out_path, "w", encoding="utf-8") as out_file:
        for search_term, word_data in word_info.items():
            if (
                debug_terms is not None
                and len(debug_terms) > 0
                and not search_term in debug_terms
            ):
                continue  # if debugging, only debug terms aren't skipped.

            anki_card = jplookup.anki.dict_to_anki_fields(
                word_data, include_romanji=True
            )
            if anki_card is None:
                if verbose:
                    print(f"No card could be created for: {search_term}")
                continue

            # Writes every field of the Anki card to the output text file.
            for i, key in enumerate(FIELD_KEYS):
                out_file.write(anki_card[key])
                if i < len(FIELD_KEYS) - 1:
                    out_file.write("\t")
            out_file.write("\n")
