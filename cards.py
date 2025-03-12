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

    for search_term, word_data in word_info.items():
        jplookup.anki.dict_to_anki_fields(word_data)


if __name__ == "__main__":
    main()
