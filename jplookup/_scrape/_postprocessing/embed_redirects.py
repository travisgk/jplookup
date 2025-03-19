"""
Filename: jplookup._scrape._postprocessing.embed_redirects.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines a function which will 
             handles redirected data entries,
             as is the case when Wiktionary links to a
             completely different page for a different spelling.

Version: 1.0
License: MIT
"""

import re
import jaconv
from jplookup._cleanstr.identification import (
    is_hiragana,
    is_kanji,
    is_kana,
    is_japanese_char,
)

# if True, removes the kanji that may appear before a definition.
REMOVE_CONTEXT_SPECIFIERS_FROM_DEFS = True

# if True, kana pronunciations will be used as alternative spellings
# when matching up redirects.
USE_KANA_AS_ALT_SPELLING = True


def _remove_alt_spellings(data):
    if isinstance(data, dict):
        data.pop("alternative-spellings", None)  # pop out the alt spelling
        for key, value in data.items():
            data[key] = _remove_alt_spellings(value)  # recursion.
    elif isinstance(data, list):
        data = [_remove_alt_spellings(item) for item in data]  # recursion.
    return data


def _sort_dict_by_trailing_number(data):
    """
    Sorts a dictionary by the number at the end of each key
    and returns a new normal dictionary.
    """

    def extract_number(key):
        match = re.search(r"(\d+)$", key)  # Find the trailing number
        return (
            int(match.group(1)) if match else float("inf")
        )  # defaults to infinity if no number

    sorted_items = sorted(data.items(), key=lambda item: extract_number(item[0]))
    result = dict(sorted_items)  # Convert back to a normal dictionary
    return result


def embed_redirects(
    clean_data: list,
    redirects: dict,
    original_term: str,
) -> list:
    """
    Returns the <clean_data>, that being the list of scraped Wiktionary entries,
    where any of the Etymology entries under <clean_data[0]> that are None
    will be matched up to any other later elements in the <clean_data> list.
    """
    redirect_keys = redirects.keys()

    if len(clean_data) == 0:
        return None

    # A temp var is used to check for an early return later.
    result = None
    if len(clean_data) == 1:
        result = clean_data

    """
    Step 1) If there are no redirects specified, meaning that the program
            failed to match them up, and all the Etymology terms in the first
            element of <clean_data> are None, and the number of them happen
            to match up with the number of elements occurring 
            after <clean_data[0]>, then the program simply fills in the blanks
            of <clean_data[0]> with the first Etymology of every element
            in <clean_data[1:]>.
    """
    if (
        (redirects is None or len(redirects.keys()) == 0)
        and len(clean_data[0].keys()) == len(clean_data) - 1
        and all(v is None for v in clean_data[0].values())
    ):
        result = {
            ("Etymology " + str(i + 1)): w[list(w.keys())[0]]
            for i, w in enumerate(clean_data[1:])
        }

    """
    Step 2) For any redirects, any definitions with specified context kanji
            that DO NOT match the original term are removed;
            those without kanji or with matching kanji remain.
    """
    for entry_index, entry in enumerate(clean_data):
        for etym in entry.values():
            if etym is None:
                continue

            for part_of_speech, contents in etym.items():
                if part_of_speech == "alternative-spellings":
                    continue  # skips alternative spellings.

                defs = contents.get("definitions")
                if defs is None:
                    continue  # skips Parts of Speech w/o Definitions.

                # Iterates through all the Definitions
                # and only takes Definitions that either have
                # no context specification at all or whose context
                # specification matches the original term.
                def_indices_to_remove = []
                for i, definition in enumerate(defs):
                    def_str = definition["definition"]
                    if is_japanese_char(def_str[0]):
                        # There are kanji specifiers for this definition;
                        # the program ensures only relevant definitions
                        # of child entries are included.
                        colon_index = def_str.find(":")
                        if colon_index >= 0:
                            # Determines the context specifiers.
                            kanji_terms = def_str[:colon_index].split(",")
                            kanji_terms = [k.strip() for k in kanji_terms]

                            # Deletes any definitions that have context
                            # specifiers which do not match up with the
                            # <original_term>, then removes said context
                            # specifiers from definitions.
                            if REMOVE_CONTEXT_SPECIFIERS_FROM_DEFS:
                                end_i = colon_index + 1
                                definition["definition"] = def_str[end_i:].strip()

                            if entry_index > 0 and original_term not in kanji_terms:
                                def_indices_to_remove.append(i)

                if len(def_indices_to_remove) > 0:
                    contents["definitions"] = [
                        d for i, d in enumerate(defs) if i not in def_indices_to_remove
                    ]

    if result is not None:
        return result

    """
    Step 3) Goes through each wiki redirect Entry scraped in the given clean data
            (that comes after the root entry) and sees which Etymology is
            referred to by each wiki Entry's referal in <redirects>.

            If the redirect Entry has more than one Etymology,
            then the redirect's Etymology to be used is found
            by matching up the original term 
            with the redirect Entry's given alternative spellings.
    """
    was_redirected = [False for _ in clean_data]
    for i, entry in enumerate(clean_data[1:]):
        index = i + 1

        # Goes through each contained Etymology header
        # in the subsequent Entry to look for alternative spellings.
        for etym_key, etymology in entry.items():
            alt_spellings = etymology.get("alternative-spellings")
            kana_spellings = []
            if USE_KANA_AS_ALT_SPELLING:
                for part_of_speech, word_data in etymology.items():
                    if part_of_speech == "alternative-spellings":
                        continue
                    pronunciations = word_data.get("pronunciations")
                    if pronunciations is not None:
                        for p in pronunciations:
                            kana = p.get("kana")
                            if kana is not None:
                                new_spellings = [
                                    kana,
                                ]
                                if is_hiragana(kana[0]):
                                    new_spellings.append(jaconv.hira2kata(kana))
                                kana_spellings.extend(
                                    [
                                        n
                                        for n in new_spellings
                                        if n not in kana_spellings
                                    ]
                                )

            if alt_spellings is None and len(kana_spellings) == 0:
                continue

            new_etym_header = None
            new_etym = None
            for part_of_speech, word_data in etymology.items():
                if part_of_speech == "alternative-spellings":
                    continue

                term = word_data.get("term")  # gets the redirect etym's term.
                if term in redirect_keys and (
                    len(entry) == 1
                    or (alt_spellings is not None and original_term in alt_spellings)
                    or original_term in kana_spellings
                ):
                    # This is the Etymology that's being referred to.
                    new_etym_header = redirects[term]
                    new_etym = etymology

                    if (
                        alt_spellings
                        and original_term in alt_spellings
                        and all(is_kana(c) for c in new_etym[part_of_speech]["term"])
                    ):
                        # Updates term with original term
                        # since this is a referral via alt spelling.
                        new_etym[part_of_speech]["term"] = original_term

                    break

            if new_etym is not None:
                clean_data[0][new_etym_header] = new_etym
                was_redirected[index] = True
                break

    """
    Step 4) Cleans up the data and returns the results.
    """
    clean_data = [e for i, e in enumerate(clean_data) if not was_redirected[i]]
    clean_data = [item for item in clean_data if item != {}]
    clean_data[0] = _sort_dict_by_trailing_number(clean_data[0])
    clean_data = _remove_alt_spellings(clean_data)

    if all(clean_data[0][key] is None for key in clean_data[0].keys()):
        # snips off the dummy Entry if it's all blanks.
        clean_data = clean_data[1:]

    return clean_data
