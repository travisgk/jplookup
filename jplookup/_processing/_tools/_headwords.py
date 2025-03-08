import jaconv
from jplookup._cleanstr._textwork import (
    is_hiragana,
    is_katakana,
    is_kana,
    separate_term_and_furigana,
)


# or removes hiragana if usage notes indicate katakana is preferred.
REMOVE_DUPLICATE_KATAKANA = True


def break_up_headwords(headword_str: str) -> list:
    """Returns a list of headwords (kanji and furigana in parentheses)."""
    return headword_str.split("or")


def extract_info_from_headwords(headwords: list, prefers_katakana: bool = False):
    """
    Returns the Japanese term,
    a list of furigana
    and a list of hiragana transcriptions.
    """
    results = [separate_term_and_furigana(h) for h in headwords]

    # gets the defining term for each headword.
    terms = [r[0] for r in results]
    if len(terms) == 0:
        return None

    # gets a list of furigana for each kanji.
    furis = []
    for r in results:
        local_furi = r[1]
        local_furi = ["".join(f) for f in local_furi]
        furis.append(local_furi)

    # gets the kana transcription for each headword.
    kanas = []
    for term, furi in zip(terms, furis):
        kana = ""
        for c, f in zip(term, furi):
            kana += c if is_kana(c) else f
        kanas.append(kana)

    # Headwords whose transcriptions are just one-to-one katakana
    # conversions are excluded.
    if REMOVE_DUPLICATE_KATAKANA:
        hira_indices, kata_indices = [], []
        for i, r in enumerate(kanas):
            if is_hiragana(r[0]):
                hira_indices.append(i)
            elif is_katakana(r[0]):
                kata_indices.append(i)

        hira_as_kata = {
            i: jaconv.hira2kata(kanas[i])
            for i in range(len(kanas))
            if i in hira_indices
        }

        indices_to_remove = []
        for i in kata_indices:
            for j in hira_indices:
                if kanas[i] == hira_as_kata[j]:
                    indices_to_remove.append(j if prefers_katakana else i)

        if len(indices_to_remove) > 0:
            new_furis, new_kanas = [], []
            for i in range(len(kanas)):
                if i not in indices_to_remove:
                    new_furis.append(furis[i])
                    new_kanas.append(kanas[i])
            furis = new_furis
            kanas = new_kanas

    if any(t != terms[0] for t in terms):
        print(f"The terms are different: {terms}")  # mere warning.

    return terms[0], furis, kanas
