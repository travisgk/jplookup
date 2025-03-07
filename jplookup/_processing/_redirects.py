import re
from jplookup._cleanstr._textwork import is_japanese_char, remove_alternative_spellings


def _sort_dict_by_trailing_number(data):
    """Sorts a dictionary by the number at the end of each key and returns a new normal dictionary."""

    def extract_number(key):
        match = re.search(r"(\d+)$", key)  # Find the trailing number
        return (
            int(match.group(1)) if match else float("inf")
        )  # Default to infinity if no number

    sorted_items = sorted(data.items(), key=lambda item: extract_number(item[0]))
    result = dict(sorted_items)  # Convert back to a normal dictionary
    return result


def link_up_redirects(clean_data: list, redirects: dict, original_term: str) -> list:
    MAX_NUM_ETYMS = 9
    redirect_keys = redirects.keys()

    if len(clean_data) == 0:
        return None

    if len(clean_data) == 1 or redirects is None or len(redirects.keys()) == 0:
        return clean_data

    # For any redirects, any definitions with specified kanji
    # that DO NOT match the original term are removed;
    # those without kanji or with matching kanji remain.
    for entry in clean_data[1:]:
        for etym in entry.values():
            for part_of_speech, contents in etym.items():
                if part_of_speech in ["alternative-spellings", "usage-notes"]:
                    continue

                defs = contents.get("definitions")
                if defs is None:
                    continue

                def_indices_to_remove = []
                for i, definition in enumerate(defs):
                    def_str = definition["definition"]
                    if is_japanese_char(def_str[0]):
                        # there are kanji specifiers for this definition;
                        # the program ensures only relevant definitions
                        # of child entries are included.
                        colon_index = def_str.find(":")
                        kanji_terms = def_str[:colon_index].split(",")
                        kanji_terms = [k.strip() for k in kanji_terms]
                        if original_term not in kanji_terms:
                            def_indices_to_remove.append(i)

                if len(def_indices_to_remove) > 0:
                    contents["definitions"] = [
                        d for i, d in enumerate(defs) if i not in def_indices_to_remove
                    ]

    successfully_redirected = [False for _ in clean_data]

    # goes through each wiki entry scraped in the given clean data
    # that comes after the root entry.
    for i, entry in enumerate(clean_data[1:]):
        index = i + 1

        # goes through each contained etymology header.
        for etym_key, etymology in entry.items():
            new_etym_header = None
            new_etym = None
            alt_spellings = etymology.get("alternative-spellings")
            if alt_spellings is None:
                continue

            # goes through each part-of-speech contents.
            for part_of_speech, word_data in etymology.items():
                if part_of_speech == "alternative-spellings":
                    continue  # can prob move removal of alt spellings to prior to call and then i can do away with this if statement

                term = word_data.get("term")
                if term in redirect_keys and (
                    len(entry) == 1 or (original_term in alt_spellings)
                ):
                    new_etym_header = redirects[term]
                    new_etym = etymology
                    break

            if new_etym is not None:
                clean_data[0][new_etym_header] = new_etym
                successfully_redirected[index] = True
                break

    clean_data = [e for i, e in enumerate(clean_data) if not successfully_redirected[i]]
    clean_data[0] = _sort_dict_by_trailing_number(clean_data[0])

    return clean_data
