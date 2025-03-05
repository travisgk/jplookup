from jplookup._cleanstr._textwork import (
    is_kana,
    is_japanese_char,
    percent_japanese,
    separate_term_and_furigana,
    extract_japanese,
)
from ._pronunciation_match import *


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

        # Creates a new dictionary for this etymology title.
        etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        result[etym_title] = {}

        # Cycles through the pronunciations
        # under this Etymology header.
        # ---
        # Each pronunciation is stored in a bank
        # and will be later matched up to the parts of speech
        # by their kana.
        pronunciation_bank = {}
        for pronunciation in entry["pronunciations"]:
            region, kana, pitch_accent, ipa = _extract_pronunciation_info(pronunciation)

            # adds a new pronunciation entry to the pronunciation bank.
            if (
                kana is not None
                and pronunciation_bank.get(kana) is None
                and any(t is not None for t in [region, pitch_accent, ipa])
            ):
                new_pronunciation = {}
                if region is not None:
                    new_pronunciation["region"] = region
                if pitch_accent is not None:
                    new_pronunciation["pitch-accent"] = pitch_accent
                if ipa is not None:
                    new_pronunciation["ipa"] = ipa
                pronunciation_bank[kana] = new_pronunciation

        # Cycles through the Parts of Speech under this Etymology header.
        parts_of_speech = entry["parts-of-speech"]
        for i, part in enumerate(parts_of_speech):
            # Sets up the data entry for this particular Part of Speech.
            headwords = _break_up_headwords(entry["headwords"][i])

            # Sets up the dictionary object for this Etymology + Part of Speech.
            # ---
            # gets the kana from the headword.
            # a list with the furigana for each corresponding char
            # is included only if a kanji with furigana is present.
            term, furigana, kanas = _extract_info_from_headwords(headwords)
            transcriptions = [
                (
                    {"kana": k, "furigana": f}
                    if any(len(furi) > 0 for furi in f)
                    else {"kana": k}
                )
                for f, k in zip(furigana, kanas)
            ]

            # the transcriptions are matched up to the pronunciations
            # to give each transcription additional phonetic information.
            for t in transcriptions:
                matching_pronunciation = find_pronunciation_match(pronunciation_bank, t)
                if matching_pronunciation is not None:
                    region = matching_pronunciation.get("region")
                    pitch_accent = matching_pronunciation.get("pitch-accent")
                    ipa = matching_pronunciation.get("ipa")
                    if region is not None:
                        t["region"] = region
                    if pitch_accent is not None:
                        t["pitch-accent"] = pitch_accent
                    if ipa is not None:
                        t["ipa"] = ipa

            # finally creates the dictionary object for this etym + part.
            result[etym_title][part] = {"term": term}
            if len(transcriptions) > 0:
                result[etym_title][part]["pronunciations"] = transcriptions
            result[etym_title][part]["definitions"] = []

            # Cycles through the Definitions under this Parts of Speech header.
            definitions = []
            for definition in entry["definitions"][i]:
                sublines = definition.get("sublines")
                if sublines is None:
                    # this definition has no sublist so it can just be added.
                    definitions.append(definition)
                else:
                    # otherwise, the sublist will be included
                    # along with its above definition text.
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
                                # if the program finds a series of sublines
                                # where it goes JP, <dd>EN</dd>, <dd>EN</dd>,
                                # then this is assumed
                                # to be an example sentence.
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
