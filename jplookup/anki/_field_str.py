"""
Filename: jplookup.anki._field_str.py
Author: TravisGK
Date: 2025-03-16

Description: This file defines helper functions that handle
             processing text for individual fields in an Anki card.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.textwork import kana_to_moras

TAB = ""
NEWLINE = ""


def _add_ruby_tags(japanese: str) -> str:
    result = ""
    prev_kanji_i = None
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
        if i + 1 == pitch_accent:  # DEBUG SEE IF THIS WORKS
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
    mora_num = 1

    if furigana_by_index is None:
        for k, furi in zip(kanji, furigana):
            if len(furi) == 0:
                if mora_num == pitch_accent:
                    result += _place_pitch_accent(k)
                else:
                    result += k
                mora_num += 1
            else:
                furi_str = ""
                if pitch_accent < mora_num + len(furi):
                    for f in furi:
                        if mora_num == pitch_accent:
                            furi_str += _place_pitch_accent(f)
                        else:
                            furi_str += f
                        mora_num += 1
                else:
                    furi_str += furi
                    mora_num += len(furi)
                result += f"<ruby>{k}<rt>{furi_str}</rt></ruby>"
        return result

    # handles furigana by index
    if len(furigana_by_index) == 1:
        start_index, run, furi = furigana_by_index[0]
        for i in range(start_index):
            result += kanji[i]

        result += "<ruby>"
        for i in range(start_index, start_index + run):
            result += kanji[i]
        result += f"<rt>{furi}</rt></ruby>"

        return result

    return kanji
