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
    AGGRESSIVENESS = 8

    if MODE == "testing":
        for i, term in enumerate(
            [
                # "中",
                # "白",
                # "はく",
                "捕る",
                "取る",
                "いかが",
                "北",
                "ふろ",
                "よくそう",
                "浴槽",
                # "犬",
                # "猫",
                # "短い",
                # "コート",
                # "ボタン",
            ]
        ):
            if i > 0:
                time.sleep(AGGRESSIVENESS)
            word_info = jplookup.scrape(term, rc_sleep_seconds=8)
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
                    print(anki_card["definitions"])
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
            for info in word_info:
                print(info)

    elif MODE == "all":
        terms = []
        with open("n5.txt", "r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if clean_line not in terms:
                    terms.append(clean_line)

        start_time = time.time()

        data = {}

        unfound = []
        exceptionals = []
        for i, term in enumerate(terms):
            try:
                sleep_length = random.uniform(
                    AGGRESSIVENESS * 0.75, AGGRESSIVENESS * 1.5
                )
                time.sleep(sleep_length)
                word_info = jplookup.scrape(term, rc_sleep_seconds=8)

                if word_info and len(word_info) > 0:
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
                    data[term] = word_info

                else:
                    unfound.append(term)

            except KeyboardInterrupt as e:
                print("Keyboard interrupt received, exiting gracefully.")
                sys.exit(0)

            except Exception as e:
                print(
                    f"################################\nEXCEPTION {e} from term {term}\n################################\n"
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
