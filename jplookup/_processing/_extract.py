from jplookup._cleanstr._textwork import (
    remove_tags,
    remove_unwanted_html,
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
        }

        """
        Creates a dict mapping each header name (e.g. "p3" or "s1") 
        to the line where its contents end.
        """
        e = layout[key]
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
        for i, s_header in enumerate(e["speech-headers"]):
            headword = None
            headword_span = s_header.find_next("span", class_="headword-line")
            if headword_span is not None:
                headword = str(headword_span).strip()
                period_index = headword.find("•")
                if period_index >= 0:
                    headword = headword[:period_index].strip()
                headword = remove_tags(headword).replace("\u0020", "")
                data[key]["headwords"].extend([headword])
            else:
                continue  # no headword span found. skips.

            """
            Searches for an ordered list that contains definitions.
            """
            ol = headword_span.find_next("ol")
            definitions = []
            if ol is not None:
                # print(headword) # DEBUG
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
                            entry["definition"] = parent_def
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
                    definitions.append(entry)

            data[key]["definitions"].append(definitions)

    return data
