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
    # loads the .json with the written jplookup info.
    with open("jp-data.json", "r", encoding="utf-8") as f:
        word_info = json.load(f)

    # goes through each term in the .json.
    for key in word_info.keys():
        # print(key)

        # looks for the term.
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

        parts = {}
        first_term = None
        pronunciation = None
        for part_of_speech, part_data in data.items():
            pronunciations = part_data.get("pronunciations")
            if pronunciation is None:
                for p in pronunciations:
                    if p.get("ipa") and p.get("pitch-accent"):
                        pronunciation = p
                        break
            if pronunciation is None:
                for p in pronunciations:
                    if p.get("pitch-accent"):
                        pronunciation = p
                        break
            if pronunciation is None:
                for p in pronunciations:
                    if p.get("ipa"):
                        pronunciation = p
                        break
            if pronunciation is None:
                pronunciation = pronunciations[0]

            term = find_first_value(part_data, "term")
            if first_term is None:
                first_term = term
                parts[part_of_speech] = part_data
            elif term == first_term:
                parts[part_of_speech] = part_data

        for part_of_speech, part_data in parts.items():
            speech_title = part_of_speech.split(" ")[0]
            if speech_title not in DESIRED_PARTS:
                continue

            term = find_first_value(part_data, "term")
            print(f"{key}\t{term}\t{speech_title}")

            for definition in part_data["definitions"]:
                print(definition["definition"])
                examples = definition.get("examples")
                if examples is not None:
                    for example in examples:
                        print(f"\t{example}")

        print(pronunciation)

        print("\n\n")
        # print(part_of_speech)
        # print(part_data)


if __name__ == "__main__":
    main()
