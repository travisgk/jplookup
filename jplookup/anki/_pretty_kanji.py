"""
Filename: jplookup.anki._pretty_kanji.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines the function which generates fancy HTML
             for a Japanese word.

Version: 1.0
License: MIT
"""

from jplookup._cleanstr.identification import is_kanji
from jplookup._cleanstr.textwork import kana_to_moras
from ._field_str import place_pitch_accent


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

    if furigana_by_index is None:
        moras_by_furi = []
        for furi in furigana:
            if len(furi) > 0:
                moras_by_furi.append(kana_to_moras(furi))
            else:
                moras_by_furi.append([])

        mora_num = 1
        i = 0
        while i < len(kanji):
            c = kanji[i]

            if is_kanji(c):
                furi_moras = moras_by_furi[i]

                furi_str = ""
                if pitch_accent < mora_num + len(furi_moras):
                    # The pitch marker of this word
                    # is in the furigana of this current kanji.
                    # ---
                    # Generates the furigana string with HTML for the marker.
                    for j, furi_mora in enumerate(furi_moras):
                        if mora_num == pitch_accent:
                            # Looks for the next kana char (if any).
                            if j == len(furi_moras) - 1:
                                if i == len(moras_by_furi) - 1:
                                    next_kana = None
                                else:
                                    next_furi = moras_by_furi[i + 1]
                                    if len(next_furi) > 0:
                                        next_kana = next_furi[0]
                                    else:
                                        next_kana = None
                            else:
                                next_kana = furi_moras[j + 1][0]

                            furi_str += place_pitch_accent(furi_mora, next_kana)
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
                i += 1  # moves forward.

            else:  # is kana.
                next_kanji_i = next(
                    (i + j + 1 for j, k in enumerate(kanji[i + 1 :]) if is_kanji(k)),
                    -1,
                )

                if next_kanji_i >= 0:
                    next_kana = kanji[i:next_kanji_i]
                else:
                    next_kana = kanji[i:]

                next_moras = kana_to_moras(next_kana)

                for j, mora in enumerate(next_moras):
                    if mora_num == pitch_accent:
                        if j == len(next_moras) - 1:
                            next_kana = None
                        else:
                            next_kana = next_moras[j + 1]
                        result += place_pitch_accent(mora, next_kana)
                    else:
                        result += mora
                    mora_num += 1
                    i += len(mora)
        return result

    # Handles furigana by index.
    if len(furigana_by_index) == 1:
        moras = kana_to_moras(kanji)
        mora_num = 1

        start_index, run, furi = furigana_by_index[0]

        # Deals with the moras coming prior to the furi by index.
        before = kanji[:start_index]
        moras_before = kana_to_moras(before)

        for i, mora in enumerate(moras_before):

            if mora_num == pitch_accent:
                if i == len(moras_before) - 1:
                    next_kana = None
                else:
                    next_kana = moras_before[i + 1][0]
                result += place_pitch_accent(mora, next_kana)
            else:
                result += mora
            mora_num += 1

        # Deals with the actual furigana.
        result += "<ruby>"
        for i in range(start_index, start_index + run):
            result += kanji[i]

        result += "<rt>"
        furi_moras = kana_to_moras(furi)
        uses_pitch_mark = pitch_accent <= start_index + len(furi_moras)
        if not uses_pitch_mark:
            result += '<span class="normal-rt">'
        furi_str = ""

        for i, mora in enumerate(furi_moras):
            if mora_num == pitch_accent:
                if i == len(furi_moras) - 1:
                    next_kana = None
                else:
                    next_kana = furi_moras[i + 1][0]
                result += place_pitch_accent(mora, next_kana)
            else:
                result += mora
            mora_num += 1

        if not uses_pitch_mark:
            result += "</span>"
        result += "</rt></ruby>"

        # Deals with the moras coming after the furi by index.
        after = kanji[start_index + run :]
        moras_after = kana_to_moras(after)

        for i, mora in enumerate(moras_after):
            if mora_num == pitch_accent:
                if i == len(moras_after) - 1:
                    next_kana = None
                else:
                    next_kana = moras_after[i + 1][0]
                result += place_pitch_accent(mora, next_kana)
            else:
                result += mora
            mora_num += 1

        return result

    return kanji
