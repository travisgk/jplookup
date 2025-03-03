from jplookup._cleanstr._textwork import (
    is_kana,
    is_japanese_char,
    percent_japanese,
    separate_term_and_furigana,
)


def _break_up_headwords(headword_str: str) -> list:
    """Returns a list of headwords (kanji and furigana in parentheses)."""
    or_index = headword_str.find("or")
    if or_index >= 0:
        return [headword_str[:or_index], headword_str[or_index + 2 :]]
    return [
        headword_str,
    ]


def _extract_info_from_headwords(headwords: list):
    """
    Returns the Japanese term,
    a list of furigana
    and a list of hiragana transcriptions.
    """
    results = [separate_term_and_furigana(h) for h in headwords]

    # gets the defining term for each headword.
    terms = [r[0] for r in results]
    if len(terms) == 0:
        return None

    # gets a list of furigana for each kanji.
    furis = []
    for r in results:
        local_furi = r[1]
        local_furi = ["".join(f) for f in local_furi]
        furis.append(local_furi)

    # gets the kana transcription for each headword.
    kanas = []
    for term, furi in zip(terms, furis):
        kana = ""
        for c, f in zip(term, furi):
            kana += c if is_kana(c) else f

        kanas.append(kana)

    if any(t != terms[0] for t in terms):
        print(f"The terms are different: {terms}")  # mere warning.

    return terms[0], furis, kanas


def _extract_japanese(subline: str) -> list:
    """
    Returns a list of every individual japanese phrase
    contained in the given text.
    """
    in_jp = False
    terms = [
        "",
    ]
    for i, c in enumerate(subline):
        if is_japanese_char(c):
            terms[-1] += c
            in_jp = True

        elif in_jp:  # not a jp char
            terms.append("")
            in_jp = False

    terms = [t for t in terms if len(t) > 0]
    return terms


def clean_data(word_info: list, term: str):
    result = {}

    # Cycles through all the Etymology keys.
    etym_keys = word_info.keys()
    for etym_key in etym_keys:
        entry = word_info[etym_key]

        # creates a new dictionary for this etymology title.
        etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        result[etym_title] = {}

        # Cycles through the Parts of Speech under this Etymology header.
        parts_of_speech = entry["parts-of-speech"]
        for i, part in enumerate(parts_of_speech):
            # Sets up the data entry for this particular Part of Speech.
            headwords = _break_up_headwords(entry["headwords"][i])
            term, furigana, kanas = _extract_info_from_headwords(headwords)
            result[etym_title][part] = {
                "term": term,
                "transcriptions": [
                    {"kana": k, "furigana": f} for f, k in zip(furigana, kanas)
                ],
                "definitions": [],
            }

            # Cycles through the pronunciations
            # under this Parts of Speech header.
            for pronunciation in entry["pronunciations"]:
                print(pronunciation)  # DEBUG

            # Cycles through the Definitions under this Parts of Speech header.
            definitions = []
            for definition in entry["definitions"][i]:
                sublines = definition.get("sublines")
                if sublines is None:
                    definitions.append(definition)
                else:
                    new_def = {"definition": definition["definition"]}
                    percent_jp = [percent_japanese(s) for s in sublines]

                    # Cycles through the Sublines under this Definition entry.
                    j = 0
                    while j < len(sublines):
                        sub = sublines[j]

                        # Handles synonyms and antonyms.
                        if sub.startswith("Synonym"):
                            sub = sub[7:]
                            new_def["synonyms"] = _extract_japanese(sub)

                        elif sub.startswith("Antonym"):
                            sub = sub[7:]
                            new_def["antonyms"] = _extract_japanese(sub)

                        # Handles sentence examples.
                        elif j + 2 < len(sublines):
                            if percent_jp[j] > 0.5 and all(
                                percent_jp[j + k] < 0.5
                                and sublines[j + k].startswith("<dd>")
                                and sublines[j + k].endswith("</dd>")
                                for k in [1, 2]
                            ):
                                #
                                if new_def.get("examples") is None:
                                    new_def["examples"] = []

                                sentence = {
                                    "japanase": sublines[j],
                                    "romanji": sublines[j + 1][4:-5],
                                    "english": sublines[j + 2][4:-5],
                                }

                                new_def["examples"].append(sentence)

                                j += 3  # skips ahead of the example lines.
                                continue

                        j += 1
                    definitions.append(new_def)
            result[etym_title][part]["definitions"] = definitions

    return result
