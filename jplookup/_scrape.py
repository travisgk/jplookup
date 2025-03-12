"""
Filename: jplookup._scrape.py
Author: TravisGK
Date: 2025-03-10

Description: This file defines the primary function that scrapes
             information about a Japanese term from its English Wiktionary
             page and returns it in an easy-to-read format for the user.

             The idea is to give back the information on the main Wiktionary
             page while also incorporating the relevant Etymologies referred
             to on separate Wiktionary pages.

Version: 1.0
License: MIT
"""

import time
import requests
from bs4 import BeautifulSoup
from ._cleanstr._textwork import (
    remove_further_pronunciations,
    shorten_html,
)
from ._cleanstr._dictform import get_dictionary_form
from ._processing._remove_empty import remove_empty_entries
from ._processing._tools._redirects import (
    remove_alternative_spellings,
    link_up_redirects,
)
from ._scrape_entry import *


def scrape(
    term: str,
    depth: int = 0,
    original_term=None,
    rc_sleep_seconds=5,
    force_sleep: bool = False,
    verbose: bool = True,
):
    """Returns either a list or None."""
    MAX_CONNECT_ATTEMPTS = 3
    MAX_DEPTH = 1  # not inclusive.

    if depth > 0 or force_sleep:
        # sleeps when doing a recursive loop to prevent getting blocked.
        time.sleep(rc_sleep_seconds)

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
                    dict_form = get_dictionary_form(term)
                if dict_form is not None:
                    return scrape(
                        dict_form,
                        depth + 1,
                        original_term,
                        rc_sleep_seconds=rc_sleep_seconds,
                    )
                return None
            successful = True
            break
        except requests.exceptions.HTTPError as e:
            if verbose:
                print(f"HTTPError in grabbing Wiktionary contents: {e}")
                print("You may be scraping too fast!")
            time.sleep(rc_sleep_seconds)
            num_attempts += 1

    if not successful:
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
        if verbose:
            print("Error: No Japanese header was found" "on that Wiktionary page.")
        return None

    # Scrapes.
    # ---
    # Recursion will be performed on pages linked to by Wiktionary
    # as being alternative spellings if a definition isn't found.
    results = []
    word_info, redirects_to_etym = scrape_word_info(
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

    if depth < MAX_DEPTH:
        # the program
        # checks to see if there are any alternatives that
        # Wiktionary is redirecting the user to.
        JP_TABLE = "wikitable ja-see"
        next_tables = japanese_header.find_all_next("table", class_=JP_TABLE)
        for table in next_tables:
            alternative = get_alternative_term_from_table(table)
            if alternative is not None:
                if (results is None or len(results) == 0) and len(next_tables) == 1:
                    # a simple redirect.
                    return scrape(
                        alternative,
                        0,
                        alternative,
                        rc_sleep_seconds=rc_sleep_seconds,
                        force_sleep=True,
                    )

                alt_results = scrape(
                    alternative,
                    depth + 1,
                    original_term,
                    rc_sleep_seconds=rc_sleep_seconds,
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
                dict_form,
                depth + 1,
                original_term,
                rc_sleep_seconds=rc_sleep_seconds,
            )

    # the additional call may be unnecessary...
    results = remove_empty_entries(results)
    if depth == 0:
        results = link_up_redirects(
            results,
            redirects_to_etym,
            original_term if original_term else term,
        )

        if len(results) > 0:
            results = remove_alternative_spellings(results)
        results = remove_empty_entries(results, remove_entries=True)

    indices_to_remove = []
    for i in range(len(results)):
        for etym_name, parts in results[i].items():
            if parts is None:
                indices_to_remove.append(i)
    if len(indices_to_remove) > 0:
        results = [r for i, r in enumerate(results) if i not in indices_to_remove]

    return results
