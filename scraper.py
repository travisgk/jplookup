import time
import random
import requests
import sys
import json
import jplookup


def main():

    MODE = "all"
    USE_PROMPT = False

    AGGRESSIVENESS = 8

    if MODE == "testing":
        for i, term in enumerate(
            [
                "コココココココ",
                "あなた",
                "いくつ",
                "かぎ",
                "それでは",
                "あさって",
                "たて",
                "ほか",
                "ふろ",
                "なぜ",
                "ください",
                "せっけん",
            ]
        ):
            time.sleep(AGGRESSIVENESS)
            word_info = jplookup.scrape(term, rc_sleep_seconds=5)
            if word_info and len(word_info) > 0:
                with open(f"out-data-{i}.json", "w", encoding="utf-8") as json_file:
                    json.dump(word_info[0], json_file, indent=4, ensure_ascii=False)
                print(
                    json.dumps(
                        word_info[0],
                        indent=4,
                        ensure_ascii=False,
                    ),
                    end="\n\n\n\n\n\n\n\n\n\n",
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
                    percent_done = int(i / len(terms) * 100)
                    print(f"\n\n{percent_done:> 2d}% {term}:")
                    data[term] = word_info

                    print(json.dumps(word_info[0], indent=4, ensure_ascii=False))

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
