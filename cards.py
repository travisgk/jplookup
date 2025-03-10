import time
import random
import sys
import json
import jplookup

DESIRED_PARTS = [
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


def find_first_value(data, term):
    """
    Recursively searches through a nested structure (dictionaries and lists)
    and returns the first non-None value for the specified key (term).

    Parameters:
        data (dict or list): The nested data structure to search.
        term (str): The key to look for in dictionaries.

    Returns:
        The first non-None value found for the given key, or None if not found.
    """
    # If data is a dictionary, check the current level first.
    if isinstance(data, dict):
        # Check if the key exists and its value is not None.
        value = data.get(term)
        if value is not None:
            return value

        # Otherwise, iterate over each value in the dictionary.
        for key in data:
            result = find_first_value(data[key], term)
            if result is not None:
                return result

    # If data is a list, iterate over its items.
    elif isinstance(data, list):
        for item in data:
            result = find_first_value(item, term)
            if result is not None:
                return result

    # Return None if the key is not found at this level.
    return None


def main():
    TAG_PRIORITIES = [("ipa", "pitch-accent"), ("pitch-accent"), ("ipa",)]

    # loads the .json with the written jplookup info.
    with open("jp-data.json", "r", encoding="utf-8") as f:
        word_info = json.load(f)

    def search_for_pronunciation(pronunciations: list, tag_priority_i: int = 0):
        keys = TAG_PRIORITIES[tag_priority_i]
        for p in pronunciations:
            if all(p.get(k) is not None for k in keys):
                return p

        if tag_priority_i < len(TAG_PRIORITIES) - 2:
            return search_for_pronunciation(pronunciations, tag_priority_i + 1)

        return None

    cards = {}
    for search_term, entries in word_info.items():
        kana_bank = {}
        for etym_term, etym_data in entries[0].items():
            for part_of_speech, word_data in etym_data.items():
                term = word_data["term"]
                pronunciations = word_data["pronunciations"]

                pronunciation = search_for_pronunciation(pronunciations)
                if pronunciation is not None:
                    kana = pronunciation["kana"]
                    if kana_bank.get(kana):
                        kana_bank[kana].append((part_of_speech, word_data))
                    else:
                        kana_bank[kana] = [
                            (part_of_speech, word_data),
                        ]

        if len(kana_bank) > 0:
            best_key = list(kana_bank.keys())[0]
            if len(kana_bank) > 1:
                best_count = 0
                for key, parts_list in kana_bank.items():
                    if len(parts_list) > best_count:
                        best_key = key
                        best_count = len(parts_list)

            print("\n\n\n")
            print(kana_bank[best_key])

    '''

    # goes through each term in the .json.
    for key in word_info.keys():
        """

        Step 1)
        """
        # looks for the desired word entry.
        data = word_info.get(key)
        if data is None or len(data) == 0:
            continue  # skips if term is not in dict.

        # looks for the first etymology header.
        for i in range(1, 10):
            etym = data[0].get(f"Etymology {i}")
            if etym is not None:
                data = etym
                break
        else:
            continue

        word_infos[key] = data

    """

    Step 2) Collects the parts of speech and pronunciation.
    """
    for key in word_info.keys():
        data = word_infos[key]

        def search_for_pronunciation(pronunciations: list, keys: list):
            for p in pronunciations:
                if all(p.get(k) is not None for k in keys):
                    return p
            return None

        parts = {}
        first_term = None
        pronunciation = None
        
        for part_of_speech, part_data in data.items():
            # gets the first term found in the first part of speech.
            term = find_first_value(part_data, "term")
            if first_term is None:
                first_term = term  # the first term is used to match up.
                parts[part_of_speech] = part_data  # adds the part of speech.
            elif term == first_term:
                # adds the part of speech that matches with the first term found.
                parts[part_of_speech] = part_data

            # looks for the first pronunciation with sufficient data.
            if pronunciation is None:
                pronunces = part_data.get("pronunciations")
                if pronunces is not None:
                    p = search_for_pronunciation(pronunces, ["ipa", "pitch-accent"])
                    if p is None:
                        p = search_for_pronunciation(pronunces, ["pitch-accent"])
                        if p is None:
                            p = search_for_pronunciation(pronunces, ["ipa"])
                            if p is None:
                                p = pronunces[0]
                    pronunciation = p

        """

        Step 3) Constructs an Anki card from the desired parts of speech.
        """
        card = {"term": first_term, "pronunciation": pronunciation}
        for part_of_speech, part_data in parts.items():
            speech_title = part_of_speech.split(" ")[0]
            if speech_title not in DESIRED_PARTS:
                continue  # only grabs the desired parts of speech.

            # seeks out the term text.
            term = find_first_value(part_data, "term")

            # print(f"{key}\t{term}\t{speech_title}")
            def_str = ""
            for definition in part_data["definitions"]:
                def_str += definition["definition"] + "\n"

                """
                examples = definition.get("examples")
                if examples is not None:
                    for example in examples:
                        jp = example["japanese"]
                        roma = example["romanji"]
                        en = example["english"]
                        def_str += f"\t{jp}\n"
                        def_str += f"\t{roma}\n"
                        def_str += f"\t{en}\n"
                """

            print(def_str)

        # print(card)
        print("\n\n")
        # print(part_of_speech)
        # print(part_data)
    '''


if __name__ == "__main__":
    main()
