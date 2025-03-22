"""
Filename: jplookup._scrape._postprocessing.irrelevant_definitions.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines a function that removes all definitions
             from each Part of Speech that is deemed irrelevant.
             The criteria can be seen below.

Version: 1.0
License: MIT
"""

REMOVE_ARCHAIC_DEFINITIONS = True
REMOVE_LITERARY_DEFINITIONS = True
REMOVE_REGIONAL_DEFINITIONS = True
REMOVE_ALT_FORM_DEFINITIONS = True

ARCHAIC_TERMS = ["archaic", "classical japanese", "obsolete"]
LITERARY_TERMS = ["literary"]
REGIONAL_TERMS = ["regional", "dialect"]
FORM_PHRASES = [
    "alternative form of ",
    "alternative spelling of ",
    "stem or continuative form of ",
    "stem or continuative forms of ",
    "stem (or continuative) form of ",
    "stem (or continuative) forms of ",
    "stem form of ",
]


def remove_irrelevant_definitions(results: list) -> list:
    forbidden = []  # forbidden to show up in parentheses.
    if REMOVE_ARCHAIC_DEFINITIONS:
        forbidden.extend(ARCHAIC_TERMS)
    if REMOVE_LITERARY_DEFINITIONS:
        forbidden.extend(LITERARY_TERMS)
    if REMOVE_REGIONAL_DEFINITIONS:
        forbidden.extend(REGIONAL_TERMS)

    if len(forbidden) > 0:
        for i, r in enumerate(results):
            for etym_name, parts in r.items():
                for p_index, part_and_data in enumerate(parts.items()):
                    part_of_speech, word_data = part_and_data
                    def_indices_to_remove = []
                    for d_index, definition in enumerate(word_data["definitions"]):
                        def_text = definition["definition"].lower()

                        if def_text.startswith("("):
                            close_paren_i = def_text.find(")")
                            if close_paren_i >= 0:
                                context = def_text[1:close_paren_i]
                                if any(s in context for s in forbidden):
                                    def_indices_to_remove.append(d_index)
                                    continue

                        if any(phrase in def_text for phrase in FORM_PHRASES):
                            def_indices_to_remove.append(d_index)

                    for d_index in reversed(def_indices_to_remove):
                        del word_data["definitions"][d_index]

    return results
