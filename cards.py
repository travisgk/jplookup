import json
import jplookup
import jplookup.anki


def main():
    FIELD_KEYS = [
        "key-term",
        "kana",
        "kanji",
        "definitions",
        "ipa",
        "pretty-kana",
        "pretty-kanji",
        "usage-notes",
    ]

    DEBUG_TERMS = [
        "昨日",
        "向こう",
        "忙しい",
        "楽しい",
        "涼しい",
    ]

    DEBUGGING = False

    # loads the .json with the written jplookup info.
    with open("jp-data.json", "r", encoding="utf-8") as jp_data:
        word_info = json.load(jp_data)

    with open("anki-out.txt", "w", encoding="utf-8") as out_file:
        for search_term, word_data in word_info.items():
            if DEBUGGING and not search_term in DEBUG_TERMS:
                continue  # if debugging, only debug terms aren't skipped.

            anki_card = jplookup.anki.dict_to_anki_fields(
                word_data, include_romanji=True
            )
            if anki_card is None:
                print(f"No card could be created for: {search_term}")
                continue

            # Writes every field of the Anki card to the output text file.
            for i, key in enumerate(FIELD_KEYS):
                out_file.write(anki_card[key])
                if i < len(FIELD_KEYS) - 1:
                    out_file.write("\t")
            out_file.write("\n")


if __name__ == "__main__":
    main()
