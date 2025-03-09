import jaconv


def _kana_matches(p_kana: str, t_kana: str) -> bool:
    """
    Returns True if the kana match each other,
    with the flexibility that a char in t_kana can
    be either い or う and still match with a p_kana's
    corresponding ー.

    """
    if len(p_kana) != len(t_kana):
        return False

    p_kana = jaconv.hira2kata(p_kana)
    t_kana = jaconv.hira2kata(t_kana)

    for p, t in zip(p_kana, t_kana):
        if p != t and not (p == "ー" and t in "いうイウ"):
            return False

    return True


def find_pronunciation_match(pronunciation_bank: dict, transcription: dict):
    """
    Returns the pronunciation dictionary in <pronunciation_bank>
    that matches up to the given <transcription> by the kana
    contained in both.

    If there's no match, then None is returned.
    """
    t_kana = transcription["kana"]

    for p_kana in pronunciation_bank.keys():
        if _kana_matches(p_kana, t_kana):
            return pronunciation_bank[p_kana]

    return None
