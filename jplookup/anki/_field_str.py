"""
Filename: jplookup.anki._field_str.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines helper functions that handle
             processing text for individual fields in an Anki card.

Version: 1.0
License: MIT
"""

import jaconv
from jplookup._cleanstr.identification import is_kanji, creates_long_vowel
from jplookup._cleanstr.textwork import kana_to_moras


def place_pitch_accent(kana: str, next_kana=None) -> str:
    """
    Parameters:
        sustain_len (int): how many kana
    """
    # Determines the length of the horiz line coming from the pitch marker.
    if next_kana is None:
        extra_sustain = len(kana) - 1
    else:
        extra_sustain = (
            len(kana) if creates_long_vowel(kana, next_kana) else len(kana) - 1
        )

    nums = ["", "-one", "-two"]
    num_str = nums[extra_sustain]
    return (
        '<span class="pitch-container">'
        f'<span class="pitch-mark{num_str}">•</span>'
        f"{kana[0]}</span>{kana[1:]}"
    )


def _add_ruby_tags(japanese: str) -> str:
    """
    Returns the given Wiktionary example sentence to
    be formatted for use with HTML by using ruby tags.
    """
    result = ""
    prev_kanji_indices = []  # prev that are in a row.
    furi_buffer = ""
    in_furi = False
    for i, c in enumerate(japanese):
        if c == "(":
            in_furi = True
        elif c == ")":
            in_furi = False

            # Processes any series of kanji gathered.
            if len(prev_kanji_indices) > 0 and len(furi_buffer) > 0:
                # Drops the series of kanji into the results.
                result += "<ruby>"
                for index in prev_kanji_indices:
                    result += japanese[index]
                result += (
                    '<rt><span class="normal-rt">' + furi_buffer + "</span></rt></ruby>"
                )

            prev_kanji_indices = []
            furi_buffer = ""
        elif in_furi:
            furi_buffer += c
        elif is_kanji(c):
            if len(prev_kanji_indices) > 0 and prev_kanji_indices[-1] != i - 1:
                # Drops the series of kanji into the results.
                for index in prev_kanji_indices:
                    result += japanese[index]
                prev_kanji_indices = []
            prev_kanji_indices.append(i)
        else:
            result += c
            prev_kanji_indices = []

    return result

    result = ""
    prev_kanji_i = None
    prev_kanji_indices = []
    in_furi = False
    for i, c in enumerate(japanese):
        if c == "(":
            in_furi = True
            prev_kanji_i = i - 1
        elif c == ")":
            in_furi = False
            if prev_kanji_i is not None:
                kanji = japanese[prev_kanji_i]
                furi = japanese[prev_kanji_i + 2 : i]
                result += f"<ruby>{kanji}<rt>{furi}</rt></ruby>"
        elif not in_furi and (
            (i < len(japanese) - 1 and japanese[i + 1] != "(") or i == len(japanese) - 1
        ):
            result += c

    return result


def create_definition_str(card_parts: list, include_romanji: bool = False) -> str:
    """
    Returns a string with HTML that nicely displays
    the word's various definitions across different
    parts of speech.
    """
    TAB = ""
    NEWLINE = ""
    result_str = ""
    for word_type, part_data in card_parts["parts-of-speech"].items():
        result_str += f'<div class="part-of-speech">{word_type}</div>{NEWLINE}'
        result_str += f'<ul class="word-definitions">{NEWLINE}'
        for definition in part_data["definitions"]:
            def_str = definition["definition"]
            result_str += (
                f'{TAB}<li class="definition-entry">{NEWLINE}'
                f"{TAB}{TAB}{def_str}{NEWLINE}"
            )

            examples = definition.get("examples")
            if examples:
                for example in examples:
                    result_str += f'{TAB}{TAB}<ul class="example-sentence">{NEWLINE}'
                    japanese = _add_ruby_tags(example["japanese"])
                    romanji = example["romanji"]
                    english = example["english"]

                    # Adds each sentence.
                    result_str += (
                        f'{TAB}{TAB}{TAB}<li class="japanese-example">'
                        f"{japanese}</li>{NEWLINE}"
                    )

                    if include_romanji:
                        result_str += (
                            f'{TAB}{TAB}{TAB}<li class="romanji-example">'
                            f"{romanji}</li>{NEWLINE}"
                        )

                    result_str += (
                        f'{TAB}{TAB}{TAB}<li class="english-example">'
                        f"{english}</li>{NEWLINE}"
                    )
                    result_str += f"{TAB}{TAB}</ul>{NEWLINE}"

            result_str += f"{TAB}</li>{NEWLINE}"
        result_str += f"</ul>{NEWLINE}"

    return result_str


def create_pretty_kana(kana: str, pitch_accent: int) -> str:
    """
    Returns a string with HTML that nicely displays
    the kana with additional phonetic information displayed.
    """
    result = ""
    moras = kana_to_moras(kana)
    for i, mora in enumerate(moras):
        if i + 1 == pitch_accent:
            next_kana = None if i == len(moras) - 1 else moras[i + 1][0]
            result += place_pitch_accent(mora, next_kana)
        else:
            result += mora

    return result
