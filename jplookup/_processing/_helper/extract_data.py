"""
Filename: jplookup._processing._helper.extract_data.py
Author: TravisGK
Date: 2025-03-16

Description: This file defines a function that can be given a
             conjugated verb and will do its best to guess
             the unconjugated form of the verb.

             This is used when a Wiktionary page couldn't be found
             for the searched term, so the program assumes it could
             be a conjugated verb and needs the dictionary form.

Version: 1.0
License: MIT
"""

from bs4 import BeautifulSoup
from jplookup._cleanstr.identification import (
    is_japanese_char,
    percent_japanese,
)
from jplookup._cleanstr.removal import (
    remove_text_in_brackets,
    remove_tags,
    remove_unwanted_html,
)
from jplookup._cleanstr.textwork import (
    extract_tag_contents,
    extract_japanese,
)

IGNORE_GIVEN_NAMES_AND_SURNAMES = True
IGNORE_SHORT_FOR_DEFINITIONS = True
GIVEN_NAMES_AND_SURNAMES = [
    "a female given name",
    "a surname",
    "a male given name",
    "a placename",
    "a place name",
    "a unisex given name",
]


def extract_data(layout: dict, find_embedded_kanji: bool):
    """Extracts data from the given layout and returns it."""
    e_keys = list(layout.keys())
    e_keys.sort(key=lambda x: int(x[1:]))  # sorts for safety.

    # True if this layout's only Etymology header is actually
    # just the Japanese header substituted in.
    no_true_etym = (
        find_embedded_kanji
        and len(e_keys) == 1
        and layout[e_keys[0]]["etym-header"].get_text().startswith("Japanese")
    )
    find_embedded_kanji = find_embedded_kanji and no_true_etym

    # Some Wiktionary pages that are kana will give pages
    # that just have a list of definitions for various
    # kanji spellings; in this case, this list will collect them
    # and the entire entry construction will be restarted
    # using the first of these terms.
    embedded_kanji_redirects = []

    data = {}
    for key in e_keys:  # etymology key.
        # sets up next data entry for the Etymology header.
        data[key] = {
            "parts-of-speech": layout[key]["parts-of-speech"],
            "pronunciations": [],
            "definitions": [],
            "headwords": [],
            "usage-notes": [],
        }

        """
        Step 1) Creates a dict mapping each header name (e.g. "p3" or "s1") 
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
        Step 2) Searches for pronunciation information.
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
        Step 3) Searches for headwords under each Part of Speech header
                and places Usage Notes, 
        """
        u_has_been_used = [False for _ in e["usage-notes"]]
        for i, s_header in enumerate(e["speech-headers"]):
            """
            Step 3a) Extracts information from the headword span
                     and gets the Usage Notes for this Etymology.
            """
            # looks for the first next <span class="headword-line">.
            headword = None
            headword_span = s_header.find_next("span", class_="headword-line")

            # determines where this etymology information ends.
            if i == len(e["speech-headers"]) - 1:
                s_end_line_num = 9999999
            else:
                s_end_line_num = e["speech-headers"][i + 1].sourceline

            # places a Usage Notes header.
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
                # Grabs information from the headword span.
                headword = str(headword_span).strip()
                period_index = headword.find("•")

                # Looks for a counter noun.
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

                # Removes junk space from headword information.
                headword = remove_tags(headword).replace("\u0020", "")

                # Embeds the counter noun into the headword directly.
                if counter is not None:
                    headword += f" counter:{counter}"

                # Adds the headword string and usage notes.
                data[key]["headwords"].append(headword)
                data[key]["usage-notes"].append(
                    "" if usage_notes is None else usage_notes
                )
            else:
                continue  # no headword span found. skips.

            """
            Step 3b) Searches for an ordered list that contains definitions.
            """
            ol = headword_span.find_next("ol")
            definitions = []
            if ol is not None:  # the <ol> with definitions was found.
                ol_str = remove_unwanted_html(str(ol))
                li_contents = extract_tag_contents(ol_str, "li")

                # Iterates through every listed item in the ordered list.
                for li in li_contents:
                    if len(li) <= 9 or '<div class="citation-whole">' in li:
                        continue  # ignores tiny <li>'s and other irrelevants.

                    entry = {"definition": ""}

                    # Cleans up the text contents.
                    li = li[4:-5]
                    if find_embedded_kanji:
                        li_with_anchors = li
                        li_with_anchors = remove_tags(
                            li_with_anchors,
                            omissions=["a"],
                        )

                    li = remove_tags(li, omissions=["ol", "li", "dd", "b"])
                    li = li.replace("<b> ", " <b>").replace(" </b>", "</b> ")
                    li = li.strip()

                    """
                    Step 3b.1) Checks if Definition meets standards.
                    """
                    # Definitions beginning with certain phrases are ignored.
                    if IGNORE_GIVEN_NAMES_AND_SURNAMES and any(
                        li.startswith(s) for s in GIVEN_NAMES_AND_SURNAMES
                    ):
                        continue  # skips.

                    # Definitions beginning with this phrase are ignored.
                    if li.startswith("Short for "):
                        continue  # skips.

                    # Definitions beginning with this phrase are ignored.
                    DUMMY_PHRASE = "This term needs a translation to English."
                    if li.startswith(DUMMY_PHRASE):
                        continue  # skips.
                    else:
                        # The dummy phrase could still occur after the colon.
                        colon_index = li.find(":")
                        if colon_index >= 0:
                            if li[colon_index + 1 :].strip().startswith(DUMMY_PHRASE):
                                continue  # skips.

                    if li.startswith("("):
                        closed_paren = li.find(") ")
                        if li[closed_paren + 2 :].startswith(DUMMY_PHRASE):
                            continue  # skips.

                    """
                    Step 3b.2) Looks for redirects for a page

                    """
                    if (
                        find_embedded_kanji
                        and is_japanese_char(li[0])
                        and len(e["pronunciation-headers"]) == 0
                    ):
                        colon_index = li.find(":")
                        if colon_index >= 0:
                            kanji_terms = li[:colon_index].split(",")
                            kanji_terms = [k.strip() for k in kanji_terms]

                            # Checks to see which first term has a redirect link.
                            redirecting_term_index = -1
                            soup = BeautifulSoup(li_with_anchors, "html.parser")
                            new_anchors = soup.find_all("a", class_="new")
                            if len(new_anchors) > 0:
                                anchor_texts = [a.get_text() for a in new_anchors]
                                for term_index, alt_term in enumerate(kanji_terms):
                                    has_redirect_link = True
                                    for a in anchor_texts:
                                        if a == alt_term:
                                            has_redirect_link = False
                                            break
                                    if has_redirect_link:
                                        redirecting_term_index = term_index
                                        break
                            else:
                                redirecting_term_index = 0

                            # only one in a series will be used.
                            if redirecting_term_index >= 0:
                                embedded_kanji_redirects.append(
                                    kanji_terms[redirecting_term_index]
                                )

                    if find_embedded_kanji and len(embedded_kanji_redirects) > 0:
                        continue  # only looking for redirecting context terms now.

                    """
                    Step 3b.3) Looks for an embedded <ol> inside the current <ol>.
                    """
                    sub_ol_start = li.find("<ol>")
                    if sub_ol_start >= 0:
                        sub_ol_end = li.rfind("</ol>")
                        if sub_ol_end >= 0:
                            # the <ol> contains its very own <ol>.
                            parent_def = li[:sub_ol_start].strip()
                            sublist_str = li[sub_ol_start + 4 : sub_ol_end].strip()
                            sublines = extract_tag_contents(sublist_str, "li")
                            entry["definition"] = (
                                remove_text_in_brackets(parent_def)
                                .strip()
                                .replace("<b>", "")
                                .replace("</b>", "")
                            )
                            entry["sublines"] = sublines
                            definitions.append(entry)
                            continue

                    """
                    Step 3b.4) By this point, no sublist is contained.
                               The program will now search for any contained <dd> 
                               or <dl> tags, which can contain synonym 
                               and antonym info, as well as example sentences.
                    """
                    tag_name = "dd"
                    dd_index = li.find("<dd>")
                    if dd_index < 0:
                        # Searches for a <dl> if a <dd> wasn't found.
                        dd_index = li.find("<dl>")

                    if dd_index >= 0:
                        # A <dd> or <dl> was found.
                        # the <li> string is already stripped of its HTML tag
                        # on the left, so only the right needs to be clipped.
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

                    """
                    Step 3b.5) Removes any text in brackets.
                               Usually a date of origin.
                               since those are not helpful for learning,
                               then finially adds the new entry.
                    """
                    entry["definition"] = remove_text_in_brackets(
                        entry["definition"]
                    ).strip()
                    definitions.append(entry)
            data[key]["definitions"].append(definitions)

    return data, embedded_kanji_redirects