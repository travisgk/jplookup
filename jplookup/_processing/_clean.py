from jplookup._cleanstr._textwork import (
    is_kana,
    is_japanese_char,
    percent_japanese,
    separate_term_and_furigana,
    extract_japanese,
)


def _extract_pronunciation_info(p_str: str):
    """Returns the region, the kana, the pitch-accent and IPA."""
    region, kana, pitch_accent, ipa = None, None, None, None

    # Extracts the region.
    REGIONS = ["Tokyo", "Osaka"]
    for r in REGIONS:
        if p_str.startswith(f"({r})"):
            region = r
            break

    # Extracts the kana.
    found_kana = extract_japanese(p_str)
    if len(found_kana) > 0:
        kana = found_kana[0]

    # Extracts the accent number.
    accent_start_index = p_str.find("– [")
    if accent_start_index >= 0:
        accent_end_index = p_str.find("])", accent_start_index)
        if accent_end_index - accent_start_index == 4:
            pitch_accent = int(p_str[accent_end_index - 1])

    # Extracts the IPA.
    IPA_TERM = "IPA(key):"
    ipa_key_index = p_str.find(IPA_TERM)
    if ipa_key_index >= 0:
        ipa_key_index += len(IPA_TERM)
        ipa_start_index = p_str.find("[", ipa_key_index)
        if ipa_start_index >= 0:
            ipa_end_index = p_str.find("]", ipa_start_index)
            if ipa_end_index >= 0:
                ipa = p_str[ipa_start_index + 1 : ipa_end_index]

    return region, kana, pitch_accent, ipa


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


def clean_data(word_info: list, term: str):
    """Returns a dict object with all the given extracted data cleaned up."""
    result = {}

    # Cycles through all the Etymology keys.
    etym_keys = word_info.keys()
    for etym_key in etym_keys:
        entry = word_info[etym_key]

        # creates a new dictionary for this etymology title.
        etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        result[etym_title] = {}

        # Cycles through the pronunciations
        # under this Etymology header.
        pronunciation_bank = {}
        for pronunciation in entry["pronunciations"]:
            region, kana, pitch_accent, ipa = _extract_pronunciation_info(pronunciation)
            print(pronunciation)  # DEBUG
            print(region)
            print(kana)
            print(pitch_accent)
            print(ipa)

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
                            new_def["synonyms"] = extract_japanese(sub)

                        elif sub.startswith("Antonym"):
                            sub = sub[7:]
                            new_def["antonyms"] = extract_japanese(sub)

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
