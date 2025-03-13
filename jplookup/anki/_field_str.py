"""
Filename: jplookup.anki._field_str.py
Author: TravisGK
Date: 2025-03-13

Description: This file defines helper functions that handle
             processing text for individual fields in an Anki card.

Version: 1.0
License: MIT
"""

TAB = "\t"


def create_definition_str(card_parts: list) -> str:
    """
    Returns a string with HTML that nicely displays
    the word's various definitions across different
    parts of speech.
    """
    result_str = ""
    for word_type, part_data in card_parts["parts-of-speech"].items():
        result_str += f'<div class="part-of-speech">{word_type}</div>\n'
        result_str += '<ul class="word-definitions">\n'
        for definition in part_data["definitions"]:
            def_str = definition["definition"]
            result_str += f"{TAB}<li>\n{TAB}{TAB}{def_str}\n"

            examples = definition.get("examples")
            if examples:
                for example in examples:
                    result_str += f'{TAB}{TAB}<ul class="example-sentence">\n'
                    japanese = example["japanese"]
                    romanji = example["romanji"]
                    english = example["english"]

                    # Adds each sentence.
                    result_str += (
                        f'{TAB}{TAB}{TAB}<li class="japanese-example">'
                        f"{japanese}</li>\n"
                    )
                    result_str += (
                        f'{TAB}{TAB}{TAB}<li class="english-example">'
                        f"{english}</li>\n"
                    )
                    result_str += f"{TAB}{TAB}</ul>\n"

            result_str += f"{TAB}</li>\n"
        result_str += "</ul>\n"

    return result_str


def create_pretty_kana(kana: str, pitch_accent: int) -> str:
    """
    Returns a string with HTML that nicely displays
    the kana with additional phonetic information displayed.
    """
    return ""


def create_pretty_kanji(
    kanji: str,
    pitch_accent: int,
    furigana,  # list, could be None.
) -> str:
    """
    Returns a string with HTML that nicely displays
    the kanji with additional phonetic information displayed
    and furigana shown.
    """
    result = ""
    print(kanji)
    print(furigana)
    for k, furi in zip(kanji, furigana):
        if len(furi) == 0:
            result += k

    return result
