from ._cleanstr import is_japanese_char, percent_japanese


def _extract_japanese(subline: str) -> list:
    """
    Returns a list of every individual japanese phrase
    contained in the given text.
    """
    i = 0
    in_jp = False
    terms = ["",]
    for i in range(len(subline)):
        c = subline[i]

        if is_japanese_char:
            terms[-1] += c
            in_jp = True

        elif in_jp:  # not a jp char
                terms.append("")
                in_jp = False

    return [t for t in terms if len(t) > 0]


def clean_data(word_info: list, term: str):
    result = {}

    #print(word_info)
    etym_keys = word_info.keys()
    for etym_key in etym_keys:
        entry = word_info[etym_key]
        if len(etym_keys) > 1:
            etym_title = f"Etymology {int(etym_key[1:]) + 1}"
        else:
            etym_title = "Etymology"
            
        result[etym_title] = {}
        parts_of_speech = entry["parts-of-speech"]
        for i, part in enumerate(parts_of_speech):
            result[etym_title][part] = {
                "headwords": entry["headwords"][i],
                "definitions": [],
            }

            definitions = []
            for definition in entry["definitions"][i]:
                sublines = definition.get("sublines")
                if sublines is None:
                    definitions.append(definition)
                else:
                    new_def = {"definition": definition["definition"]}
                    j = 0
                    percent_jp = [percent_japanese(s) for s in sublines]
                    while j < len(sublines):
                        sub = sublines[j]
                        
                        # handles synonyms and antonyms.
                        if sub.startswith("Synonym"):
                            sub = sub[7:]
                            new_def["synonyms"] = _extract_japanese(sub)

                        elif sub.startswith("Antonym"):
                            sub = sub[7:]
                            new_def["antonyms"] = _extract_japanese(sub)

                        # handles sentence examples.
                        elif j + 2 < len(sublines):
                            if (
                                percent_jp[j] > 0.5
                                and all(
                                    percent_jp[j + k] < 0.5 
                                    and sublines[j + k].startswith("<dd>")
                                    and sublines[j + k].endswith("</dd>")
                                    for k in [1, 2]
                                )
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

                                j += 3
                                continue

                        j += 1
                    definitions.append(new_def)
            result[etym_title][part]["definitions"] = definitions


                        

    return result