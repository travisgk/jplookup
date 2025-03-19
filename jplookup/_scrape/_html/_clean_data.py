"""
Filename: jplookup._scrape._html._clean_data.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines a function that takes the outputs
             from extract_data(...) seen in .extract.py and extrapolates
             it into a more useful format while also
             cleaning up residual data.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.identification import (
    percent_japanese,
    find_pronunciation_match,
)
from jplookup._cleanstr.removal import remove_spaces_jp
from jplookup._cleanstr.textwork import (
    extract_japanese,
    extract_pronunciation_info,
    change_furi_to_kata,
)
from ._headwords import *

# if True, furigana will be changed to kata
# if that's standard.
ENFORCE_KATAKANA_FURI = True


def clean_data(word_info: list, term: str) -> dict:
    """Returns a dict object with all the given extracted data cleaned up."""
    result = {}

    # Cycles through all the Etymology keys.
    for etym_key, entry in word_info.items():
        """

        Step 1) Creates a new dictionary for this etymology title.
        """
        etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        result[etym_title] = {}
        entry = word_info[etym_key]

        alt_spellings = entry.get("alternative-spellings")
        if alt_spellings is not None:
            result[etym_title]["alternative-spellings"] = alt_spellings

        """
        Step 2) Cycles through the pronunciations
                under this Etymology header, storing each
                pronunciation in a dictionary (bank) to
                later be matched up to the Parts of Speech
                by their kana.
        """
        pronunciation_bank = {}
        for pronunciation in entry["pronunciations"]:
            region, kana, pitch_accent, ipa = extract_pronunciation_info(pronunciation)

            # Adds a new pronunciation entry to the pronunciation bank.
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

        """
        Step 3) Cycles through the Parts of Speech under this Etymology header.
        """

        # Sorts parts of speech by their appearance
        # on the page from top-to-bottom.
        parts_of_speech = entry["parts-of-speech"]
        parts_of_speech = sorted(parts_of_speech, key=lambda x: x[1])
        parts_of_speech = [s[0] for s in parts_of_speech]

        parts_to_remove = []
        for i, part in enumerate(parts_of_speech):
            if part == "alternative-spellings":
                continue

            """
            Step 3a) Gets the headword string
                     from the list parallel to the parts of speech,
                     looks for a Counter noun, and also breaks up 
                     the headword string into a list of headwords.
            """
            headword_str = entry["headwords"][i]

            counter_index = headword_str.find(" counter:")
            counter = None
            if counter_index >= 0:
                counter = headword_str[counter_index + 9 :]
                headword_str = headword_str[:counter_index]
            headwords = break_up_headwords(headword_str)

            """
            Step 3b) Sets up the dictionary object 
                     for this Etymology + Part of Speech.

                     Gets a singular term and furigana 
                     and kana transcriptions from each headword. 

                     If a verb adds a stem to a word
                     and its transcription is changed because of it,
                     then that transcription will still be added to the
                     output lists but won't change the <term> that's receieved.

                     This shouldn't be an issue, since Wiktionary tends to be
                     written with the top priority definitions closer 
                     to the start of the HTML, and also verb forms of words 
                     commonly exist under their own Etymology header, 
                     meaning that its transcription extraction process 
                     is independent from the noun forms.
            """
            # Gets the kana from the headword.
            # a list with the furigana for each corresponding char
            # is included only if a kanji with furigana is present.
            prefers_katakana = False
            usage_notes = entry["usage-notes"][i]
            if len(usage_notes) > 0:
                prefers_katakana = "often spelled in katakana" in usage_notes

            # Extracts transcriptions.
            term, furigana, kanas = extract_info_from_headwords(
                headwords, prefers_katakana
            )
            transcriptions = [
                (
                    {"kana": k, "furigana": f}
                    if any(len(furi) > 0 for furi in f)
                    else {"kana": k}
                )
                for f, k in zip(furigana, kanas)
            ]

            """
            Step 3c) The transcriptions are matched up 
                     to the pronunciations to give 
                     each transcription additional phonetic information.
            """
            for t in transcriptions:
                matching_pronunciation = find_pronunciation_match(
                    pronunciation_bank,
                    t,
                )
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

            """
            Step 3d) Finally creates the dict object for this etym + part.
            """
            result[etym_title][part] = {"term": term}

            if counter is not None:
                result[etym_title][part]["counter"] = counter

            if len(transcriptions) > 0:
                result[etym_title][part]["pronunciations"] = transcriptions
            result[etym_title][part]["definitions"] = []

            """
            Step 3e) Cycles through the Definitions 
                     under this Parts of Speech header
                     and adds its information, with some
                     Definitions in particular being excluded,
                     then deletes arbitrary data.
            """
            definitions = []
            for definition in entry["definitions"][i]:
                definition["definition"] = definition["definition"].strip()

                """
                Step 3e.2) Examines to see if there are any sublines provided.
                """
                def_text = definition["definition"]
                sublines = definition.get("sublines")
                dd_index = def_text.find("<dd>")
                if sublines is None:
                    # There may be sublines specified in <dd> tags.
                    if dd_index >= 0:
                        # The definition text contains <dd> tags to break up.
                        sublines = extract_tag_contents(def_text, tag="dd")
                        if len(sublines) == 0:
                            sublines = None
                            definitions.append(definition)
                        else:
                            def_text = def_text[:dd_index].strip()
                    else:
                        # This definition has no sublist so it can just be added.
                        definitions.append(definition)

                if sublines is not None:
                    # Strips the newline nonsense.
                    sublines = [s.strip() for s in sublines]

                    # The found sublist will be included
                    # along with its above definition text.
                    if dd_index >= 0:
                        def_text = def_text[:dd_index].strip()

                    new_def = {"definition": def_text}
                    percent_jp = [percent_japanese(s) for s in sublines]

                    # Cycles through the Sublines under this Definition entry.
                    j = 0
                    while j < len(sublines):
                        sub = sublines[j]

                        # Handles synonyms and antonyms.
                        handled = False
                        if sub.startswith("Synonym"):
                            sub = sub[7:]
                            new_def["synonyms"] = extract_japanese(sub)
                            handled = True

                        elif sub.startswith("Antonym"):
                            sub = sub[7:]
                            new_def["antonyms"] = extract_japanese(sub)
                            handled = True

                        # Some examples are given on one line.
                        elif "―" in sub:
                            sub_strs = sub.split("―")
                            if (
                                len(sub_strs) == 3
                                and percent_japanese(sub_strs[0]) > 0.5
                                and all(percent_japanese(s) < 0.5 for s in sub_strs[1:])
                            ):
                                english = sub_strs[2].strip()
                                DUMMY_PHRASE = "(please add an English translation"
                                if not english.startswith(DUMMY_PHRASE):
                                    sentence = {
                                        "japanese": remove_spaces_jp(
                                            sub_strs[0].strip()
                                        ),
                                        "romanji": sub_strs[1].strip(),
                                        "english": english,
                                    }
                                    if prefers_katakana and ENFORCE_KATAKANA_FURI:
                                        sentence["japanese"] = change_furi_to_kata(
                                            sentence["japanese"],
                                            term=term,
                                        )

                                    # adds the inline example.
                                    if new_def.get("examples") is None:
                                        new_def["examples"] = [
                                            sentence,
                                        ]
                                    else:
                                        new_def["examples"].append(sentence)
                                handled = True

                        if handled:
                            j += 1
                            continue

                        # Handles multi-line sentence examples.
                        if (
                            j + 2 < len(sublines)
                            and percent_jp[j] > 0.5
                            and not sub.startswith("<dd>")
                            and all(
                                percent_jp[j + k] < 0.5
                                and sublines[j + k].startswith("<dd>")
                                and sublines[j + k].endswith("</dd>")
                                for k in [1, 2]
                            )
                        ):
                            # If the program finds a series of sublines
                            # where it goes JP, <dd>EN</dd>, <dd>EN</dd>,
                            # then this is assumed
                            # to be an example sentence.
                            english = sublines[j + 2][4:-5]
                            DUMMY_PHRASE = "(please add an English translation"
                            if not english.startswith(DUMMY_PHRASE):
                                sentence = {
                                    "japanese": remove_spaces_jp(sublines[j]),
                                    "romanji": sublines[j + 1][4:-5],
                                    "english": english,
                                }
                                if prefers_katakana:
                                    sentence["japanese"] = change_furi_to_kata(
                                        sentence["japanese"],
                                        term=term,
                                    )

                                if new_def.get("examples") is None:
                                    new_def["examples"] = [
                                        sentence,
                                    ]
                                else:
                                    new_def["examples"].append(sentence)

                            j += 3  # skips ahead of the example lines.
                            continue

                        j += 1

                    # The updated definition is added.
                    definitions.append(new_def)

            if len(definitions) > 0:
                result[etym_title][part]["definitions"] = definitions
                if len(usage_notes) > 0:
                    result[etym_title][part]["usage-notes"] = usage_notes.strip()
            else:
                # Deletes a Part of Speech entry
                # if it no longer has any definitions.
                parts_to_remove.append((etym_title, part))

        # Deletes the Parts of Speech with no Definitions left.
        for etym_title, part in parts_to_remove:
            del result[etym_title][part]

    """
    Step 4) Deletes any Etymology entries 
            that don't have any Parts of Speech anymore.
    """
    for etym_key in word_info.keys():
        etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        parts = [k for k in result[etym_title].keys() if k != "alternative-spellings"]
        if all(len(result[etym_title][part].keys()) == 0 for part in parts):
            del result[etym_title]

    return result
