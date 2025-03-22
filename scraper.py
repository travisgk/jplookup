import time
import random
import requests
import sys
import json
import jplookup
import jplookup.anki


def main():
    VERBOSE = True
    MODE = "all"
    PATIENCE = 0.1

    if MODE == "testing":
        WORDS = [
            "人",
        ]

        # Scrapes every testing term.
        for i, term in enumerate(WORDS):
            if i > 0:
                time.sleep(PATIENCE)
            word_info = jplookup.scrape(term, re_sleep_seconds=PATIENCE)
            if word_info and len(word_info) > 0:
                with open(f"out-data-{i}.json", "w", encoding="utf-8") as json_file:
                    json.dump(word_info, json_file, indent=4, ensure_ascii=False)
                print(
                    json.dumps(
                        word_info,
                        indent=4,
                        ensure_ascii=False,
                    )
                )
                anki_card = jplookup.anki.dict_to_anki_fields(
                    word_info, include_romanji=True
                )
                if anki_card:
                    print(
                        json.dumps(
                            anki_card,
                            indent=4,
                            ensure_ascii=False,
                        )
                    )
                print(
                    "\n\n\n\n\n\n\n\n\n\n",
                )
            else:
                print(
                    f"No relevant info found for {term}. Skipping...",
                    end="\n\n\n\n\n\n\n\n\n\n",
                )

    elif MODE == "prompt":
        word = None
        while True:
            print("Enter a word: ", end="")
            word = input()
            if len(word) == 0:
                print("Please enter a word.")
                continue

            if word.lower() == "exit":
                break

            word_info = jplookup.scrape(word)
            if word_info:
                print(
                    json.dumps(
                        word_info[0],
                        indent=4,
                        ensure_ascii=False,
                    )
                )

    elif MODE == "all":
        # Grabs all unique Japanese terms.
        terms = []
        with open("n5.txt", "r", encoding="utf-8") as file:
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
                        sleep_length = random.uniform(6.0, 13.0)
                    else:
                        sleep_length = random.uniform(
                            PATIENCE * 0.75,
                            PATIENCE * 1.5,
                        )
                    time.sleep(sleep_length)

                # Scrapes.
                word_info = jplookup.scrape(
                    term,
                    re_sleep_seconds=0.1,
                    error_sleep_seconds=20,
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

                    if VERBOSE:
                        print("\n" * 6)
                        print(json.dumps(word_info[0], indent=4, ensure_ascii=False))
                        print(
                            f"{percent_done:> 2d}% [{hours}:{minutes:02}:{seconds:02}] {term}"
                        )

                    # Adds the entry to the dictionary.
                    data[term] = word_info

                else:
                    print(f"No data saved for {term}!")
                    unfound.append(term)

            except KeyboardInterrupt as e:
                print("Keyboard interrupt received, exiting gracefully.")
                sys.exit(0)

            except Exception as e:
                print(
                    "################################\n"
                    + f"EXCEPTION {e} from term {term}\n"
                    + "################################\n"
                )
                exceptionals.append(term)

        # End of run. Saves everything that went wrong (if anything).
        with open("exceptionals.txt", "w", encoding="utf-8") as out_file:
            for x in exceptionals:
                out_file.write(x + "\n")

        with open("unfound.txt", "w", encoding="utf-8") as out_file:
            for u in unfound:
                out_file.write(u + "\n")

        # Save the dictionary to a file.
        with open("jp-data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
