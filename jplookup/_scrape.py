import time
import requests
from bs4 import BeautifulSoup
from ._cleanstr._textwork import (
    remove_unwanted_html,
    remove_tags,
    remove_further_pronunciations,
    shorten_html,
)
from ._cleanstr._dictform import get_dictionary_form
from ._processing._clean import clean_data
from ._processing._extract import extract_data
from ._processing._redirects import remove_alternative_spellings, link_up_redirects

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


def _get_alternative_term_from_table(table_obj) -> str:
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


def _scrape_word_info(term: str, jp_header, finding_alts: bool) -> list:
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

    """
    Step 4) Matches up elements by line numbers to determine the page layout.
    """
    layout = {}
    h_used = [False for _ in pronunciation_headers]
    f_used = [False for _ in found_word_part_headers]
    if len(etymology_headers) == 0:
        etymology_headers = [jp_header]  # forces header.

    for i, e in enumerate(etymology_headers):
        key = f"e{i}"
        layout[key] = {
            "etym-header": e,
            "pronunciation-headers": [],
            "speech-headers": [],
            "parts-of-speech": [],
        }
        if i == len(etymology_headers) - 1:
            next_ety_line_num = 9999999
        else:
            next_ety_line_num = etymology_headers[i + 1].sourceline

        # looks for any "Alternative Spelling" specifications.
        alt_spellings_header = e.find_next("table", class_="wikitable floatright")
        if alt_spellings_header is None and len(etymology_headers) <= 1:
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
            if not h_used[j] and (
                e is None
                or (e.sourceline <= h.sourceline and h.sourceline < next_ety_line_num)
            ):
                h_used[j] = True
                layout[key]["pronunciation-headers"].append(h)

        # adds any part-of-speech header that's below the "Etymology" header.
        for j, f in enumerate(found_word_part_headers):
            if not f_used[j] and (
                e is None
                or (e.sourceline <= f.sourceline and f.sourceline < next_ety_line_num)
            ):
                f_used[j] = True
                layout[key]["speech-headers"].append(f)
                layout[key]["parts-of-speech"].append(found_word_parts[j])

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
                redirect_term = _get_alternative_term_from_table(next_table)
                if redirect_term is not None:
                    etym_term = f"Etymology {i + 1}"
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


def scrape(term: str, depth: int = 0, original_term=None, sleep_seconds=1.5) -> list:
    MAX_DEPTH = 1  # not inclusive.

    if depth > 0:
        # sleeps when doing a recursive loop to prevent getting blocked.
        time.sleep(sleep_seconds)

    # Gets the HTML source.
    url = f"https://en.wiktionary.org/wiki/{term}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error {response.status_code}: Could not fetch page for {term}")
        if depth < MAX_DEPTH:
            dict_form = get_dictionary_form(term)
        if dict_form is not None:
            return scrape(
                dict_form, depth + 1, original_term, sleep_seconds=sleep_seconds
            )
        return None

    clean_text = shorten_html(response.text)
    clean_text = remove_further_pronunciations(clean_text)

    # Finds the "Japanese" header; returns if no header was found.
    soup = BeautifulSoup(clean_text, "html.parser")
    japanese_header = None
    headers = []
    for header_tag in HEADER_TAGS:
        next_header = soup.find(header_tag, id="Japanese")
        if next_header is not None:
            japanese_header = next_header
            break

    if japanese_header is None:
        print("Error: No Japanese header was found on that Wiktionary page.")
        return None

    # Scrapes.
    # ---
    # Recursion will be performed on pages linked to by Wiktionary
    # as being alternative spellings if a definition isn't found.
    results = []
    word_info, redirects_to_etym = _scrape_word_info(
        term, japanese_header, depth < MAX_DEPTH
    )  # gets list of info.

    if word_info is not None and len(word_info.keys()) > 0:
        results.append(word_info)
    else:
        sorted_values = sorted(
            [v for v in redirects_to_etym.values()],
            key=lambda v: int(v[10:]),
        )

        results.append({v: None for v in sorted_values})

    # elif depth == 0 and len(redirects_to_etym.keys()) > 1:

    # alternatives = []  # tuples of the term (str) and the sourceline (int).
    if depth < MAX_DEPTH:
        # the program
        # checks to see if there are any alternatives that
        # Wiktionary is redirecting the user to.
        JP_TABLE = "wikitable ja-see"
        next_tables = japanese_header.find_all_next("table", class_=JP_TABLE)
        for table in next_tables:
            alternative = _get_alternative_term_from_table(table)
            if alternative is not None:
                if (results is None or len(results) == 0) and len(next_tables) == 1:
                    next_depth = depth  # a simple redirect won't add depth.
                else:
                    next_depth = depth + 1

                alt_results = scrape(
                    alternative, next_depth, original_term, sleep_seconds=sleep_seconds
                )

                if alt_results is not None:
                    results.extend(alt_results)

    if (results is None or len(results) == 0) and depth < MAX_DEPTH:
        # if there were no results found after looking for alternatives,
        # then the program will try to look for a dictionary form
        # of the word (the program assuming it could be a verb).
        dict_form = get_dictionary_form(term)
        if dict_form is not None:
            return scrape(
                dict_form, depth + 1, original_term, sleep_seconds=sleep_seconds
            )

    if depth == 0:
        results = link_up_redirects(
            results,
            redirects_to_etym,
            original_term if original_term else term,
        )

        if len(results) > 0:
            results = remove_alternative_spellings(results)

    return results
