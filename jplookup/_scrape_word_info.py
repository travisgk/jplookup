from bs4 import BeautifulSoup
from ._processing._clean import clean_data
from ._processing._extract import extract_data
from ._cleanstr._textwork import remove_unwanted_html, remove_tags

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


def get_alternative_term_from_table(table_obj) -> str:
    text = table_obj.get_text()
    declaring_index = text.find("For pronunciation and definitions of")

    if declaring_index >= 0:
        opening_index = text.find("【", declaring_index)
        if opening_index >= 0:
            closing_index = text.find("】", opening_index)
            if closing_index >= 0:
                # splices out the term of the alternative spelling.
                alternative = text[opening_index + 1 : closing_index]
                return alternative

    return None


def scrape_word_info(term: str, jp_header, finding_alts: bool) -> list:
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
    found_word_part_headers = []
    breakout = False
    for part in PARTS_OF_SPEECH:
        for tag in HEADER_TAGS:
            current_header = jp_header.find_next(tag)
            while current_header and current_header.sourceline < end_line_num:
                header_text = current_header.get_text().strip()
                if header_text.startswith(part) and header_text != part + "s":
                    found_word_parts.append(part)
                    found_word_part_headers.append(current_header)
                current_header = current_header.find_next(tag)

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

        # looks for any "Alternative spelling" specifications.
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
                        alts.append(remove_tags(str(alt_spelling_span)))
                    layout[key]["alternative-spellings"] = alts

        # adds any pronunciation header that's below the "Etymology" header.
        for j, h in enumerate(pronunciation_headers):
            if (
                not h_used[j]
                and h.sourceline < next_ety_line_num
                and (e is None or (e.sourceline <= h.sourceline))
            ):
                h_used[j] = True
                layout[key]["pronunciation-headers"].append(h)

        # adds any part-of-speech header that's below the "Etymology" header.
        for j, f in enumerate(found_word_part_headers):
            if (
                not f_used[j]
                and f.sourceline < next_ety_line_num
                and (e is None or e.sourceline <= f.sourceline)
            ):
                f_used[j] = True
                layout[key]["speech-headers"].append(f)
                layout[key]["parts-of-speech"].append(found_word_parts[j])

        # adds any usage notes header that's below the "Etymology" header.
        for j, u in enumerate(usage_notes_headers):
            if (
                not u_used[j]
                and u.sourceline < next_ety_line_num
                and (e is None or e.sourceline <= u.sourceline)
            ):
                # retrieves the text contents out of either
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
                        # both a <p> and <ul> were found.
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
    keys_to_delete = []
    sorted_keys = sorted(layout.keys(), key=lambda x: int(x[1:]))  # sorts for safety.
    for key in sorted_keys:
        info = layout[key]

        if len(info["pronunciation-headers"]) == 0 and len(info["speech-headers"]) == 0:
            keys_to_delete.append(key)

    # Looks for redirects.
    JP_TABLE = "wikitable ja-see"
    redirects_to_etym = {}
    if finding_alts:
        for key in keys_to_delete:
            i = int(key[1:])
            etym_header = etymology_headers[i]
            if i < len(etymology_headers) - 1:
                end_line = etymology_headers[i + 1].sourceline
            else:
                end_line = 9999999

            next_table = etym_header.find_next("table", class_=JP_TABLE)
            if (
                next_table is not None
                and next_table.sourceline < end_line
                # and next_table.sourceline - etym_header.sourceline < 18
            ):
                redirect_term = get_alternative_term_from_table(next_table)
                if redirect_term is not None:
                    etym_term = "Etymology " + str(i + 1)
                    redirects_to_etym[redirect_term] = etym_term

                    layout[f"e{i}"] = None

            etym_index = int(key[1:])

    for key in keys_to_delete:
        del layout[key]

    if len(layout.keys()) == 0:
        return None, redirects_to_etym

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
    data = extract_data(layout)
    data = clean_data(data, term)

    return data, redirects_to_etym
