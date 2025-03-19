"""
Filename: jplookup._scrape._html._scrape_word_info.py
Author: TravisGK
Date: 2025-03-19

Description: This file defines the helper function that actually
             retrieves raw data from the Wiktionary HTML.

Version: 1.0
License: MIT
"""

from bs4 import BeautifulSoup
from jplookup._cleanstr.identification import is_japanese_char
from jplookup._cleanstr.removal import remove_tags
from ._extract_data import extract_data
from ._clean_data import clean_data

PARTS_OF_SPEECH = [
    "Noun",
    "Adjective",
    "Adnominal",
    "Verb",
    "Adverb",
    "Proper noun",
    "Interjection",
    "Particle",
    "Counter",
    "Conjunction",
    "Affix",
    "Suffix",
    "Prefix",
    "Phrase",
    "Proverb",
    "Pronoun",
    "Numeral",
    "Syllable",
]
HEADER_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def get_alternative_terms_from_table(table_obj) -> list:
    """
    Returns any text that's in brackets of a specific table element
    which contains some form of alternative spelling.
    """

    text = table_obj.get_text()
    declaring_index = text.find("For pronunciation and definitions of")

    if declaring_index < 0:
        return []

    alts = []
    index = declaring_index
    while index < len(text):
        opening_index = text.find("【", index + 1)
        if opening_index >= 0:
            closing_index = text.find("】", opening_index)
            if closing_index >= 0:
                # Splices out the term of the alternative spelling.
                alternative = text[opening_index + 1 : closing_index]
                alts.append(alternative)
                index = closing_index + 1
                continue
        break

    return alts


def scrape_word_info(
    term: str,
    jp_header,
    finding_alts: bool,
    find_embedded_kanji: bool,
):
    """
    TODO: COMMENT NEEDS UPDATE
    Returns a list of dictionaries, with each dict representing
    a page from Wiktionary. This marks down the locations of various HTML
    elements and grabs some raw HTML contents.
    """
    """
    Step 1) Looks for the source line where the Japanese ends.
    """
    end_line_num = 9999999
    ending_header = jp_header.find_next("div", class_="mw-heading mw-heading2")
    if ending_header is not None:
        end_line_num = ending_header.sourceline

    """
    Step 2) Finds title tags containing "Pronunciation" and "Etymology".
    """

    def find_header_tags(contained_text: str) -> list:
        next_headers = []
        for header_tag in HEADER_TAGS:
            current_header = jp_header.find_next(header_tag)
            while current_header and current_header.sourceline < end_line_num:
                if current_header.get_text().startswith(contained_text):
                    next_headers.append(current_header)
                current_header = current_header.find_next(header_tag)

        return next_headers

    pronunciation_headers = find_header_tags("Pronunciation")
    etymology_headers = find_header_tags("Etymology")
    usage_notes_headers = find_header_tags("Usage notes")

    """
    Step 3) Finds title tags containing parts of speech.
    """
    found_word_parts = []
    found_word_part_lines = []
    found_word_part_headers = []
    breakout = False
    for part in PARTS_OF_SPEECH:
        for tag in HEADER_TAGS:
            current_header = jp_header.find_next(tag)
            while current_header and current_header.sourceline < end_line_num:
                header_text = current_header.get_text().strip()
                if header_text.startswith(part) and header_text != part + "s":
                    found_word_parts.append(part)
                    found_word_part_lines.append(current_header.sourceline)
                    found_word_part_headers.append(current_header)
                current_header = current_header.find_next(tag)

    # Zips, sorts by order of appearance, and unzips back into separate lists.
    if len(found_word_part_lines) > 0:
        sorted_lists = sorted(
            zip(
                found_word_part_lines,
                found_word_parts,
                found_word_part_headers,
            )
        )
        found_word_part_lines, found_word_parts, found_word_part_headers = map(
            list, zip(*sorted_lists)
        )

    # Ensures that word parts all have unique key names.
    for part in PARTS_OF_SPEECH:
        found_indices = []
        for i, found in enumerate(found_word_parts):
            if found == part:
                found_indices.append(i)
        if len(found_indices) > 1:
            for i, matching_index in enumerate(found_indices):
                new_name = f"{part} {i + 1}"
                found_word_parts[matching_index] = new_name

    """
    Step 4) Matches up elements by line numbers to determine the page layout.
    """
    layout = {}
    h_used = [False for _ in pronunciation_headers]
    f_used = [False for _ in found_word_part_headers]
    u_used = [False for _ in usage_notes_headers]
    if len(etymology_headers) == 0:
        etymology_headers = [jp_header]  # forces header.

    for i, e in enumerate(etymology_headers):
        key = f"e{i}"
        layout[key] = {
            "etym-header": e,
            "pronunciation-headers": [],
            "speech-headers": [],
            "parts-of-speech": [],
            "usage-headers": [],
            "usage-notes": [],
        }
        if i == len(etymology_headers) - 1:
            next_ety_line_num = 9999999
        else:
            next_ety_line_num = etymology_headers[i + 1].sourceline

        # Looks for any "Alternative spelling" specifications.
        alt_spellings_header = e.find_next("table", class_="wikitable floatright")

        if alt_spellings_header is None:
            alt_spellings_header = jp_header.find_next(
                "table", class_="wikitable floatright"
            )

        if alt_spellings_header is not None:
            table_text = str(alt_spellings_header)
            if (
                alt_spellings_header.sourceline <= next_ety_line_num
                and "Alternative spelling" in table_text
            ):
                soup = BeautifulSoup(table_text, "html.parser")
                alt_spellings = soup.find_all("span", class_="Jpan")
                if len(alt_spellings) > 0:
                    alts = []
                    for alt_spelling_span in alt_spellings:
                        tagless = remove_tags(str(alt_spelling_span))
                        for i, c in enumerate(tagless):
                            if not is_japanese_char(c):
                                tagless = tagless[:i]
                                break
                        alts.append(tagless)
                    layout[key]["alternative-spellings"] = alts

        # Adds any pronunciation header that's below the "Etymology" header.
        for j, h in enumerate(pronunciation_headers):
            if (
                not h_used[j]
                and h.sourceline < next_ety_line_num
                and (e is None or (e.sourceline <= h.sourceline))
            ):
                h_used[j] = True
                layout[key]["pronunciation-headers"].append(h)

        # If the Wiktionary entry doesn't place the Pronunciation
        # under an Etymology and it was never found to be below any
        # etym header, then the pronunciation will simply
        # be applied to the first etymology.
        #
        # Applying to all instead of just the first may be dangerous?
        # Best case scenario: this isn't common
        # b/c the Pronunciations seem to regularly given under Etyms.
        if i == len(etymology_headers) - 1 and len(h_used) == 1 and not h_used[0]:
            h_used[0] = True
            layout["e0"]["pronunciation-headers"].append(h)

        # Adds any part-of-speech header that's below the "Etymology" header.
        for j, f in enumerate(found_word_part_headers):
            if (
                not f_used[j]
                and f.sourceline < next_ety_line_num
                and (e is None or e.sourceline <= f.sourceline)
            ):
                # Appends the information and includes the sourceline too.
                f_used[j] = True
                layout[key]["speech-headers"].append(f)
                layout[key]["parts-of-speech"].append(
                    (found_word_parts[j], found_word_part_lines[j])
                )

        # Adds any usage notes header that's below the "Etymology" header.
        for j, u in enumerate(usage_notes_headers):
            if (
                not u_used[j]
                and u.sourceline < next_ety_line_num
                and (e is None or e.sourceline <= u.sourceline)
            ):
                # Retrieves the text contents out of either
                # the following <ul> or <p> to get the usage notes,
                # grabbing the closest text.
                next_p = u.find_next("p")
                next_ul = u.find_next("ul")
                DUMMY_PHRASE = "Japanese terms spelled with"
                if next_p and next_p.sourceline < next_ety_line_num:
                    u_used[j] = True
                    if (
                        next_ul
                        and next_ul.sourceline < next_ety_line_num
                        and not next_ul.get_text().startswith(DUMMY_PHRASE)
                    ):
                        # Both a <p> and <ul> were found.
                        if next_p.sourceline < next_ul.sourceline:
                            layout[key]["usage-headers"].append(next_p)
                            layout[key]["usage-notes"].append(next_p.get_text())
                        else:
                            layout[key]["usage-headers"].append(next_ul)
                            layout[key]["usage-notes"].append(next_ul.get_text())

                    else:
                        layout[key]["usage-headers"].append(next_p)
                        layout[key]["usage-notes"].append(next_p.get_text())
                elif (
                    next_ul
                    and next_ul.sourceline < next_ety_line_num
                    and not next_ul.get_text().startswith(DUMMY_PHRASE)
                ):
                    u_used[j] = True
                    layout[key]["usage-headers"].append(next_ul)
                    layout[key]["usage-notes"].append(next_ul.get_text())

    # Figures out which empty Etymology headers to delete.
    etym_keys_to_delete = []
    sorted_keys = sorted(layout.keys(), key=lambda x: int(x[1:]))  # sorts for safety.
    for key in sorted_keys:
        info = layout[key]

        if len(info["pronunciation-headers"]) == 0 and len(info["speech-headers"]) == 0:
            etym_keys_to_delete.append(key)

    # Looks for redirects for every Etymology
    # lacking any Pronunciation or Part of Speech header.
    JP_TABLE = "wikitable ja-see"
    all_redirect_terms = []
    redirects_to_etym = {}
    if finding_alts:
        for key in etym_keys_to_delete:
            i = int(key[1:])
            etym_header = etymology_headers[i]
            if i < len(etymology_headers) - 1:
                end_line = etymology_headers[i + 1].sourceline
            else:
                end_line = 9999999

            # Looks for a <table> with a redirect to another webpage
            # for an alternative spelling.
            next_table = etym_header.find_next("table", class_=JP_TABLE)
            if next_table is not None and next_table.sourceline < end_line:
                redirect_terms = get_alternative_terms_from_table(next_table)

                if len(redirect_terms) > 0:
                    all_redirect_terms.extend(redirect_terms)
                    etym_term = "Etymology " + str(i + 1)
                    redirects_to_etym[redirect_terms[0]] = etym_term
                    layout[f"e{i}"] = None

    # Finally deletes the keys with None in them.
    for key in etym_keys_to_delete:
        del layout[key]

    if len(layout.keys()) == 0:
        redirects_to_etym = {}
        for i, redirect_term in enumerate(all_redirect_terms):
            etym_term = "Etymology " + str(i + 1)
            redirects_to_etym[redirect_term] = etym_term

        return None, redirects_to_etym, None

    """
    Step 5) Adds details about the ending line numbers 
            to each element of the layout.
    """
    keys = list(layout.keys())
    for i, key in enumerate(keys):
        e = layout[key]
        if i < len(keys) - 1:
            next_key = keys[i + 1]
            next_e = layout[next_key]
            e["end-line-num"] = next_e["etym-header"].sourceline
        else:
            e["end-line-num"] = end_line_num

    """
    Step 6) Extracts data using the layout dictionary,
            then cleans up that data for user-friendliness
            and returns the result.
    """
    data, embedded_kanji_redirects = extract_data(layout, find_embedded_kanji)
    if len(embedded_kanji_redirects) > 0:
        return None, None, embedded_kanji_redirects

    data = clean_data(data, term)

    return data, redirects_to_etym, None
