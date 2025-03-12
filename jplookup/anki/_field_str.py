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
            result_str += f"\t<li>\n\t\t{def_str}\n"

            examples = definition.get("examples")
            if examples:
                for example in examples:
                    result_str += '\t\t<ul class="example-sentence">\n'
                    japanese = example["japanese"]
                    romanji = example["romanji"]
                    english = example["english"]

                    # Adds each sentence.
                    result_str += (
                        f'\t\t\t<li class="japanese-example">{japanese}</li>\n'
                    )
                    result_str += f'\t\t\t<li class="english-example">{english}</li>\n'
                    result_str += "\t\t</ul>\n"

            result_str += "\t</li>\n"
        result_str += "</ul>\n"

    return result_str


def create_pretty_kana(kana: str, pitch_accent: int) -> str:
    return ""
