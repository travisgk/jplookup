import requests
from bs4 import BeautifulSoup
from ._dictform import get_dictionary_form
from ._extract import extract_data

PARTS_OF_SPEECH = [
    
    "Noun",
    "Proper noun",
    "Particle",
    "Phrase",
    "Proverb",
    "Pronoun",
    "Adverb",
    "Numeral",
    "Adjective",
    "Adnominal",
    "Verb",
]
HEADER_TAGS = ["h4", "h3", "h2", "h1"]

def _scrape_word_info(term: str, jp_header) -> list:
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
            found_headers = jp_header.find_all_next(header_tag)
            next_headers.extend([
                h for h in found_headers 
                if h.sourceline < end_line_num 
                and contained_text in h.get_text()
            ])
        return next_headers

    pronunciation_headers = find_header_tags("Pronunciation")
    etymology_headers = find_header_tags("Etymology")

    """
    Step 3) Finds title tags containing parts of speech.
    """
    found_word_parts = []
    found_word_part_headers = []
    breakout = False
    for part in PARTS_OF_SPEECH:
        for tag in HEADER_TAGS:
            headers = jp_header.find_all_next(tag)
            for h in headers:
                if h.sourceline >= end_line_num:
                    # breaks out after the ending line.
                    breakout = True
                    break

                header_text = h.get_text().strip()
                if header_text == part and part:
                    found_word_parts.append(part)
                    found_word_part_headers.append(h)
            if breakout:
                break
        if breakout:
            break

    """
    Step 4) Matches up elements by line numbers to determine the page layout.
    """
    layout = {}
    h_used = [False for _ in pronunciation_headers]
    f_used = [False for _ in found_word_part_headers]
    if len(etymology_headers) == 0:
        etymology_headers = [jp_header] # forces header.

    for i, e in enumerate(etymology_headers):
        key = f"e{i}"
        layout[key] = {
            "etym-header": e,
            "pronunciation-headers": [],
            "speech-headers": [],
        }
        if i == len(etymology_headers) - 1:
            next_ety_line_num = None
        else:
            next_ety_line_num = etymology_headers[i + 1].sourceline

        # adds any pronunciation header that's below the "Etymology" header.
        for j, h in enumerate(pronunciation_headers):
            if (
                not h_used[j]
                and (
                    e is None 
                    or (
                        e.sourceline <= h.sourceline 
                        and (next_ety_line_num is None or h.sourceline < next_ety_line_num)
                    )
                )
            ):
                h_used[j] = True
                layout[key]["pronunciation-headers"].append(h)

        # adds any part-of-speech header that's below the "Etymology" header.
        for j, f in enumerate(found_word_part_headers):
            if (
                not f_used[j]
                and (
                    e is None
                    or(
                        e.sourceline <= f.sourceline 
                        and (next_ety_line_num is None or f.sourceline < next_ety_line_num)
                    )
                )
            ):
                f_used[j] = True
                layout[key]["speech-headers"].append(f)

    # Deletes any Etymology headers which contain no information.
    keys_to_delete = []
    sorted_keys = sorted(layout.keys(), key=lambda x: int(x[1:]))  # sorts for safety.
    for key in sorted_keys:
        info = layout[key]
        if (
            len(info["pronunciation-headers"]) == 0
        ):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del layout[key]

    if len(layout.keys()) == 0:
        return []

    """
    Step 5) Adds details about the ending line numbers 
            to each element of the layout.
    """
    def find_next_header(p_headers: list, s_headers: list, start_line_num: int):
        next_p = None  # pronunciation.
        next_s = None  # part-of-speech.

        for p in p_headers:
            if start_line_num < p.sourceline:
                next_p = p
                break

        for s in s_headers:
            if start_line_num < s.sourceline:
                next_s = s
                break

        if next_p is not None and next_s is not None:
            return next_p if next_p.sourceline < next_s.sourceline else next_s
        if next_p is not None:
            return next_p
        if next_s is not None:
            return next_s
        return None

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
    Step 6) Extracts data using the layout dictionary.
    """
    extract_data(layout)

    #for h in pronunciation_headers:
    #    print(f"{str(h)}\t{h.sourceline}")

    #for f in found_word_part_headers:
    #    print(f"{str(f)}\t{f.sourceline}")
    #print(layout)
    #print(found_word_parts)
    return found_word_parts


def scrape(term: str, depth: int = 0) -> list:
    MAX_DEPTH = 3

    # Gets the HTML source.
    url = f"https://en.wiktionary.org/wiki/{term}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error {response.status_code}: Could not fetch page for {term}")
        if depth < MAX_DEPTH:
            dict_form = get_dictionary_form(term)
        if dict_form is not None:
            return scrape(dict_form, depth + 1)
        return []

    # Finds the "Japanese" header; returns if no header was found.
    soup = BeautifulSoup(response.text, "html.parser")
    japanese_header = None
    headers = []
    for header_tag in HEADER_TAGS:
        next_headers = soup.find_all(header_tag, id="Japanese")
        if len(next_headers) > 0:
            japanese_header = next_headers[0]
            break

    if japanese_header is None:
        print("Error: No Japanese header was found on that Wiktionary page.")
        return []

    # Scrapes.
    # ---
    # Recursion will be performed on pages linked to by Wiktionary
    # as being alternative spellings if a definition isn't found.
    results = _scrape_word_info(term, japanese_header)  # gets list of info.
    if len(results) == 0 and depth < MAX_DEPTH:
        # if there were no results found, then the program
        # checks to see if there are any alternatives that
        # Wiktionary is redirecting the user to.
        next_tables = soup.find_all("table", class_="wikitable ja-see")
        for table in next_tables:
            text = table.get_text()
            declaring_index = text.find("For pronunciation and definitions of")
            if declaring_index >= 0:
                opening_index = text.find("【", declaring_index)
                if opening_index >= 0:
                    closing_index = text.find("】", opening_index)
                    if closing_index >= 0:
                        # splices out the term of the alternative spelling.
                        alternative = text[opening_index + 1 : closing_index]
                        alt_results = scrape(alternative, depth + 1)
                        results.extend(alt_results)

    if len(results) == 0 and depth < MAX_DEPTH:
        # if there were no results found after looking for alternatives,
        # then the program will try to look for a dictionary form
        # of the word (the program assuming it could be a verb).
        dict_form = get_dictionary_form(term)
        if dict_form is not None:
            return scrape(dict_form, depth + 1)

    return results