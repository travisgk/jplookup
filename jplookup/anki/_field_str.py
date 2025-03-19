"""
Filename: jplookup.anki._field_str.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines helper functions that handle
             processing text for individual fields in an Anki card.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.identification import is_kanji
from jplookup._cleanstr.textwork import kana_to_moras

TAB = ""
NEWLINE = ""


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
                result += f"<rt>{furi_buffer}</rt></ruby>"

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
            result += _place_pitch_accent(mora)
        else:
            result += mora

    return result


def _place_pitch_accent(kana) -> str:
    return (
        '<span class="pitch-container">'
        '<span class="pitch-mark">•</span>'
        f"{kana}</span>"
    )


def create_pretty_kanji(
    kanji: str,
    kana: str,
    pitch_accent: int,
    furigana,
    furigana_by_index,  #  list, could be None.
) -> str:
    """
    Returns a string with HTML that nicely displays
    the kanji with additional phonetic information displayed
    and furigana shown.
    """
    if furigana is None and furigana_by_index is None:
        return kanji

    result = ""

    if furigana_by_index is None:
        moras_by_furi = []
        for furi in furigana:
            if len(furi) > 0:
                moras_by_furi.append(kana_to_moras(furi))
            else:
                moras_by_furi.append([])

        mora_num = 1
        for i, c in enumerate(kanji):
            if is_kanji(c):
                furi_moras = moras_by_furi[i]

                furi_str = ""
                if pitch_accent < mora_num + len(furi_moras):
                    # The pitch marker of this word
                    # is in the furigana of this current kanji.
                    # ---
                    # Generates the furigana string with HTML for the marker.
                    for furi_mora in furi_moras:
                        if mora_num == pitch_accent:
                            furi_str += _place_pitch_accent(furi_mora)
                        else:
                            furi_str += f'<span class="normal-rt">{furi_mora}</span>'
                        mora_num += 1

                    result += f"<ruby>{c}<rt>{furi_str}</rt></ruby>"

                else:
                    # Otherwise, this is just a normal furigana.
                    # It gets a particular span element surrounding it
                    # so that all furigana are rendered at the same level.
                    furi_str = "".join([f for f in furi_moras])
                    mora_num += len(furi_moras)
                    result += (
                        f"<ruby>{c}<rt>"
                        + f'<span class="normal-rt">{furi_str}</span>'
                        + "</rt></ruby>"
                    )
            else:  # is kana.
                next_kanji_i = next(
                    (i + j for j, c in enumerate(kanji[i + 1 :]) if is_kanji(c)),
                    -1,
                )

                if next_kanji_i >= 0:
                    next_kana = kanji[i:next_kanji_i]
                else:
                    next_kana = kanji[i:]
                next_moras = kana_to_moras(next_kana)

                for mora in next_moras:
                    if mora_num == pitch_accent:
                        result += _place_pitch_accent(mora)
                    else:
                        result += mora
                    mora_num += 1
        return result

    # Handles furigana by index.
    """if len(furigana_by_index) == 1:
        moras = kana_to_moras(kanji)
        mora_num = 1
        for i in 


        start_index, run, furi = furigana_by_index[0]
        for i in range(start_index):
            result += kanji[i]

        result += "<ruby>"
        for i in range(start_index, start_index + run):
            result += kanji[i]
        result += f"<rt>{furi}</rt></ruby>"

        return result
    """

    return kanji
