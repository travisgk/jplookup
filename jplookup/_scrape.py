"""
Filename: jplookup._scrape.py
Author: TravisGK
Date: 2025-03-16

Description: This file defines the primary function that scrapes
             information about a Japanese term from its English Wiktionary
             page and returns it in an easy-to-read format for the user.

             The idea is to give back the information on the main Wiktionary
             page while also incorporating the relevant Etymologies referred
             to on separate Wiktionary pages.

Version: 1.0
License: MIT
"""

import requests
import time
from bs4 import BeautifulSoup
from ._cleanstr.dictform import get_dictionary_form
from ._cleanstr.identification import is_kanji
from ._cleanstr.removal import (
    shorten_html,
    remove_further_pronunciations,
    remove_alternative_spellings,
)
from ._processing.tools.exchange_phonetic_info import *
from ._processing.tools.remove_empty_entries import *
from ._processing.tools.embed_redirects import *
from ._processing.scrape_word_info import *
from ._processing._missing_furigana import fill_in_missing_furigana


def scrape(
    term: str,
    depth: int = 0,
    original_term=None,
    rc_sleep_seconds=5,
    force_sleep: bool = False,
    verbose: bool = True,
):
    """
    Scrapes a Wiktionary entry for Japanese word information,
    returning a list which includes pronunciations and definitions,
    with definitions having any example sentences added.
    This will be a list of dictionaries.

    None is returned if no results could be found.

    The first dictionary of the returned results will contain
    the primary

    Any pages that are redirected to (i.e. alternative spelling) will
    be scraped as well, however, only information relevant to the original
    searched term will be taken and then appended to the root page's data.
    For example:
        - term = "はく":
            This will grab the definitions of ALL words with kanji spellings,
            where for each kanji spelling its Wiktionary page
            is scraped recursively, however, only etymologies
            with pronunciations of "はく" under these child Wiktionary pages
            will have their definitions taken and added to the data of the
            original scrape(...) call.

        - term = "捕る"
            This Wiktionary page indicates that "捕る"
            is an alternative spelling of "はく", providing a redirect to the
            Wiktionary page for "はく". In this case, the "はく" page is scraped,
            however, only definitions that are specified as fitting
            with the contextual spelling ("捕る") or have no specified
            fitting contextual spellings at all will be taken
            and added to the data of the original scrape(...) call.

        - term = "取る"
            This Wiktionary page indicates that "取る"
            is an alternative spelling of "はく", providing a redirect to the
            Wiktionary page for "はく". In this case, the "はく" page is scraped,
            however, only definitions that are specified as fitting
            with the contextual spelling ("取る") or have no specified
            fitting contextual spellings at all will be taken
            and added to the data of the original scrape(...) call.

    Parameters:
        term (str): the Japanese word to search.
        depth (int): the recursive depth.
        original_term (str): used for recursive calls; holds the original term
                             searched when <term> is being used
                             for an alternative spelling.
        rc_sleep_seconds: the duration in seconds that the program
                          will sleep before scraping a child Wiktionary page.
        force_sleep (bool): if True, the program sleeps for <rc_sleep_seconds>
                            regardless of the current recursive depth.
        verbose (bool): if False, the script won't print any error messages.
    """
    """Returns either a list or None."""
    MAX_CONNECT_ATTEMPTS = 5  # number of times to retry if fails for a term.
    MAX_DEPTH = 1  # not inclusive. not tested for above 1.

    if depth > 0 or force_sleep:
        # Sleeps when doing a recursive loop to prevent getting blocked.
        time.sleep(rc_sleep_seconds)

    """
    Step 1) Retrieves HTML and searches for the main header.
    """

    def show_http_error_message(e):
        # If requests runs into some error other than 404,
        # then the program assumes Wiktionary is blocking access.
        if verbose:
            print(f"Scrape Error in grabbing Wiktionary contents: {e}")
            print("You may be scraping too fast!")
        time.sleep(rc_sleep_seconds * 2)

    # Gets the HTML source.
    num_attempts = 0
    successful = False
    while num_attempts < MAX_CONNECT_ATTEMPTS:
        try:
            url = f"https://en.wiktionary.org/wiki/{term}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                if verbose:
                    print(
                        f"Error {response.status_code}: "
                        f"Could not fetch page for {term}"
                    )
                if depth < MAX_DEPTH:
                    # The word could be a conjugated form of a verb
                    # so the program tries to search the dict form of it.
                    dict_form = get_dictionary_form(term)
                    if dict_form is not None:
                        return scrape(
                            dict_form,
                            depth + 1,
                            dict_form,
                            rc_sleep_seconds=rc_sleep_seconds,
                            verbose=verbose,
                        )
                return None  # unsuccessful.
            successful = True
            break

        except requests.exceptions.ConnectionError as e:
            show_http_error_message(e)
            num_attempts += 1  # reattempts a few times before giving up.
        except requests.exceptions.RequestException as e:
            show_http_error_message(e)
            num_attempts += 1  # reattempts a few times before giving up.
        except requests.exceptions.HTTPError as e:
            show_http_error_message(e)
            num_attempts += 1  # reattempts a few times before giving up.

    if not successful:
        return None

    # Shortens HTML to give BeautifulSoup less to parse.
    clean_text = shorten_html(response.text)
    clean_text = remove_further_pronunciations(clean_text)

    # Finds the header tag with "Japanese"; returns if no header was found.
    soup = BeautifulSoup(clean_text, "html.parser")
    japanese_header = None
    headers = []
    for header_tag in HEADER_TAGS:
        next_header = soup.find(header_tag, id="Japanese")
        if next_header is not None:
            japanese_header = next_header
            break

    if japanese_header is None:
        if verbose:
            print("Error: No Japanese header was found" + "on that Wiktionary page.")
        return None

    """
    Step 2) Recursion will be performed on pages linked to by Wiktionary
            as being alternative spellings if a definition isn't found.
    """
    results = []
    word_info, redirects_to_etym, embedded_kanji_redirects = scrape_word_info(
        term,
        japanese_header,
        depth < MAX_DEPTH,
        find_embedded_kanji=depth == 0,
    )  # gets list of info.

    # If this is a Wiktionary page full of kanji spellings,
    # then a list of recursive results is returned to the user.
    if embedded_kanji_redirects and len(embedded_kanji_redirects) > 0:
        comp = []
        for embed in embedded_kanji_redirects:
            info = scrape(
                embed,
                depth=depth + 1,
                original_term=term,
                rc_sleep_seconds=rc_sleep_seconds,
                force_sleep=True,
                verbose=verbose,
            )
            if info is not None:
                comp.append(info[0])

        if len(comp) > 0:
            comp = remove_alternative_spellings(comp)
        comp = remove_empty_entries(comp, remove_entries=True)
        return comp

    # Otherwise, results are added as normal.
    if word_info is not None and len(word_info.keys()) > 0:
        results.append(word_info)
    else:
        sorted_values = sorted(
            [v for v in redirects_to_etym.values()],
            key=lambda v: int(v[10:]),
        )
        results.append({v: None for v in sorted_values})

    if depth < MAX_DEPTH:
        # The program
        # checks to see if there are any alternatives that
        # Wiktionary is redirecting the user to.
        JP_TABLE = "wikitable ja-see"
        next_tables = japanese_header.find_all_next("table", class_=JP_TABLE)
        for table in next_tables:
            alternatives = get_alternative_terms_from_table(table)
            if len(alternatives) > 0:
                # A recursive call with depth added is made.
                for alternative in alternatives:
                    alt_results = scrape(
                        alternative,
                        depth + 1,
                        term,
                        rc_sleep_seconds=rc_sleep_seconds,
                        verbose=verbose,
                    )

                    if alt_results is not None:
                        results.extend(alt_results)

    if (results is None or len(results) == 0) and depth < MAX_DEPTH:
        # If there were no results found after looking for alternatives,
        # then the program will try to look for a dictionary form
        # of the word (the program assuming it could be a verb).
        dict_form = get_dictionary_form(term)
        if dict_form is not None:
            return scrape(
                dict_form,
                depth + 1,
                original_term,
                rc_sleep_seconds=rc_sleep_seconds,
                verbose=verbose,
            )

    """
    Step 3) Embeds the relevant word information from any
            pages that were redirected to.
    """
    # results = remove_empty_entries(results)  # probably unneeded
    if depth == 0:
        results = embed_redirects(
            results,
            redirects_to_etym,
            term,
        )

        if len(results) > 0:
            results = remove_alternative_spellings(results)
        results = remove_empty_entries(results, remove_entries=True)

    """
    Step 4) Goes through each entry 
            and removes any Etymology entry that lacks any Definitions.
    """
    for i in range(len(results)):
        keys_to_keep = []
        for etym_name, parts in results[i].items():
            if etym_name == "alternative-spellings" or parts is not None:
                keys_to_keep.append(etym_name)
        if len(keys_to_keep) > 0:
            results[i] = {
                key: value for key, value in results[i].items() if key in keys_to_keep
            }

    if depth > 0:
        return results

    results = remove_alternative_spellings(results)

    """
    Step 5) Shares pronunciation information with those of matching kana
            that lack pitch-accent or IPA (depth is at 0)
    """
    results = exchange_phonetic_info(results)
    results = fill_in_missing_furigana(results)

    return results
