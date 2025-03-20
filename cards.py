import time
import random
import sys
import json
import jplookup
import jplookup.anki


def main():
    # loads the .json with the written jplookup info.
    with open("jp-data.json", "r", encoding="utf-8") as f:
        word_info = json.load(f)

    with open("anki-out.txt", "w", encoding="utf-8") as out_file:
        KEYS = [
            "key-term",
            "kana",
            "kanji",
            "definitions",
            "ipa",
            "pretty-kana",
            "pretty-kanji",
            "usage-notes",
        ]
        for search_term, word_data in word_info.items():

            anki_card = jplookup.anki.dict_to_anki_fields(
                word_data, include_romanji=True
            )
            if anki_card is None:
                print(search_term)
                continue

            for i, key in enumerate(KEYS):
                out_file.write(anki_card[key])
                if i < len(KEYS) - 1:
                    out_file.write("\t")
            out_file.write("\n")


if __name__ == "__main__":
    main()
