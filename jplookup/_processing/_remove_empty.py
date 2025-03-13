"""
Filename: jplookup._processing._remove_empty.py
Author: TravisGK
Date: 2025-03-13

Description: This file defines a function that will remove
             all empty Parts of Speech, then will remove
             all empty Etymologies, and then optionally will remove
             all empty Entries from the given list of Wiktionary Entries.

Version: 1.0
License: MIT
"""

import copy


def remove_empty_entries(
    clean_data: list,
    remove_entries: bool = False,
):
    indices_to_delete = []
    for i, entry in enumerate(clean_data):
        to_delete = []

        # Clears out empty definitions.
        for etym_name, parts in entry.items():
            if parts is None:
                continue

            for part_of_speech, part_data in parts.items():
                if part_of_speech == "alternative-spellings":
                    continue

                defs = part_data.get("definitions")
                if defs is None or len(defs) == 0:
                    to_delete.append((etym_name, part_of_speech))

        for etym_name, part_of_speech in to_delete:
            # Ensures the key exists before deleting.
            if (
                part_of_speech != "alternative-spellings"
                and etym_name in entry
                and part_of_speech in entry[etym_name]
            ):
                del entry[etym_name][part_of_speech]

        # Clears out empty etymologies.
        to_delete = []
        for etym_name, parts in entry.items():
            if parts is None:
                continue
            elif parts.get("alternative-spellings") is None:
                if len(parts) == 0:
                    to_delete.append(etym_name)
            elif len(parts) == 1:
                to_delete.append(etym_name)

        # Deletes each, ensuring the key exists before deleting.
        for etym_name in to_delete:
            if etym_name in entry:
                del entry[etym_name]

        # If the entry has no keys left, mark the index for deletion
        if len(entry.keys()) == 0:
            indices_to_delete.append(i)

    if remove_entries:
        return [w for i, w in enumerate(clean_data) if i not in indices_to_delete]
    return clean_data
