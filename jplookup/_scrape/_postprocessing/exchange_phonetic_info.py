"""
Filename: jplookup._scrape._postprocessing.exchange_phonetic_info.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines a function that collects every pronunciation
             in <results> and has them compared against each other
             in order to fill in missing phonetic information, with
             matches being made by their kana transcriptions.

Version: 1.0
License: MIT
"""

import jaconv
from jplookup._cleanstr.identification import kata_matches


def exchange_phonetic_info(results):
    """
    Shares pronunciation information with those of matching kana
    that lack pitch-accent or IPA.
    """
    # Gets all the pronunciation dict objects and kata conversions.
    all_pronunciations = []
    all_kata = []
    all_refs = []
    for i in range(len(results)):
        for etym_name, parts in results[i].items():
            for part_of_speech, part_data in parts.items():
                pronunciations = part_data.get("pronunciations")
                if pronunciations is not None:  # TODO: pretty sure this is unneeded.
                    for j, p in enumerate(pronunciations):
                        if p.get("kana"):
                            all_pronunciations.append(p)
                            all_kata.append(jaconv.hira2kata(p["kana"]))
                            all_refs.append((i, etym_name, part_of_speech, j))

    if len(all_pronunciations) <= 1:
        return results

    # Shares information among one another.
    KEYS = ["kana", "furigana", "region", "pitch-accent", "ipa"]
    needs_updates = [True for _ in all_pronunciations]
    changed_indices = []
    for index, receiver_p in enumerate(all_pronunciations[::-1]):
        i = len(all_pronunciations) - index - 1
        if not needs_updates[i]:
            continue

        for j, giver_p in enumerate(all_pronunciations):
            if i == j or receiver_p.get("pitch-accent") not in [
                None,
                giver_p.get("pitch-accent"),
            ]:
                continue

            if kata_matches(all_kata[i], all_kata[j]):
                has_everything = True
                was_changed = False
                for key in KEYS[2:]:
                    if giver_p.get(key):
                        if receiver_p.get(key) is None:
                            receiver_p[key] = giver_p[key]
                            was_changed = True
                    else:
                        has_everything = False
                if has_everything:
                    needs_updates[j] = False
                if was_changed:
                    changed_indices.append(i)

    # Reorders dictionary key order to be consistent.
    for i in changed_indices:
        entry_i, etym, part, p_i = all_refs[i]
        p = results[entry_i][etym][part]["pronunciations"][p_i]
        results[entry_i][etym][part]["pronunciations"][p_i] = {
            key: p[key] for key in KEYS if p.get(key) is not None
        }
    return results
