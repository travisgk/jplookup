"""
Filename: jplookup._scrape._postprocessing.clean_keys.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines the helper function that renames
             the Part of Speech keys to be ordered.

Version: 1.0
License: MIT
"""


def clean_keys(results: list) -> list:
    for i, r in enumerate(results):
        for j, etym_name_and_data in enumerate(r.items()):
            etym_name, etym_data = etym_name_and_data
            part_counts = {}
            part_strings = []
            for part_of_speech, word_info in etym_data.items():
                space_index = part_of_speech.rfind(" ")
                if space_index >= 0:
                    part_str = part_of_speech[:space_index]
                else:
                    part_str = part_of_speech
                part_strings.append(part_str)

                if part_counts.get(part_str):
                    part_counts[part_str] += 1
                else:
                    part_counts[part_str] = 1

            new_etym = {}
            part_occurrences = {}
            for k, part_and_info in enumerate(etym_data.items()):
                part_str = part_strings[k]
                part_of_speech, word_info = part_and_info
                if part_counts[part_str] == 1:
                    new_title = part_str
                else:
                    if part_occurrences.get(part_str):
                        part_occurrences[part_str] += 1
                        new_title = part_str + f" {part_occurrences[part_str]}"
                    else:
                        part_occurrences[part_str] = 1
                        new_title = part_str + " 1"
                new_etym[new_title] = word_info
            results[i][etym_name] = new_etym

    return results
