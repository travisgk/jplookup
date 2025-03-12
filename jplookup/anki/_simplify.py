_TAG_PRIORITIES = [
    (
        "ipa",
        "pitch-accent",
        "kana",
    ),
    (
        "pitch-accent",
        "kana",
    ),
    (
        "ipa",
        "kana",
    ),
    ("kana",),
]


def search_for_pronunciation(pronunciations: list, tag_priority_i: int = 0):
    """
    Returns the first pronunciation dictionary with all the tags
    specified in <_TAG_PRIORITIES[tag_priority_i]>.

    If no pronunciation was found, and there's a further tuple to
    check again in <_TAG_PRIORITIES>, then this function
    runs recursively for that next tuple.
    """
    keys = _TAG_PRIORITIES[tag_priority_i]
    for p in pronunciations:
        if all(p.get(k) is not None for k in keys):
            return p

    if tag_priority_i < len(_TAG_PRIORITIES) - 1:
        return search_for_pronunciation(pronunciations, tag_priority_i + 1)

    return None


def _join_word_data(word_dicts: list) -> dict:
    """
    Returns a dictionary composed out of
    all the contents of each <word_dict>.
    """
    result = {
        "term": word_dicts[0][1]["term"],
        "pronunciation": word_dicts[0][1]["pronunciation"],
    }

    # Adds the Definitions of every dictionary.
    definitions = []
    for part_of_speech, part_data in word_dicts:
        definitions.extend(part_data["definitions"])
    result["definitions"] = definitions

    # Adds the Usage Notes of every dictionary.
    usage_notes_str = ""
    for part_of_speech, part_data in word_dicts:
        usage_notes = part_data.get("usage-notes")
        if usage_notes:
            if len(usage_notes_str) > 0:
                usage_notes_str += "\n"
            usage_notes_str += usage_notes

    if len(usage_notes_str) > 0:
        result["usage-notes"] = usage_notes_str

    return result


def combine_like_terms(card_parts: list) -> list:
    """
    Returns the list of Part-of-Speech with all
    Parts-of-Speech of matching term, kana
    and word type combined into one.
    """
    unique_part_names = list(set([part for part, _ in card_parts]))

    # Sorts parts into groups by the unique parts names.
    sorted_parts = []
    for unique_part_name in unique_part_names:
        sorted_parts.append([])
        for part_of_speech, part_data in card_parts:
            if part_of_speech == unique_part_name:
                if (
                    len(sorted_parts[-1]) == 0
                    or sorted_parts[-1][-1][1]["term"] == part_data["term"]
                ):
                    sorted_parts[-1].append((part_of_speech, part_data))

    # Each list of sorted parts is collapsed into a single dictionary.
    result_parts = {
        part_name: _join_word_data(parts)
        for part_name, parts in zip(
            unique_part_names,
            sorted_parts,
        )
    }

    # Removes the individualized attributes since
    # they're all the same; they're going to be moved
    # to a more global scope in the <result>.
    kanji = result_parts[unique_part_names[0]]["term"]
    pronunciation = result_parts[unique_part_names[0]]["pronunciation"]
    for unique_part_name in unique_part_names:
        del result_parts[unique_part_name]["term"]
        del result_parts[unique_part_name]["pronunciation"]

    result = {}
    for key, value in pronunciation.items():
        if key != "furigana":
            result[key] = value

    if kanji != pronunciation.get("kana"):
        result["kanji"] = kanji
        if pronunciation.get("furigana"):
            result["furigana"] = pronunciation.get("furigana")

    result["parts-of-speech"] = result_parts

    return result
