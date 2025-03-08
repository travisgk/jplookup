from jplookup._cleanstr._textwork import (
    percent_japanese,
    remove_text_in_brackets,
    remove_tags,
    remove_further_pronunciations,
    remove_unwanted_html,
    extract_japanese,
    extract_tag_contents,
)


def extract_data(layout: dict):
    """Extracts data from the given layout and returns it."""
    e_keys = list(layout.keys())
    e_keys.sort(key=lambda x: int(x[1:]))  # sorts for safety.

    data = {}
    for key in e_keys:
        # sets up next data entry for the Etymology header.
        data[key] = {
            "parts-of-speech": layout[key]["parts-of-speech"],
            "pronunciations": [],
            "definitions": [],
            "headwords": [],
            "usage-notes": [],
        }

        """
        Creates a dict mapping each header name (e.g. "p3" or "s1") 
        to the line where its contents end.
        """
        e = layout[key]  # etymology.

        alt_spellings = e.get("alternative-spellings")
        if alt_spellings is not None:
            data[key]["alternative-spellings"] = alt_spellings

        results = []
        results.extend(
            [
                (p.sourceline, p, f"p{i}")
                for i, p in enumerate(e["pronunciation-headers"])
            ]
        )
        results.extend(
            [(s.sourceline, s, f"s{i}") for i, s in enumerate(e["speech-headers"])]
        )
        results.sort(key=lambda x: x[0])
        to_end_line = {
            results[i][2]: (
                results[i + 1][0] if i < len(results) - 1 else e["end-line-num"]
            )
            for i in range(len(results))
        }
        results = None

        """
        Searches for pronunciation information.
        """
        for i, p_header in enumerate(e["pronunciation-headers"]):
            # looks for the next <ul> which could contain pronunciation info.
            current_ul = p_header.find_next("ul")
            end_line_num = to_end_line[f"p{i}"]  # SUSPECT
            while current_ul and current_ul.sourceline < end_line_num:
                ul_text = current_ul.get_text()
                if any(s in ul_text for s in ["ꜜ", "IPA"]):
                    contents = remove_tags(ul_text)
                    data[key]["pronunciations"].append(contents)

                current_ul = current_ul.find_next("ul")

        """
        Searches for headwords under each Part of Speech header.
        """
        u_has_been_used = [False for _ in e["usage-notes"]]
        for i, s_header in enumerate(e["speech-headers"]):
            headword = None
            headword_span = s_header.find_next("span", class_="headword-line")

            if i == len(e["speech-headers"]) - 1:
                s_end_line_num = 9999999
            else:
                s_end_line_num = e["speech-headers"][i + 1].sourceline

            usage_notes = None
            for j, u_header in enumerate(e["usage-headers"]):
                if (
                    not u_has_been_used[j]
                    and s_header.sourceline <= u_header.sourceline < s_end_line_num
                ):
                    u_has_been_used[j] = True
                    usage_notes = e["usage-notes"][j]
                    break

            if headword_span is not None:
                headword = str(headword_span).strip()
                period_index = headword.find("•")

                # looks for a counter.
                counter = None
                if period_index >= 0:
                    headword = headword[:period_index].strip()
                    p_parent = headword_span.find_parent("p")
                    p_text = p_parent.get_text()
                    counter_index = p_text.rfind("counter ")
                    if counter_index >= 0:
                        closing_index = p_text.find(")", counter_index + 8)
                        if closing_index >= 0:
                            contents = p_text[counter_index + 8 : closing_index]
                            if percent_japanese(contents) > 0.9:
                                counter = contents
                                # print(f"counter is {counter}")

                headword = remove_tags(headword).replace("\u0020", "")
                if counter is not None:
                    headword += f" counter:{counter}"
                data[key]["headwords"].append(headword)
                data[key]["usage-notes"].append(
                    "" if usage_notes is None else usage_notes
                )
            else:
                continue  # no headword span found. skips.

            """
            Searches for an ordered list that contains definitions.
            """
            ol = headword_span.find_next("ol")
            definitions = []
            if ol is not None:
                ol_str = remove_unwanted_html(str(ol))
                li_contents = extract_tag_contents(ol_str, "li")

                # iterates through every item in the ordered list.
                for li in li_contents:
                    if len(li) <= 9 or '<div class="citation-whole">' in li:
                        continue

                    entry = {"definition": ""}

                    # cleans up the text contents.
                    li = li[4:-5]
                    li = remove_tags(li, omissions=["ol", "li", "dd"])

                    # looks for an embedded <ol> inside the current <ol>.
                    sub_ol_start = li.find("<ol>")
                    if sub_ol_start >= 0:
                        sub_ol_end = li.rfind("</ol>")
                        if sub_ol_end >= 0:
                            # the <ol> contains its very own <ol>.
                            parent_def = li[:sub_ol_start].strip()
                            sublist_str = li[sub_ol_start + 4 : sub_ol_end].strip()
                            sublines = extract_tag_contents(sublist_str, "li")
                            entry["definition"] = remove_text_in_brackets(
                                parent_def
                            ).strip()
                            entry["sublines"] = sublines
                            definitions.append(entry)
                            continue

                    # no sublist is contained.
                    # searches for any contained <dd> or <dl> tags,
                    # which can contain synonym and antonym info,
                    # as well as example sentences.
                    tag_name = "dd"
                    dd_index = li.find("<dd>")
                    if dd_index < 0:
                        dd_index = li.find("<dl>")

                    if dd_index >= 0:
                        entry["definition"] = li[:dd_index].strip()
                        dd_tags = extract_tag_contents(li, "dd")
                        sublines = []
                        for dd_content in dd_tags:
                            dd_content = dd_content[4:-5]
                            sub_dd_index = dd_content.find("<dd>")
                            if sub_dd_index >= 0:
                                sublines.append(dd_content[:sub_dd_index])
                                sub_dd_tags = extract_tag_contents(dd_content, "dd")
                                for sub_dd in sub_dd_tags:
                                    sublines.append(sub_dd)
                            else:
                                sublines.append(dd_content)
                        entry["sublines"] = sublines
                    else:
                        entry["definition"] = li.strip()

                    # removes any text in brackets (usually a date of origin.
                    # since those are not helpful for learning.
                    entry["definition"] = remove_text_in_brackets(
                        entry["definition"]
                    ).strip()

                    # the new definition entry is finally added.
                    definitions.append(entry)

            data[key]["definitions"].append(definitions)

    return data


def extract_pronunciation_info(p_str: str):
    """Returns the region, the kana, the pitch-accent and IPA."""
    region, kana, pitch_accent, ipa = None, None, None, None

    # Extracts the region.
    REGIONS = ["Tokyo", "Osaka"]
    for r in REGIONS:
        if p_str.startswith(f"({r})"):
            region = r
            break

    # Extracts the kana.
    found_kana = extract_japanese(p_str)
    if len(found_kana) > 0:
        kana = found_kana[0]

    # Extracts the accent number.
    accent_start_index = p_str.find("– [")
    if accent_start_index >= 0:
        accent_end_index = p_str.find("])", accent_start_index)
        if accent_end_index - accent_start_index == 4:
            pitch_accent = int(p_str[accent_end_index - 1])

    # Extracts the IPA.
    IPA_TERM = "IPA(key):"
    ipa_key_index = p_str.find(IPA_TERM)
    if ipa_key_index >= 0:
        ipa_key_index += len(IPA_TERM)
        ipa_start_index = p_str.find("[", ipa_key_index)
        if ipa_start_index >= 0:
            ipa_end_index = p_str.find("]", ipa_start_index)
            if ipa_end_index >= 0:
                ipa = p_str[ipa_start_index + 1 : ipa_end_index]

    return region, kana, pitch_accent, ipa
