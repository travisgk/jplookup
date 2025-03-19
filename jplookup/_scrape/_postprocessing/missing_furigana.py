"""
Filename: jplookup._scrape._postprocessing.missing_furigana.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines a function which will 
             look through the given list to find
             any Pronunciations for terms with kanji that
             lack proper furigana representation, and
             then try to place the kana transcription
             appropriately to create a list of furigana.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.identification import is_kanji, is_kana
from jplookup._cleanstr.textwork import kana_to_moras


def fill_in_missing_furigana(results: list):
    KEYS = [
        "kana",
        "furigana",
        "furigana-by-index",
        "region",
        "pitch-accent",
        "ipa",
    ]
    for r in results:
        for etym_name, etym_data in r.items():
            for part_of_speech, word_data in etym_data.items():
                term = word_data["term"]
                if all(not is_kanji(c) for c in term):
                    continue

                pronunciations = word_data.get("pronunciations")
                if pronunciations and any(is_kanji(c) for c in term):
                    for p_index, p in enumerate(pronunciations):
                        kana = p.get("kana")
                        furi = p.get("furigana")
                        if kana is not None and (
                            furi is None
                            or any(
                                (len(furi[i]) == 0 and is_kanji(c))
                                for i, c in enumerate(term)
                            )
                        ):
                            new_furi = ["" for _ in range(len(term))]
                            temp_term = term
                            temp_kana = kana

                            # Clips identical characters from kanji/kana.
                            start_index = 0
                            cutoff = 0
                            while (
                                len(temp_term) > 0
                                and len(temp_kana) > 0
                                and temp_term[0] == temp_kana[0]
                            ):
                                # Chomps left.
                                temp_term = temp_term[1:]
                                temp_kana = temp_kana[1:]
                                start_index += 1

                            while (
                                len(temp_term) > 0
                                and len(temp_kana) > 0
                                and temp_term[-1] == temp_kana[-1]
                            ):
                                # Chomps right.
                                temp_term = temp_term[:-1]
                                temp_kana = temp_kana[:-1]
                                cutoff += 1

                            # Checks if the num of moras
                            # in kana and term are the same.
                            moras = kana_to_moras(temp_kana)
                            series = kana_to_moras(temp_term)
                            if len(series) > 0 and len(series) == len(moras):
                                index = 0
                                for i in range(len(series)):
                                    s = series[i]
                                    if len(s) == 1 and is_kanji(s):
                                        new_furi[start_index + index] = moras[i]
                                        index += len(s)
                                p["furigana"] = new_furi

                            # Checks if there's only one kanji to transcribe.
                            elif (
                                len(series) == 1
                                and len(series[0]) == 1
                                and len(moras) > 1
                            ):
                                p["furigana"] = (
                                    ["" for _ in range(start_index)]
                                    + moras
                                    + ["" for _ in range(cutoff)]
                                )

                            else:
                                # Otherwise, the remaining kana are added
                                # as a special form of furigana where
                                # the start index in the term is given,
                                # as well as for how many chars
                                # the furigana will span.
                                furi_with_loc = []
                                furi_with_loc.append(
                                    (start_index, len(temp_term), "".join(moras))
                                )

                                p["furigana-by-index"] = furi_with_loc
                                if p.get("furigana"):
                                    del p["furigana"]

                            pronunciations[p_index] = {
                                key: p[key] for key in KEYS if p.get(key)
                            }  # updates key order.

    return results
