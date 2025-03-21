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
        TERMS = [
            "借りる",
            "降りる",
            "大きな",
            "勤める",
            "入れる",
            "向こう",
            "食べる",
            "冷たい",
            "小さな",
            "忙しい",
            "晴れる",
            "開ける",
            "初めて",
            "閉まる",
            "お婆さん",
            "曲がる",
            "並べる",
            "難しい",
            "美味しい",
            "消える",
            "皆さん",
            "大きい",
            "楽しい",
            "お母さん",
            "少ない",
            "誕生日",
            "涼しい",
            "小さい",
            "答える",
            "危ない",
            "浴びる",
            "直ぐに",
            "無くす",
            "暖かい",
            "掛ける",  # YOU ARE ADDING THE BLUES
        ]
        for search_term, word_data in word_info.items():
            if not any(search_term == term for term in TERMS):
                continue

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
