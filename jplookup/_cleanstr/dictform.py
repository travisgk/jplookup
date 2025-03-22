"""
Filename: jplookup._cleanstr.dictform.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines a function that can be given a
             conjugated verb and will do its best to guess
             the unconjugated form of the verb.

             This is used when a Wiktionary page couldn't be found
             for the searched term, so the program assumes it could
             be a conjugated verb and needs the dictionary form.

Version: 1.0
License: MIT
"""


def get_dictionary_form(word):
    # Expanded list of irregular verbs & their dictionary forms.
    irregular_verbs = {
        #
        # する and its variations
        "しました": "する",
        "しなかった": "する",
        "している": "する",
        "してた": "する",
        "してる": "する",
        "しておる": "する",
        "しよう": "する",
        "される": "する",
        "させる": "する",
        "させられる": "する",
        "しなければ": "する",
        "しなくちゃ": "する",
        "しなきゃ": "する",
        "しちゃった": "する",
        #
        # できる (potential of する)
        "できました": "できる",
        "できなかった": "できる",
        "できて": "できる",
        "できちゃった": "できる",
        #
        # くる and its variations
        "来ました": "来る",
        "来なかった": "来る",
        "来て": "来る",
        "きた": "来る",
        "こない": "来る",
        "こなかった": "来る",
        "こよう": "来る",
        "こられる": "来る",
        "こい": "来る",
        #
        # 行く
        "行きました": "行く",
        "行かなかった": "行く",
        "行って": "行く",
        "行った": "行く",
        #
        # 敬語 (polite/honorific verbs)
        "いらっしゃいました": "いらっしゃる",
        "いらっしゃった": "いらっしゃる",
        "おっしゃいました": "おっしゃる",
        "おっしゃった": "おっしゃる",
        "下さった": "下さる",
        "下さいました": "下さる",
        "なさいました": "なさる",
        "なさった": "なさる",
        "召し上がった": "召し上がる",
        "召し上がりました": "召し上がる",
        "くださった": "くださる",
        "くださいます": "くださる",
        "ご覧になった": "ご覧になる",
        "ご覧になりました": "ご覧になる",
        #
        # ござる variations
        "ございました": "ござる",
        "ござった": "ござる",
        #
        # Other irregulars (common contractions)
        "参りました": "参る",
        "参った": "参る",
        "存じました": "存じる",
        "存じ上げました": "存じ上げる",
        "知っていた": "知る",
        "知ってる": "知る",
        "忘れちゃった": "忘れる",
        "考えちゃった": "考える",
        "持ってた": "持つ",
        "持っている": "持つ",
        "取っちゃった": "取る",
        "見てた": "見る",
        "やってた": "やる",
        "やってる": "やる",
        "飲んでた": "飲む",
        "飲んでる": "飲む",
        "遊んでた": "遊ぶ",
        "遊んでる": "遊ぶ",
        "死んでた": "死ぬ",
        "死んでる": "死ぬ",
        "書いてた": "書く",
        "書いてる": "書く",
        "泳いでた": "泳ぐ",
        "泳いでる": "泳ぐ",
        "笑ってた": "笑う",
        "笑ってる": "笑う",
    }

    if word in irregular_verbs:
        return irregular_verbs[word]

    # 五段 verbs need special handling because of their stem changes
    godan_mappings = {
        "わない": "う",
        "わなかった": "う",  # e.g., 買わない → 買う
        "らない": "る",
        "らなかった": "る",  # e.g., 困らない → 困る
        "たない": "つ",
        "たなかった": "つ",  # e.g., 立たない → 立つ
        "ばない": "ぶ",
        "ばなかった": "ぶ",  # e.g., 遊ばない → 遊ぶ
        "まない": "む",
        "まなかった": "む",  # e.g., 読まない → 読む
        "さない": "す",
        "さなかった": "す",  # e.g., 話さない → 話す
        "がない": "ぐ",
        "がなかった": "ぐ",  # e.g., 泳がない → 泳ぐ
        "かない": "く",
        "かなかった": "く",  # e.g., 書かない → 書く
        "なない": "ぬ",
        "ななかった": "ぬ",  # e.g., 死なない → 死ぬ
    }

    for end, base in godan_mappings.items():
        if word.endswith(end):
            return word[: -len(end)] + base  # Restore dictionary form

    # Common 一段 verb patterns (ichidan verbs end in る and are easier)
    ichidan_mappings = {
        "ました": "る",
        "なかった": "る",
        "ない": "る",
        "ている": "る",
        "てた": "る",
        "てる": "る",
        "れば": "る",
        "られる": "る",
        "せる": "る",
    }

    for end, base in ichidan_mappings.items():
        if word.endswith(end):
            return word[: -len(end)] + base  # restores dictionary form.

    return None  # not recognized as a conjugated verb.
