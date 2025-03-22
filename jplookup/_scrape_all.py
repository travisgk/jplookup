"""
Filename: jplookup._scrape_all.py
Author: TravisGK
Date: 2025-03-22

Description: This file defines a function to let the user
             easily scrape a list of Japanese terms.

Version: 1.0.1
License: MIT
"""

import json
import random
import sys
import time
from jplookup._scrape.scrape import scrape
import jplookup.anki


def scrape_all(
    out_path="jp-data.json",
    in_path="n5.txt",
    words=None,
    sleep_seconds=0.1,
    error_sleep_seconds=20,
    verbose: bool = True,
):
    """
    Takes either an <in_path> specifying a .txt file to load terms from,
    or takes a list of <words> directly, then saves the scraped
    results as a single dictionary to the <out_path> JSON.
    """
    PATIENCE = sleep_seconds

    # Grabs all unique Japanese terms.
    terms = []
    if words is not None:
        for word in words:
            if word not in terms:
                terms.append(word)
    else:
        with open(in_path, "r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if clean_line not in terms:
                    terms.append(clean_line)

    start_time = time.time()

    # Collects data into one dictionary.
    # Any terms that throw errors will be saved to their own text files.
    data = {}
    unfound = []
    exceptionals = []
    for i, term in enumerate(terms):
        try:
            if i > 0:
                if i % 20 == 0:
                    # Sleeps for a little while every 20 terms.
                    sleep_length = random.uniform(
                        error_sleep_seconds * 0.75,
                        error_sleep_seconds * 1.25,
                    )
                else:
                    sleep_length = random.uniform(
                        PATIENCE * 0.75,
                        PATIENCE * 1.5,
                    )
                time.sleep(sleep_length)

            # Scrapes.
            word_info = scrape(
                term,
                re_sleep_seconds=sleep_seconds,
                error_sleep_seconds=error_sleep_seconds,
            )
            if word_info and len(word_info) > 0:
                # Prints how much time is remaining to scrape all the words.
                percent_done = int((i + 1) / len(terms) * 100)
                elapsed = time.time() - start_time
                elapsed_per_entry = elapsed / (i + 1)  # avg
                num_remaining = len(terms) - (i + 1)
                remaining_time = int(num_remaining * elapsed_per_entry)
                hours = remaining_time // 3600
                remaining_time %= 3600
                minutes = remaining_time // 60
                remaining_time %= 60
                seconds = remaining_time

                if verbose:
                    print("\n" * 6)
                    print(json.dumps(word_info[0], indent=4, ensure_ascii=False))
                    print(
                        f"{percent_done:> 2d}% [{hours}:{minutes:02}:{seconds:02}] {term}"
                    )

                # Adds the entry to the dictionary.
                data[term] = word_info

            else:
                if verbose:
                    print(f"No data saved for {term}!")
                unfound.append(term)

        except KeyboardInterrupt as e:
            if verbose:
                print("Keyboard interrupt received, exiting gracefully.")
            sys.exit(0)

        except Exception as e:
            if verbose:
                print(
                    "################################\n"
                    + f"EXCEPTION {e} from term {term}\n"
                    + "################################\n"
                )
            exceptionals.append(term)

    # End of run. Saves everything that went wrong (if anything).
    if verbose and len(exceptionals) > 0:
        print("These terms threw exceptions:")
        for x in exceptionals:
            print(f"\t{x}")
        print("\n", end="")

    if verbose and len(unfound) > 0:
        print("These terms could not be found:")
        for u in unfound:
            print(f"\t{u}")
        print("\n", end="")

    # Save the dictionary to a file.
    if out_path is not None:
        with open(out_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    return data