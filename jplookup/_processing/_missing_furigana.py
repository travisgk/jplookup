from jplookup._cleanstr.identification import is_kanji, is_kana
from jplookup._cleanstr.textwork import kana_to_moras


def fill_in_missing_furigana(results: list):
    for r in results:
        for etym_name, etym_data in r.items():
            for part_of_speech, word_data in etym_data.items():
                term = word_data["term"]
                if all(not is_kanji(c) for c in term):
                    continue

                pronunciations = word_data.get("pronunciations")
                if pronunciations and any(is_kanji(c) for c in term):
                    for p_index, p in enumerate(pronunciations):
                        kana = p.get("kana")
                        furi = p.get("furigana")
                        if kana is not None and (
                            furi is None
                            or any(
                                (len(furi[i]) == 0 and is_kanji(c))
                                for i, c in enumerate(term)
                            )
                        ):
                            new_furi = ["" for _ in range(len(term))]
                            temp_term = term
                            temp_kana = kana

                            # Clips identical characters from kanji/kana.
                            start_index = 0
                            while (
                                len(temp_term) > 0
                                and len(temp_kana) > 0
                                and temp_term[0] == temp_kana[0]
                            ):
                                temp_term = temp_term[1:]
                                temp_kana = temp_kana[1:]
                                start_index += 1

                            while (
                                len(temp_term) > 0
                                and len(temp_kana) > 0
                                and temp_term[-1] == temp_kana[-1]
                            ):
                                temp_term = temp_term[:-1]
                                temp_kana = temp_kana[:-1]

                            #
                            for search_len in range(1, 5):
                                while (
                                    len(temp_term) > search_len
                                    and len(temp_kana) > search_len
                                    and is_kana(temp_term[search_len])
                                    and temp_term[search_len] == temp_kana[search_len]
                                    and all(
                                        is_kanji(temp_term[i])
                                        for i in range(search_len)
                                    )
                                ):
                                    for i, k in enumerate(temp_kana[:search_len]):
                                        new_furi[start_index + i] = k

                                    temp_term = temp_term[search_len + 1 :]
                                    temp_kana = temp_kana[search_len + 1 :]
                                    start_index += search_len + 1

                                while (
                                    len(temp_term) > search_len
                                    and len(temp_kana) > search_len
                                    and is_kana(temp_term[-search_len - 1])
                                    and temp_term[-search_len - 1]
                                    == temp_kana[-search_len - 1]
                                    and all(
                                        is_kanji(temp_term[-i - 1])
                                        for i in range(search_len)
                                    )
                                ):
                                    for i, k in enumerate(temp_kana[-search_len:]):
                                        new_furi[
                                            start_index
                                            + len(temp_term)
                                            - search_len
                                            + i
                                        ] = k

                                    temp_term = temp_term[: -search_len - 1]
                                    temp_kana = temp_kana[: -search_len - 1]

                            # Breaks the remaining kana into moras.
                            moras = kana_to_moras(temp_kana)

                            # Breaks the remaining term into series of
                            # alternating kanji/kana.
                            series = []
                            last_was_kana = False
                            for i, c in enumerate(temp_term):
                                if is_kana(c):
                                    if not last_was_kana:
                                        series.append("")
                                    last_was_kana = True
                                else:
                                    if i == 0 or last_was_kana:
                                        series.append("")
                                        if i > 0 and last_was_kana:
                                            series = (
                                                series[:i]
                                                + kana_to_moras(series[i])
                                                + series[i + 1 :]
                                            )
                                    last_was_kana = False
                                series[-1] += c

                            """
                            # Finds any kana that occurs only once.
                            kana_count = {}
                            for c in temp_kana:
                                if kana_count.get(c) is None:
                                    kana_count[c] = 1
                                else:
                                    kana_count[c] += 1

                            
                            unique_kana = ""
                            for key, value in kana_count.items():
                                if value == 1 and key in temp_term:
                                    unique_kana += key
                            unique_moras = kana_to_moras(unique_kana)

                            s_indices_to_delete = []
                            m_indices_to_delete = []

                            for unique_mora in unique_moras:
                                if unique_mora in series and unique in moras:

                                    series_index = -1
                                    for i, s in series:
                                        if unique == s:
                                            series_index = i
                                            break

                                    if series_index < 0:
                                        continue

                                    mora_index = -1
                                    for i, m in moras:
                                        if unique == m:
                                            mora_index = i
                                            break

                                    if mora_index < 0:
                                        continue

                                    s_indices_to_delete.append(series_index)
                                    m_indices_to_delete.append(mora_index)


                            series = [s for i, s in series if i not in s_indices_to_delete]
                            moras = [m for i, m in moras if i not in m_indices_to_delete]
                            """
                            # ):
                            #   series = series[1:]
                            #   moras = moras[1:]

                            if len(series) > 0 and len(series) == len(moras):
                                for i in range(len(series)):
                                    s, m = series[i], moras[i]
                                    new_furi[start_index + i] = moras[i]
                                p["furigana"] = new_furi
                            else:

                                furi_with_loc = []
                                furi_with_loc.append((start_index, "".join(moras)))
                                p["furigana-by-index"] = furi_with_loc

                            if furi is not None:
                                del p["furigana"]

                            KEYS = [
                                "kana",
                                "furigana",
                                "furigana-by-index",
                                "region",
                                "pitch-accent",
                                "ipa",
                            ]
                            pronunciations[p_index] = {
                                key: p[key] for key in KEYS if p.get(key)
                            }

    return results
