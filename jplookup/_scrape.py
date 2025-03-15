"""
Filename: jplookup._scrape.py
Author: TravisGK
Date: 2025-03-13

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
import jaconv
from ._cleanstr._textwork import (
    kata_matches,
    remove_further_pronunciations,
    shorten_html,
)
from ._cleanstr._dictform import get_dictionary_form
from ._processing._remove_empty import remove_empty_entries
from ._processing._tools._redirects import (
    remove_alternative_spellings,
    embed_redirects,
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
                            original_term,
                            rc_sleep_seconds=rc_sleep_seconds,
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
            print("Error: No Japanese header was found" "on that Wiktionary page.")
        return None

    """
    Step 2) Recursion will be performed on pages linked to by Wiktionary
            as being alternative spellings if a definition isn't found.
    """
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
        # The program
        # checks to see if there are any alternatives that
        # Wiktionary is redirecting the user to.
        JP_TABLE = "wikitable ja-see"
        next_tables = japanese_header.find_all_next("table", class_=JP_TABLE)
        for table in next_tables:
            alternative = get_alternative_term_from_table(table)
            if alternative is not None:
                if len(next_tables) == 1 and (results is None or len(results) == 0):
                    # This is a simple redirect; no depth added.
                    return scrape(
                        alternative,
                        0,
                        alternative,
                        rc_sleep_seconds=rc_sleep_seconds,
                        force_sleep=True,
                    )

                # Otherwise a recursive call with depth added is made.
                alt_results = scrape(
                    alternative,
                    depth + 1,
                    original_term,
                    rc_sleep_seconds=rc_sleep_seconds,
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
            )

    """
    Step 3) Embeds the relevant word information from any
            pages that were redirected to.
    """
    results = remove_empty_entries(results)  # possibly unneeded
    if depth == 0:
        results = embed_redirects(
            results,
            redirects_to_etym,
            original_term if original_term else term,
        )

        if len(results) > 0:
            results = remove_alternative_spellings(results)
        results = remove_empty_entries(results, remove_entries=True)

    """
    Step 4) Removes any Etymology entry that lacks any Definitions.
    """
    indices_to_remove = []
    for i in range(len(results)):
        for etym_name, parts in results[i].items():
            if parts is None:
                indices_to_remove.append(i)
    if len(indices_to_remove) > 0:
        results = [r for i, r in enumerate(results) if i not in indices_to_remove]

    if depth > 0:
        return results
    """
    Step 5) Shares pronunciation information with those of matching kana
            that lack pitch-accent or IPA.
    """
    # Gets all the pronunciation dict objects and kata conversions.
    all_pronunciations = []
    all_kata = []
    all_refs = []
    for i in range(len(results)):
        for etym_name, parts in results[i].items():
            for part_of_speech, part_data in parts.items():
                pronunciations = part_data.get("pronunciations")
                if pronunciations is not None:  # TODO: pretty sure this is unneeded.
                    for j, p in enumerate(pronunciations):
                        if p.get("kana"):
                            all_pronunciations.append(p)
                            all_kata.append(jaconv.hira2kata(p["kana"]))
                            all_refs.append((i, etym_name, part_of_speech, j))

    if len(all_pronunciations) <= 1:
        return results

    # Shares information among one another.
    KEYS = ["kana", "furigana", "region", "pitch-accent", "ipa"]
    needs_updates = [True for _ in all_pronunciations]
    changed_indices = []
    for index, receiver_p in enumerate(all_pronunciations[::-1]):
        i = len(all_pronunciations) - index - 1
        if not needs_updates[i]:
            continue

        for j, giver_p in enumerate(all_pronunciations):
            if i == j or receiver_p.get("pitch-accent") not in [
                None,
                giver_p.get("pitch-accent"),
            ]:
                continue

            if kata_matches(all_kata[i], all_kata[j]):
                has_everything = True
                was_changed = False
                for key in KEYS[2:]:
                    if giver_p.get(key):
                        if receiver_p.get(key) is None:
                            receiver_p[key] = giver_p[key]
                            was_changed = True
                    else:
                        has_everything = False
                if has_everything:
                    needs_updates[j] = False
                if was_changed:
                    changed_indices.append(i)

    # Reorders dictionary key order to be consistent.
    for i in changed_indices:
        entry_i, etym, part, p_i = all_refs[i]
        p = results[entry_i][etym][part]["pronunciations"][p_i]
        results[entry_i][etym][part]["pronunciations"][p_i] = {
            key: p[key] for key in KEYS if p.get(key) is not None
        }

    return results
