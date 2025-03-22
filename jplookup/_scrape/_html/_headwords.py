"""
Filename: jplookup._scrape._html._headwords.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines functions relating to extracting information
             from the contents of a <span class="headword-line">, which will
             contain the defined term, the furigana for any kanji (if any).

Version: 1.0
License: MIT
"""

import jaconv
from jplookup._cleanstr.identification import (
    is_hiragana,
    is_katakana,
    is_kana,
)
from jplookup._cleanstr.textwork import separate_term_and_furigana


# If True, this will remove any transcriptions that are written in katakana
# that correspond 1:1 with any other hiragana transcriptions.
# The opposite is also done if the "Usage notes" on the Wiktionary entry
# specifies that the word is typically written in katakana (i.e. many animals),
# so in that case the hiragana terms will be the ones removed
# while the katakana transcriptions remain.
REMOVE_DUPLICATE_KATAKANA = True


def break_up_headwords(headword_str: str) -> list:
    """Returns a list of headwords (kanji and furigana in parentheses)."""
    return headword_str.split("or")


def extract_info_from_headwords(headwords: list, prefers_katakana: bool = False):
    """
    Returns the Japanese term,
    a list of furigana
    and a list of hiragana transcriptions.
    """
    results = [separate_term_and_furigana(h) for h in headwords]

    """
    Step 1) Retrieves the terms from the headwords,
            gets the furigana for each term
            and then uses both to generate the kana
            transcription for the term.
    """
    # Gets the defining term for each headword.
    terms = [r[0] for r in results]
    if len(terms) == 0:
        return None

    # Gets a list of furigana for each kanji.
    furis = []
    for r in results:
        local_furi = r[1]
        local_furi = ["".join(f) for f in local_furi]
        furis.append(local_furi)

    # Gets the kana transcription for each headword.
    kanas = []
    for term, furi in zip(terms, furis):
        kana = ""
        for c, f in zip(term, furi):
            kana += c if is_kana(c) else f
        kanas.append(kana)

    """
    Step 2) Headwords whose transcriptions are just one-to-one katakana
            conversions are excluded.
    """
    if REMOVE_DUPLICATE_KATAKANA:
        # Determines which indices of <kana> contain
        # a transcription in either hiragana or katakana.
        hira_indices, kata_indices = [], []
        for i, r in enumerate(kanas):
            if is_hiragana(r[0]):
                hira_indices.append(i)
            elif is_katakana(r[0]):
                kata_indices.append(i)

        # Converts the hiragana transcriptions to katakana for comparison.
        hira_as_kata = {
            i: jaconv.hira2kata(kanas[i])
            for i in range(len(kanas))
            if i in hira_indices
        }

        # Iterates through both to find matches between the hiragana strings
        # and the katakana strings, if a match is found, then one of those
        # will be marked to be removed from the overall list of kana.
        indices_to_remove = []
        for i in kata_indices:
            for j in hira_indices:
                if kanas[i] == hira_as_kata[j]:
                    indices_to_remove.append(j if prefers_katakana else i)

        # Updates the lists of furigana and kana.
        if len(indices_to_remove) > 0:
            new_furis, new_kanas = [], []
            for i in range(len(kanas)):
                if i not in indices_to_remove:
                    new_furis.append(furis[i])
                    new_kanas.append(kanas[i])
            furis = new_furis
            kanas = new_kanas

    # if any(t != terms[0] for t in terms):
    #    print(f"The terms are different: {terms}")  # mere warning.

    return terms[0], furis, kanas
